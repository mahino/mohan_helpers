#!/usr/bin/env bash
set -euo pipefail

# Collect microservice logs from NCM pods by:
# 1) dynamically resolving pod names by prefix
# 2) reading supervisorctl status inside the container
# 3) copying matching *.log* files from service log directories
#
# Default services:
#   epsilon   -> ns ntnx-ncm-common,       pod prefix ncm-epsilon,   log dir /home/epsilon/log
#   calm      -> ns ntnx-ncm-self-service, pod prefix ncm-calm,      log dir /home/calm/log
#   policy    -> ns ntnx-ncm-self-service, pod prefix ncm-policy,    log dir /home/policy/log
#   scheduler -> ns ntnx-ncm-self-service, pod prefix ncm-scheduler, log dir /home/epsilon/log
#
# Examples:
#   ./collect_microservice_logs.sh
#   ./collect_microservice_logs.sh -k nc_kubecconfig -s epsilon,policy
#   ./collect_microservice_logs.sh -s epsilon -t indra_0.log,arjun_0.log

KUBECONFIG_PATH="../kube/ss_kube"
OUT_BASE="microservice-logs"
SELECTED_SERVICES="epsilon,calm,policy,scheduler"
TAIL_LINES=0
EXPLICIT_TARGETS=""
KUBECTL_REQUEST_TIMEOUT="20s"
KUBECTL_RETRIES=3
KUBECTL_RETRY_SLEEP_SEC=3

usage() {
  cat <<'EOF'
Usage: collect_microservice_logs.sh [options]

Options:
  -k <kubeconfig>     Kubeconfig path (default: ../kube/ss_kube)
  -o <output_base>    Output base dir prefix (default: microservice-logs)
  -s <services>       Comma-separated services (default: epsilon,calm,policy,scheduler)
  -t <targets>        Comma-separated explicit log file names (e.g. indra_0.log,arjun_0.log)
  -n <tail_lines>     Also collect tail logs using kubectl logs --tail (0 = skip, default: 0)
  -r <retries>        kubectl retries on transient failure (default: 3)
  -w <timeout>        kubectl request timeout (default: 20s)
  -h                  Show help
EOF
}

while getopts ":k:o:s:t:n:r:w:h" opt; do
  case "${opt}" in
    k) KUBECONFIG_PATH="${OPTARG}" ;;
    o) OUT_BASE="${OPTARG}" ;;
    s) SELECTED_SERVICES="${OPTARG}" ;;
    t) EXPLICIT_TARGETS="${OPTARG}" ;;
    n) TAIL_LINES="${OPTARG}" ;;
    r) KUBECTL_RETRIES="${OPTARG}" ;;
    w) KUBECTL_REQUEST_TIMEOUT="${OPTARG}" ;;
    h)
      usage
      exit 0
      ;;
    \?)
      echo "Invalid option: -${OPTARG}" >&2
      usage
      exit 2
      ;;
  esac
done

if ! command -v kubectl >/dev/null 2>&1; then
  echo "[ERROR] kubectl not found in PATH" >&2
  exit 1
fi

if ! [[ "${TAIL_LINES}" =~ ^[0-9]+$ ]]; then
  echo "[ERROR] -n tail lines must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "${KUBECTL_RETRIES}" =~ ^[0-9]+$ ]]; then
  echo "[ERROR] -r retries must be a non-negative integer" >&2
  exit 1
fi

ts="$(date +%Y%m%d_%H%M%S)"
out_dir="${OUT_BASE}_${ts}"
mkdir -p "${out_dir}"

declare -A NS_BY_SERVICE=(
  ["epsilon"]="ntnx-ncm-common"
  ["calm"]="ntnx-ncm-self-service"
  ["policy"]="ntnx-ncm-self-service"
  ["scheduler"]="ntnx-ncm-self-service"
)
declare -A POD_PREFIX_BY_SERVICE=(
  ["epsilon"]="ncm-epsilon"
  ["calm"]="ncm-calm"
  ["policy"]="ncm-policy"
  ["scheduler"]="ncm-scheduler"
)
declare -A LOG_DIR_BY_SERVICE=(
  ["epsilon"]="/home/epsilon/log"
  ["calm"]="/home/calm/log"
  ["policy"]="/home/policy/log"
  ["scheduler"]="/home/epsilon/log"
)
declare -A SUPERVISOR_CONF_BY_SERVICE=(
  ["epsilon"]="/home/epsilon/conf/supervisor/supervisord.conf"
  ["calm"]="/home/calm/conf/supervisor/supervisord.conf"
  ["policy"]="/home/policy/conf/supervisor/supervisord.conf"
  ["scheduler"]="/home/epsilon/conf/supervisor/supervisord.conf"
)
declare -A ACTIVATE_BY_SERVICE=(
  ["epsilon"]="/home/epsilon/venv/bin/activate"
  ["calm"]="/home/calm/venv/bin/activate"
  ["policy"]="/home/policy/venv/bin/activate"
  ["scheduler"]="/home/epsilon/venv/bin/activate"
)

IFS=',' read -r -a services <<< "${SELECTED_SERVICES}"
IFS=',' read -r -a explicit_targets <<< "${EXPLICIT_TARGETS}"

echo "[INFO] Output directory: ${out_dir}"
echo "[INFO] Using kubeconfig: ${KUBECONFIG_PATH}"
echo "[INFO] kubectl timeout/retries: ${KUBECTL_REQUEST_TIMEOUT} / ${KUBECTL_RETRIES}"
echo "[INFO] Services: ${SELECTED_SERVICES}"

run_kubectl_retry() {
  local attempt=1
  local rc=0
  while true; do
    if output="$("$@" 2>&1)"; then
      printf "%s" "${output}"
      return 0
    fi
    rc=$?
    if [[ "${attempt}" -ge "${KUBECTL_RETRIES}" ]]; then
      printf "%s" "${output}" >&2
      return "${rc}"
    fi
    echo "[WARN] kubectl attempt ${attempt}/${KUBECTL_RETRIES} failed; retrying in ${KUBECTL_RETRY_SLEEP_SEC}s..." >&2
    echo "[WARN] ${output}" >&2
    attempt=$((attempt + 1))
    sleep "${KUBECTL_RETRY_SLEEP_SEC}"
  done
}

resolve_pod() {
  local namespace="$1"
  local prefix="$2"
  run_kubectl_retry kubectl --kubeconfig="${KUBECONFIG_PATH}" --request-timeout="${KUBECTL_REQUEST_TIMEOUT}" get pods -n "${namespace}" \
    -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' \
    | awk -v p="^${prefix}" '$0 ~ p {print; exit}'
}

run_kexec() {
  local ns="$1"
  local pod="$2"
  local cmd="$3"
  run_kubectl_retry kubectl --kubeconfig="${KUBECONFIG_PATH}" --request-timeout="${KUBECTL_REQUEST_TIMEOUT}" exec -n "${ns}" "${pod}" -- bash -lc "${cmd}"
}

copy_from_pod() {
  local ns="$1"
  local pod="$2"
  local src="$3"
  local dst="$4"
  run_kubectl_retry kubectl --kubeconfig="${KUBECONFIG_PATH}" --request-timeout="${KUBECTL_REQUEST_TIMEOUT}" cp -n "${ns}" "${pod}:${src}" "${dst}" >/dev/null
}

echo "[INFO] Verifying API server reachability..."
if ! run_kubectl_retry kubectl --kubeconfig="${KUBECONFIG_PATH}" --request-timeout="${KUBECTL_REQUEST_TIMEOUT}" version --short >/dev/null; then
  echo "[ERROR] Kubernetes API not reachable. Check kubeconfig/context/network and retry."
  exit 1
fi

for raw_service in "${services[@]}"; do
  service="$(echo "${raw_service}" | xargs)"
  [[ -z "${service}" ]] && continue

  if [[ -z "${NS_BY_SERVICE[${service}]:-}" ]]; then
    echo "[WARN] Unknown service '${service}', skipping"
    continue
  fi

  ns="${NS_BY_SERVICE[${service}]}"
  prefix="${POD_PREFIX_BY_SERVICE[${service}]}"
  log_dir="${LOG_DIR_BY_SERVICE[${service}]}"
  supervisor_conf="${SUPERVISOR_CONF_BY_SERVICE[${service}]}"
  activate_path="${ACTIVATE_BY_SERVICE[${service}]}"

  echo "==================================================================="
  echo "[INFO] Service: ${service} (ns=${ns}, prefix=${prefix}, log_dir=${log_dir})"

  pod="$(resolve_pod "${ns}" "${prefix}" || true)"
  if [[ -z "${pod}" ]]; then
    echo "[ERROR] No running pod found for service '${service}' with prefix '${prefix}'"
    continue
  fi
  echo "[INFO] Resolved pod: ${pod}"

  service_out_dir="${out_dir}/${service}"
  mkdir -p "${service_out_dir}"

  # 1) Collect supervisor status snapshot
  status_file="${service_out_dir}/supervisor_status.txt"
  {
    echo "Service: ${service}"
    echo "Namespace: ${ns}"
    echo "Pod: ${pod}"
    echo "Collected at: $(date)"
    echo "------------------------------------------------------------"
    run_kexec "${ns}" "${pod}" "source '${activate_path}' >/dev/null 2>&1 || true; supervisorctl -c '${supervisor_conf}' status | head -n 200"
  } > "${status_file}" 2>&1 || true
  echo "[INFO] Wrote status: ${status_file}"

  # 2) Build candidate log basenames from supervisor program names
  candidate_names_file="${service_out_dir}/candidate_log_names.txt"
  awk '
    NF > 0 {
      name=$1
      sub(/^.*:/,"",name)
      sub(/_[0-9]+$/,"",name)
      if (name != "" && name != "RUNNING" && name != "STOPPED") {
        print name
      }
    }' "${status_file}" | sort -u > "${candidate_names_file}" || true

  # Append explicit targets
  for t in "${explicit_targets[@]}"; do
    tt="$(echo "${t}" | xargs)"
    [[ -z "${tt}" ]] && continue
    # Normalize "indra_0.log" -> "indra_0.log"
    echo "${tt}" >> "${candidate_names_file}"
  done
  sort -u -o "${candidate_names_file}" "${candidate_names_file}" || true

  # 3) List files in log dir and decide which *.log* to copy
  pod_listing_file="${service_out_dir}/pod_log_dir_listing.txt"
  run_kexec "${ns}" "${pod}" "ls -1 '${log_dir}' 2>/dev/null || true" > "${pod_listing_file}" || true

  mapfile -t all_log_files < <(awk '/\.log/ {print $0}' "${pod_listing_file}" | sort -u)
  if [[ "${#all_log_files[@]}" -eq 0 ]]; then
    echo "[WARN] No *.log* files found in ${log_dir} for ${service}"
  fi

  copied=0
  while IFS= read -r candidate; do
    [[ -z "${candidate}" ]] && continue
    # If explicit target looks like a full filename, match directly.
    if [[ "${candidate}" == *.log* ]]; then
      if grep -Fxq "${candidate}" "${pod_listing_file}"; then
        dst="${service_out_dir}/${candidate}"
        if copy_from_pod "${ns}" "${pod}" "${log_dir}/${candidate}" "${dst}"; then
          echo "[INFO] Copied explicit: ${candidate}"
          copied=$((copied + 1))
        fi
      fi
      continue
    fi

    # Otherwise match candidate base against any *.log* filename.
    while IFS= read -r lf; do
      [[ -z "${lf}" ]] && continue
      # Match "indra" -> "indra_0.log", "indra.log", "indra_0.log.1", etc.
      if [[ "${lf}" =~ ^${candidate}([._-].*)?\.log.*$ ]]; then
        dst="${service_out_dir}/${lf}"
        if [[ ! -e "${dst}" ]]; then
          if copy_from_pod "${ns}" "${pod}" "${log_dir}/${lf}" "${dst}"; then
            echo "[INFO] Copied: ${lf}"
            copied=$((copied + 1))
          fi
        fi
      fi
    done < <(printf "%s\n" "${all_log_files[@]}")
  done < "${candidate_names_file}"

  # 4) Optional tail capture from kubectl logs stream (container stdout/stderr)
  if [[ "${TAIL_LINES}" -gt 0 ]]; then
    tail_out="${service_out_dir}/pod_stdout_tail_${TAIL_LINES}.log"
    if kubectl --kubeconfig="${KUBECONFIG_PATH}" logs -n "${ns}" "${pod}" --tail="${TAIL_LINES}" > "${tail_out}" 2>/dev/null; then
      echo "[INFO] Saved kubectl logs tail: ${tail_out}"
    else
      echo "[WARN] Failed to read kubectl logs tail for ${service}"
      rm -f "${tail_out}" || true
    fi
  fi

  if [[ "${copied}" -eq 0 ]]; then
    echo "[WARN] No matching microservice log files copied for ${service}"
  else
    echo "[INFO] Copied ${copied} file(s) for ${service}"
  fi
done

echo "==================================================================="
echo "[INFO] Done. Collected artifacts are under: ${out_dir}"
du -sh "${out_dir}" 2>/dev/null || true

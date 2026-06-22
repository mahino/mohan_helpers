#!/usr/bin/env bash
set -euo pipefail

# Interactive Fluentd live log streamer:
# - Select one namespace or ALL
# - Discover running pods + containers
# - Resolve latest fluentd folder per pod/container
# - Tail matching .log* file(s) in background
# - Append locally to <pod>-<container>.log

KUBECONFIG_PATH="${HOME}/kube/ss_kube"
FLUENTD_NAMESPACE="ntnx-system"
FLUENTD_POD_PREFIX="fluentd-aggregator"
FLUENTD_BASE_DIR="/fluentd/data/logs"

declare -a TAIL_PIDS=()

usage() {
  cat <<'EOF'
Usage: collect_fluentd_live_logs.sh [-k <kubeconfig>]

Options:
  -k <path>   Kubeconfig path (default: ~/kube/ss_kube)
  -h          Show help
EOF
}

while getopts ":k:h" opt; do
  case "${opt}" in
    k) KUBECONFIG_PATH="${OPTARG}" ;;
    h)
      usage
      exit 0
      ;;
    \?)
      echo "Unknown option: -${OPTARG}" >&2
      usage
      exit 1
      ;;
    :)
      echo "Option -${OPTARG} requires an argument." >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "${KUBECONFIG_PATH}" ]]; then
  echo "ERROR: kubeconfig not found: ${KUBECONFIG_PATH}" >&2
  exit 1
fi

KUBECTL=(kubectl --kubeconfig="${KUBECONFIG_PATH}")

cleanup() {
  local code=$?
  trap - INT TERM EXIT
  if [[ ${#TAIL_PIDS[@]} -gt 0 ]]; then
    echo ""
    echo "Stopping ${#TAIL_PIDS[@]} background tail process(es)..."
    for pid in "${TAIL_PIDS[@]}"; do
      kill "${pid}" 2>/dev/null || true
    done
    wait 2>/dev/null || true
  fi
  exit "${code}"
}

trap cleanup INT TERM EXIT

echo "Checking cluster access..."
"${KUBECTL[@]}" version >/dev/null 2>&1 || {
  echo "ERROR: cluster access failed with kubeconfig: ${KUBECONFIG_PATH}" >&2
  exit 1
}

FLUENTD_POD="$("${KUBECTL[@]}" get pods -n "${FLUENTD_NAMESPACE}" \
  --field-selector=status.phase=Running \
  -o jsonpath="{range .items[*]}{.metadata.name}{'\n'}{end}" | rg "^${FLUENTD_POD_PREFIX}" -m 1 || true)"

if [[ -z "${FLUENTD_POD}" ]]; then
  echo "ERROR: no running fluentd pod found in namespace ${FLUENTD_NAMESPACE} (prefix ${FLUENTD_POD_PREFIX})" >&2
  exit 1
fi

echo "Using Fluentd pod: ${FLUENTD_NAMESPACE}/${FLUENTD_POD}"

mapfile -t ALL_NAMESPACES < <("${KUBECTL[@]}" get namespaces -o jsonpath="{range .items[*]}{.metadata.name}{'\n'}{end}" | sort)
if [[ ${#ALL_NAMESPACES[@]} -eq 0 ]]; then
  echo "ERROR: no namespaces found." >&2
  exit 1
fi

echo ""
echo "Select namespace to stream:"
echo "  0) ALL"
for i in "${!ALL_NAMESPACES[@]}"; do
  printf "  %d) %s\n" "$((i + 1))" "${ALL_NAMESPACES[$i]}"
done

read -r -p "Enter selection number: " NS_SELECTION
if ! [[ "${NS_SELECTION}" =~ ^[0-9]+$ ]]; then
  echo "ERROR: invalid selection '${NS_SELECTION}'" >&2
  exit 1
fi

declare -a TARGET_NAMESPACES=()
if [[ "${NS_SELECTION}" -eq 0 ]]; then
  TARGET_NAMESPACES=("${ALL_NAMESPACES[@]}")
else
  idx=$((NS_SELECTION - 1))
  if (( idx < 0 || idx >= ${#ALL_NAMESPACES[@]} )); then
    echo "ERROR: selection out of range" >&2
    exit 1
  fi
  TARGET_NAMESPACES=("${ALL_NAMESPACES[$idx]}")
fi

echo ""
echo "Target namespace(s): ${TARGET_NAMESPACES[*]}"
echo ""

start_tail_for_pair() {
  local ns="$1"
  local pod="$2"
  local container="$3"

  local pattern="${FLUENTD_BASE_DIR}/kube.${ns}.${pod}.*.${container}.*"
  local latest_dir
  latest_dir="$("${KUBECTL[@]}" exec -n "${FLUENTD_NAMESPACE}" "${FLUENTD_POD}" -- bash -lc "ls -dt ${pattern} 2>/dev/null | head -n 1" | tr -d '\r')"

  if [[ -z "${latest_dir}" ]]; then
    echo "WARN: no fluentd folder found for ${ns}/${pod}/${container} (pattern: ${pattern})"
    return 0
  fi

  echo "LATEST FOLDER -> ${ns}/${pod}/${container}: ${latest_dir}"

  local latest_log
  latest_log="$("${KUBECTL[@]}" exec -n "${FLUENTD_NAMESPACE}" "${FLUENTD_POD}" -- bash -lc "ls -1t \"${latest_dir}\"/*.log* 2>/dev/null | head -n 1" | tr -d '\r')"

  if [[ -z "${latest_log}" ]]; then
    echo "WARN: no .log* file found under ${latest_dir} for ${ns}/${pod}/${container}"
    return 0
  fi

  local out_file="${pod}-${container}.log"
  echo "TAIL START -> ${latest_log} >> ${out_file}"

  (
    "${KUBECTL[@]}" exec -n "${FLUENTD_NAMESPACE}" "${FLUENTD_POD}" -- \
      bash -lc "tail -n 0 -F \"${latest_log}\""
  ) >> "${out_file}" 2>&1 &

  TAIL_PIDS+=("$!")
}

for ns in "${TARGET_NAMESPACES[@]}"; do
  echo "Discovering running pods in namespace: ${ns}"
  mapfile -t POD_CONTAINER_LINES < <(
    "${KUBECTL[@]}" get pods -n "${ns}" --field-selector=status.phase=Running \
      -o jsonpath="{range .items[*]}{.metadata.name}{'|'}{range .spec.containers[*]}{.name}{','}{end}{'\n'}{end}"
  )

  if [[ ${#POD_CONTAINER_LINES[@]} -eq 0 ]]; then
    echo "INFO: no running pods in ${ns}"
    continue
  fi

  for line in "${POD_CONTAINER_LINES[@]}"; do
    [[ -z "${line}" ]] && continue
    pod="${line%%|*}"
    containers_csv="${line#*|}"
    IFS=',' read -r -a containers <<< "${containers_csv}"
    for container in "${containers[@]}"; do
      [[ -z "${container}" ]] && continue
      start_tail_for_pair "${ns}" "${pod}" "${container}"
    done
  done
done

if [[ ${#TAIL_PIDS[@]} -eq 0 ]]; then
  echo "No eligible fluentd log streams were started."
  exit 0
fi

echo ""
echo "Started ${#TAIL_PIDS[@]} live tail process(es)."
echo "Logs are appending to local files named: <pod>-<container>.log"
echo "Press Ctrl+C to stop all tails cleanly."

wait

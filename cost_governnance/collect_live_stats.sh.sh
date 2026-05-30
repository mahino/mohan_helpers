#!/bin/bash

NAMESPACE="ncm-cg"
LOG_FILE="pod_usage.log"
INTERVAL=60          # collect every 60 seconds
DURATION=1800        # 30 minutes (1800 seconds)

START_TIME=$(date +%s)

echo "Starting pod resource collection for namespace: $NAMESPACE"
echo "Press Ctrl+C to stop early."
echo

# Convert CPU to millicores
cpu_to_millicores() {
  local val="$1"
  if [[ "$val" =~ ^([0-9]+)m$ ]]; then
    echo "${BASH_REMATCH[1]}"
  elif [[ "$val" =~ ^([0-9]+)$ ]]; then
    echo $(( ${BASH_REMATCH[1]} * 1000 ))
  elif [[ "$val" =~ ^([0-9]+\.[0-9]+)$ ]]; then
    echo $(awk "BEGIN {printf \"%.0f\", ${BASH_REMATCH[1]} * 1000}")
  else
    echo ""
  fi
}

# Convert memory to Mi
mem_to_mi() {
  local val="$1"
  if [[ "$val" =~ ^([0-9]+)Mi$ ]]; then
    echo "${BASH_REMATCH[1]}"
  elif [[ "$val" =~ ^([0-9]+)Gi$ ]]; then
    echo $(( ${BASH_REMATCH[1]} * 1024 ))
  elif [[ "$val" =~ ^([0-9]+)Ki$ ]]; then
    echo $(( ${BASH_REMATCH[1]} / 1024 ))
  elif [[ "$val" =~ ^([0-9]+)$ ]]; then
    echo $(( ${BASH_REMATCH[1]} / 1048576 ))
  else
    echo ""
  fi
}

while true; do
  CURRENT_TIME=$(date +%s)
  ELAPSED=$(( CURRENT_TIME - START_TIME ))

  if [ "$ELAPSED" -ge "$DURATION" ]; then
    echo "Reached 30 minutes. Stopping collection."
    break
  fi

  {
    echo "============================================================================================================"
    echo "Timestamp : $(date)"
    echo "Namespace : $NAMESPACE"
    echo "------------------------------------------------------------------------------------------------------------"
    printf "%-40s %-10s %-12s %-15s %-15s %-10s %-10s\n" \
      "POD_NAME" "CPU(m)" "MEMORY(Mi)" "CPU_LIMIT" "MEM_LIMIT" "CPU%" "MEM%"
    echo "------------------------------------------------------------------------------------------------------------"

    kubectl top pod -n "$NAMESPACE" --no-headers 2>/dev/null | \
    while read -r pod cpu mem; do

      # Get limits (sum of all containers)
      CPU_LIMIT=$(kubectl get pod "$pod" -n "$NAMESPACE" \
        -o jsonpath='{range .spec.containers[*]}{.resources.limits.cpu}{" "}{end}' 2>/dev/null)

      MEM_LIMIT=$(kubectl get pod "$pod" -n "$NAMESPACE" \
        -o jsonpath='{range .spec.containers[*]}{.resources.limits.memory}{" "}{end}' 2>/dev/null)

      # Calculate CPU percentage
      cpu_used=$(cpu_to_millicores "$cpu")
      cpu_limit_total=0
      for c in $CPU_LIMIT; do
        c_val=$(cpu_to_millicores "$c")
        if [ -n "$c_val" ]; then
          cpu_limit_total=$(( cpu_limit_total + c_val ))
        fi
      done
      if [ -n "$cpu_used" ] && [ "$cpu_limit_total" -gt 0 ]; then
        cpu_pct=$(awk "BEGIN {printf \"%.1f\", ($cpu_used / $cpu_limit_total) * 100}")
      else
        cpu_pct="N/A"
      fi

      # Calculate memory percentage
      mem_used=$(mem_to_mi "$mem")
      mem_limit_total=0
      for m in $MEM_LIMIT; do
        m_val=$(mem_to_mi "$m")
        if [ -n "$m_val" ]; then
          mem_limit_total=$(( mem_limit_total + m_val ))
        fi
      done
      if [ -n "$mem_used" ] && [ "$mem_limit_total" -gt 0 ]; then
        mem_pct=$(awk "BEGIN {printf \"%.1f\", ($mem_used / $mem_limit_total) * 100}")
      else
        mem_pct="N/A"
      fi

      printf "%-40s %-10s %-12s %-15s %-15s %-10s %-10s\n" \
        "$pod" "$cpu" "$mem" "${CPU_LIMIT:-N/A}" "${MEM_LIMIT:-N/A}" "$cpu_pct" "$mem_pct"
    done

    echo
  } >> "$LOG_FILE"

  sleep "$INTERVAL"
done

#!/bin/bash

# Configuration
LOCAL_BASE_DIR="./pod_logs_$(date +%Y%m%d_%H%M%S)"

declare -A PODS
declare -A REMOTE_PATHS

PODS[ntnx-ncm-common]="ncm-epsilon-0 ncm-epsilon-1 ncm-epsilon-2"
PODS[ntnx-ncm-self-service]="ncm-calm-0 ncm-calm-1 ncm-calm-2"

REMOTE_PATHS[ntnx-ncm-common]="/home/epsilon/log"
REMOTE_PATHS[ntnx-ncm-self-service]="/home/calm/log"

echo "============================================"
echo "Pod Log Collector"
echo "============================================"
echo "Output directory: $LOCAL_BASE_DIR"
echo ""

mkdir -p "$LOCAL_BASE_DIR"

total_files=0
total_pods=0

for NS in "${!PODS[@]}"; do
    REMOTE_PATH="${REMOTE_PATHS[$NS]}"
    echo "Namespace: $NS"
    echo "  Remote path: $REMOTE_PATH"
    
    for POD in ${PODS[$NS]}; do
        # Check if pod is running
        POD_STATUS=$(kubectl get pod -n "$NS" "$POD" -o jsonpath='{.status.phase}' 2>/dev/null)
        if [ "$POD_STATUS" != "Running" ]; then
            echo "  ⚠ $POD - Skipping (Status: ${POD_STATUS:-Not Found})"
            continue
        fi
        
        DEST_DIR="$LOCAL_BASE_DIR/${NS}/${POD}"
        mkdir -p "$DEST_DIR"
        
        # Copy log files
        echo -n "  ✓ $POD - Copying logs... "
        
        FILE_COUNT=$(kubectl exec -n "$NS" "$POD" -- sh -c "
            cd $REMOTE_PATH 2>/dev/null &&
            find . -maxdepth 1 -name '*.log' -type f -size +0c 2>/dev/null | wc -l
        " 2>/dev/null | tr -d '[:space:]')
        
        if [ "$FILE_COUNT" -gt 0 ] 2>/dev/null; then
            kubectl exec -n "$NS" "$POD" -- sh -c "
                cd $REMOTE_PATH &&
                find . -maxdepth 1 -name '*.log' -type f -size +0c -print0 |
                tar --null -czf - --files-from=-
            " 2>/dev/null | tar -xzf - -C "$DEST_DIR" 2>/dev/null
            
            echo "$FILE_COUNT file(s)"
            total_files=$((total_files + FILE_COUNT))
        else
            echo "No log files found"
            rmdir "$DEST_DIR" 2>/dev/null
        fi
        
        total_pods=$((total_pods + 1))
    done
    echo ""
done

echo "============================================"
echo "Summary"
echo "  Pods processed: $total_pods"
echo "  Total files copied: $total_files"
echo "  Output directory: $LOCAL_BASE_DIR"
echo "============================================"

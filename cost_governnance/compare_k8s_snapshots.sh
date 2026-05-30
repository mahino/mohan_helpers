#!/bin/bash
#
# K8s Cluster Snapshot Comparison Script
# Compares before/after snapshots from VM power down/up scenarios
# Usage: ./compare_k8s_snapshots.sh <before_dir> <after_dir> [output_file]
#

set -euo pipefail

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default directories
BEFORE_DIR="${1:-./cluster_snapshot_before}"
AFTER_DIR="${2:-./cluster_snapshot_after}"
OUTPUT_FILE="${3:-comparison_report_$(date +%Y%m%d_%H%M%S).log}"

# Ensure directories exist
if [[ ! -d "$BEFORE_DIR" ]] || [[ ! -d "$AFTER_DIR" ]]; then
    echo -e "${RED}Error: Before or After directory does not exist${NC}"
    echo "Usage: $0 <before_dir> <after_dir> [output_file]"
    exit 1
fi

# Function to print header
print_header() {
    local title="$1"
    local width=100
    local padding=$(( (width - ${#title}) / 2 ))
    echo ""
    printf '%*s' "$width" '' | tr ' ' '='
    echo ""
    printf '%*s%s%*s\n' "$padding" '' "$title" "$padding" ''
    printf '%*s' "$width" '' | tr ' ' '='
    echo ""
}

# Function to print section
print_section() {
    local title="$1"
    echo ""
    echo -e "${CYAN}┌──────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} ${BOLD}${title}${NC}"
    echo -e "${CYAN}└──────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
}

# Function to print table row
print_table_row() {
    printf "│ %-40s │ %-25s │ %-25s │\n" "$1" "$2" "$3"
}

# Function to print table separator
print_table_sep() {
    echo "├──────────────────────────────────────────┼───────────────────────────┼───────────────────────────┤"
}

# Function to print table header
print_table_header() {
    echo "┌──────────────────────────────────────────┬───────────────────────────┬───────────────────────────┐"
    printf "│ %-40s │ %-25s │ %-25s │\n" "RESOURCE" "BEFORE" "AFTER"
    echo "├──────────────────────────────────────────┼───────────────────────────┼───────────────────────────┤"
}

# Function to print table footer
print_table_footer() {
    echo "└──────────────────────────────────────────┴───────────────────────────┴───────────────────────────┘"
}

# Function to extract node status
get_node_status() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{print $1, $2}' | sort
    fi
}

# Function to get node age comparison
get_node_ages() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{print $1, $5}' | sort
    fi
}

# Function to count events by type
count_events_by_type() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{print $3}' | sort | uniq -c | sort -rn
    fi
}

# Function to count events by reason
count_events_by_reason() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{print $4}' | sort | uniq -c | sort -rn | head -15
    fi
}

# Function to get statefulset ready status
get_statefulset_status() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{print $1"/"$2, $3}' | sort
    fi
}

# Function to check kube-system pods
get_kube_system_status() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{print $1, $3, $4}' | sort
    fi
}

# Function to count pods by status
count_pods_by_status() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{print $3}' | sort | uniq -c | sort -rn
    fi
}

# Function to count total restarts
count_total_restarts() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{
            # Handle restart counts like "8 (2d22h ago)" or just "8"
            split($4, parts, " ")
            gsub(/[^0-9]/, "", parts[1])
            if (parts[1] != "") sum += parts[1]
        } END {print sum+0}'
    fi
}

# Function to compare PDB status
get_pdb_disruptions() {
    local file="$1"
    if [[ -f "$file" ]]; then
        tail -n +2 "$file" | awk '{print $1"/"$2, $5}' | sort
    fi
}

# Function to get node pod count and resources from JSON files
get_node_resources() {
    local json_file="$1"
    if [[ -f "$json_file" ]]; then
        # Get first entry which contains node-level aggregates
        head -16 "$json_file" | grep -E '"pod_count"|"cpu_req"|"mem_req"|"cpu_lim"|"mem_lim"' | head -5
    fi
}

# Function to extract specific value from node JSON
get_node_json_value() {
    local json_file="$1"
    local key="$2"
    if [[ -f "$json_file" ]]; then
        grep -m1 "\"$key\"" "$json_file" 2>/dev/null | sed 's/.*: *\([0-9]*\).*/\1/' | head -1
    else
        echo "N/A"
    fi
}

# Start report generation
{
    print_header "K8S CLUSTER SNAPSHOT COMPARISON REPORT"
    echo ""
    echo "Generated: $(date)"
    echo "Before Snapshot: $BEFORE_DIR"
    echo "After Snapshot:  $AFTER_DIR"
    echo ""

    # =============================================================================
    # VERSION INFO
    # =============================================================================
    print_section "KUBERNETES VERSION"
    
    echo ""
    echo "BEFORE:"
    cat "$BEFORE_DIR/version.txt" 2>/dev/null | sed 's/^/  /'
    echo ""
    echo "AFTER:"
    cat "$AFTER_DIR/version.txt" 2>/dev/null | sed 's/^/  /'

    # =============================================================================
    # NODE STATUS COMPARISON
    # =============================================================================
    print_section "NODE STATUS COMPARISON"
    
    print_table_header
    
    # Get unique node names from both files
    nodes_before=$(tail -n +2 "$BEFORE_DIR/nodes.txt" 2>/dev/null | awk '{print $1}' | sort)
    nodes_after=$(tail -n +2 "$AFTER_DIR/nodes.txt" 2>/dev/null | awk '{print $1}' | sort)
    all_nodes=$(echo -e "$nodes_before\n$nodes_after" | sort -u)
    
    while IFS= read -r node; do
        [[ -z "$node" ]] && continue
        
        # Get status and age from before (columns: NAME STATUS ROLES AGE VERSION)
        status_before=$(tail -n +2 "$BEFORE_DIR/nodes.txt" 2>/dev/null | awk -v n="$node" '$1==n {print $2}')
        age_before=$(tail -n +2 "$BEFORE_DIR/nodes.txt" 2>/dev/null | awk -v n="$node" '$1==n {print $4}')
        
        # Get status and age from after
        status_after=$(tail -n +2 "$AFTER_DIR/nodes.txt" 2>/dev/null | awk -v n="$node" '$1==n {print $2}')
        age_after=$(tail -n +2 "$AFTER_DIR/nodes.txt" 2>/dev/null | awk -v n="$node" '$1==n {print $4}')
        
        status_before="${status_before:-N/A} (age:${age_before:-N/A})"
        status_after="${status_after:-N/A} (age:${age_after:-N/A})"
        
        print_table_row "$node" "$status_before" "$status_after"
    done <<< "$all_nodes"
    
    print_table_footer

    # Node taints comparison
    echo ""
    echo "Node Taints Comparison:"
    echo "───────────────────────"
    echo "BEFORE:"
    cat "$BEFORE_DIR/node_taints.txt" 2>/dev/null | sed 's/^/  /'
    echo ""
    echo "AFTER:"
    cat "$AFTER_DIR/node_taints.txt" 2>/dev/null | sed 's/^/  /'

    # =============================================================================
    # NODE PODS AND RESOURCES
    # =============================================================================
    print_section "NODE PODS & RESOURCES PER VM"
    
    echo ""
    echo "┌───────────────────────┬────────────┬────────────┬────────────────────────────┬────────────────────────────┐"
    printf "│ %-21s │ %-10s │ %-10s │ %-26s │ %-26s │\n" "NODE" "B-PODS" "A-PODS" "BEFORE RESOURCES" "AFTER RESOURCES"
    echo "├───────────────────────┼────────────┼────────────┼────────────────────────────┼────────────────────────────┤"
    
    total_pods_before=0
    total_pods_after=0
    total_cpu_req_before=0
    total_cpu_req_after=0
    total_mem_req_before=0
    total_mem_req_after=0
    
    while IFS= read -r node; do
        [[ -z "$node" ]] && continue
        
        # Get before values from node JSON
        before_json="$BEFORE_DIR/nodes/${node}.json"
        after_json="$AFTER_DIR/nodes/${node}.json"
        
        # Extract pod count
        pods_before=$(get_node_json_value "$before_json" "pod_count")
        pods_after=$(get_node_json_value "$after_json" "pod_count")
        
        # Extract resource values (in millicores for CPU, Mi for memory)
        cpu_req_before=$(get_node_json_value "$before_json" "cpu_req")
        mem_req_before=$(get_node_json_value "$before_json" "mem_req")
        cpu_req_after=$(get_node_json_value "$after_json" "cpu_req")
        mem_req_after=$(get_node_json_value "$after_json" "mem_req")
        
        # Format resource strings
        if [[ "$cpu_req_before" != "N/A" ]] && [[ "$mem_req_before" != "N/A" ]]; then
            res_before="CPU:${cpu_req_before}m MEM:${mem_req_before}Mi"
            total_cpu_req_before=$((total_cpu_req_before + cpu_req_before))
            total_mem_req_before=$((total_mem_req_before + mem_req_before))
        else
            res_before="N/A"
        fi
        
        if [[ "$cpu_req_after" != "N/A" ]] && [[ "$mem_req_after" != "N/A" ]]; then
            res_after="CPU:${cpu_req_after}m MEM:${mem_req_after}Mi"
            total_cpu_req_after=$((total_cpu_req_after + cpu_req_after))
            total_mem_req_after=$((total_mem_req_after + mem_req_after))
        else
            res_after="N/A"
        fi
        
        # Update totals
        [[ "$pods_before" != "N/A" ]] && total_pods_before=$((total_pods_before + pods_before))
        [[ "$pods_after" != "N/A" ]] && total_pods_after=$((total_pods_after + pods_after))
        
        # Truncate node name for display
        node_short="${node:0:21}"
        
        # Highlight changes
        if [[ "$pods_before" != "$pods_after" ]]; then
            printf "│ %-21s │ %-10s │ %-10s │ %-26s │ %-26s │ *\n" \
                "$node_short" "${pods_before:-N/A}" "${pods_after:-N/A}" "$res_before" "$res_after"
        else
            printf "│ %-21s │ %-10s │ %-10s │ %-26s │ %-26s │\n" \
                "$node_short" "${pods_before:-N/A}" "${pods_after:-N/A}" "$res_before" "$res_after"
        fi
    done <<< "$all_nodes"
    
    echo "├───────────────────────┼────────────┼────────────┼────────────────────────────┼────────────────────────────┤"
    printf "│ %-21s │ %-10s │ %-10s │ %-26s │ %-26s │\n" \
        "TOTAL" "$total_pods_before" "$total_pods_after" \
        "CPU:${total_cpu_req_before}m MEM:${total_mem_req_before}Mi" \
        "CPU:${total_cpu_req_after}m MEM:${total_mem_req_after}Mi"
    echo "└───────────────────────┴────────────┴────────────┴────────────────────────────┴────────────────────────────┘"
    
    # Calculate and show deltas
    echo ""
    echo "Pod/Resource Delta Summary:"
    echo "  Total Pods:    Before=$total_pods_before  After=$total_pods_after  Delta=$((total_pods_after - total_pods_before))"
    echo "  Total CPU Req: Before=${total_cpu_req_before}m  After=${total_cpu_req_after}m  Delta=$((total_cpu_req_after - total_cpu_req_before))m"
    echo "  Total Mem Req: Before=${total_mem_req_before}Mi  After=${total_mem_req_after}Mi  Delta=$((total_mem_req_after - total_mem_req_before))Mi"

    # =============================================================================
    # DELETED AND ADDED PODS PER NODE
    # =============================================================================
    print_section "DELETED & ADDED PODS PER VM"
    
    echo ""
    for node in $all_nodes; do
        [[ -z "$node" ]] && continue
        
        before_json="$BEFORE_DIR/nodes/${node}.json"
        after_json="$AFTER_DIR/nodes/${node}.json"
        
        # Extract pod names from before
        if [[ -f "$before_json" ]]; then
            pods_list_before=$(grep -o '"name": "[^"]*"' "$before_json" 2>/dev/null | sed 's/"name": "//g; s/"//g' | sort -u)
        else
            pods_list_before=""
        fi
        
        # Extract pod names from after
        if [[ -f "$after_json" ]]; then
            pods_list_after=$(grep -o '"name": "[^"]*"' "$after_json" 2>/dev/null | sed 's/"name": "//g; s/"//g' | sort -u)
        else
            pods_list_after=""
        fi
        
        # Find deleted pods (in before but not in after)
        deleted_pods=$(comm -23 <(echo "$pods_list_before" | sort) <(echo "$pods_list_after" | sort) 2>/dev/null | grep -v "^$")
        deleted_count=$(echo "$deleted_pods" | grep -c "." 2>/dev/null || echo 0)
        
        # Find added pods (in after but not in before)
        added_pods=$(comm -13 <(echo "$pods_list_before" | sort) <(echo "$pods_list_after" | sort) 2>/dev/null | grep -v "^$")
        added_count=$(echo "$added_pods" | grep -c "." 2>/dev/null || echo 0)
        
        # Get pod counts
        pods_before=$(get_node_json_value "$before_json" "pod_count")
        pods_after=$(get_node_json_value "$after_json" "pod_count")
        
        echo "┌─────────────────────────────────────────────────────────────────────────────────────────────────┐"
        printf "│ NODE: %-30s  PODS BEFORE: %-6s  PODS AFTER: %-6s  DELTA: %-+6d │\n" \
            "$node" "${pods_before:-0}" "${pods_after:-0}" "$((${pods_after:-0} - ${pods_before:-0}))"
        echo "├─────────────────────────────────────────────────────────────────────────────────────────────────┤"
        
        # Show deleted pods
        if [[ $deleted_count -gt 0 ]]; then
            printf "│ DELETED PODS (%d):%-77s│\n" "$deleted_count" ""
            echo "$deleted_pods" | head -20 | while read -r pod; do
                [[ -z "$pod" ]] && continue
                printf "│   - %-89s│\n" "${pod:0:89}"
            done
            if [[ $deleted_count -gt 20 ]]; then
                printf "│   ... and %d more%-78s│\n" "$((deleted_count - 20))" ""
            fi
        else
            printf "│ DELETED PODS: (none)%-73s│\n" ""
        fi
        
        echo "│─────────────────────────────────────────────────────────────────────────────────────────────────│"
        
        # Show added pods
        if [[ $added_count -gt 0 ]]; then
            printf "│ ADDED PODS (%d):%-79s│\n" "$added_count" ""
            echo "$added_pods" | head -20 | while read -r pod; do
                [[ -z "$pod" ]] && continue
                printf "│   + %-89s│\n" "${pod:0:89}"
            done
            if [[ $added_count -gt 20 ]]; then
                printf "│   ... and %d more%-78s│\n" "$((added_count - 20))" ""
            fi
        else
            printf "│ ADDED PODS: (none)%-75s│\n" ""
        fi
        
        echo "└─────────────────────────────────────────────────────────────────────────────────────────────────┘"
        echo ""
    done

    # =============================================================================
    # STATEFULSET STATUS
    # =============================================================================
    print_section "STATEFULSET STATUS COMPARISON"
    
    echo ""
    echo "┌──────────────────────────────────────────────────────────┬─────────────────┬─────────────────┐"
    printf "│ %-56s │ %-15s │ %-15s │\n" "NAMESPACE/STATEFULSET" "BEFORE READY" "AFTER READY"
    echo "├──────────────────────────────────────────────────────────┼─────────────────┼─────────────────┤"
    
    # Get statefulset names
    sts_before=$(tail -n +2 "$BEFORE_DIR/statefulsets.txt" 2>/dev/null | awk '{print $1"/"$2}' | sort)
    sts_after=$(tail -n +2 "$AFTER_DIR/statefulsets.txt" 2>/dev/null | awk '{print $1"/"$2}' | sort)
    all_sts=$(echo -e "$sts_before\n$sts_after" | sort -u)
    
    sts_changes=0
    while IFS= read -r sts; do
        [[ -z "$sts" ]] && continue
        ns=$(echo "$sts" | cut -d'/' -f1)
        name=$(echo "$sts" | cut -d'/' -f2)
        
        ready_before=$(tail -n +2 "$BEFORE_DIR/statefulsets.txt" 2>/dev/null | awk -v n="$ns" -v s="$name" '$1==n && $2==s {print $3}')
        age_before=$(tail -n +2 "$BEFORE_DIR/statefulsets.txt" 2>/dev/null | awk -v n="$ns" -v s="$name" '$1==n && $2==s {print $4}')
        
        ready_after=$(tail -n +2 "$AFTER_DIR/statefulsets.txt" 2>/dev/null | awk -v n="$ns" -v s="$name" '$1==n && $2==s {print $3}')
        age_after=$(tail -n +2 "$AFTER_DIR/statefulsets.txt" 2>/dev/null | awk -v n="$ns" -v s="$name" '$1==n && $2==s {print $4}')
        
        before_str="${ready_before:-N/A} (${age_before:-N/A})"
        after_str="${ready_after:-N/A} (${age_after:-N/A})"
        
        # Highlight changes
        if [[ "$ready_before" != "$ready_after" ]]; then
            ((sts_changes++))
            printf "│ %-56s │ %-15s │ %-15s │ *CHANGED*\n" "$sts" "$before_str" "$after_str"
        else
            printf "│ %-56s │ %-15s │ %-15s │\n" "$sts" "$before_str" "$after_str"
        fi
    done <<< "$all_sts"
    
    echo "└──────────────────────────────────────────────────────────┴─────────────────┴─────────────────┘"
    echo ""
    echo "Total StatefulSets with changes: $sts_changes"

    # =============================================================================
    # KUBE-SYSTEM PODS STATUS
    # =============================================================================
    print_section "KUBE-SYSTEM PODS COMPARISON"
    
    echo ""
    echo "┌────────────────────────────────────────┬────────────┬──────────────┬────────────┬──────────────┐"
    printf "│ %-38s │ %-10s │ %-12s │ %-10s │ %-12s │\n" "POD NAME" "B-STATUS" "B-RESTARTS" "A-STATUS" "A-RESTARTS"
    echo "├────────────────────────────────────────┼────────────┼──────────────┼────────────┼──────────────┤"
    
    pods_before=$(tail -n +2 "$BEFORE_DIR/kube_system_pods.txt" 2>/dev/null | awk '{print $1}' | sort)
    pods_after=$(tail -n +2 "$AFTER_DIR/kube_system_pods.txt" 2>/dev/null | awk '{print $1}' | sort)
    all_pods=$(echo -e "$pods_before\n$pods_after" | sort -u)
    
    while IFS= read -r pod; do
        [[ -z "$pod" ]] && continue
        
        status_before=$(tail -n +2 "$BEFORE_DIR/kube_system_pods.txt" 2>/dev/null | awk -v p="$pod" '$1==p {print $3}')
        restarts_before=$(tail -n +2 "$BEFORE_DIR/kube_system_pods.txt" 2>/dev/null | awk -v p="$pod" '$1==p {print $4}')
        
        status_after=$(tail -n +2 "$AFTER_DIR/kube_system_pods.txt" 2>/dev/null | awk -v p="$pod" '$1==p {print $3}')
        restarts_after=$(tail -n +2 "$AFTER_DIR/kube_system_pods.txt" 2>/dev/null | awk -v p="$pod" '$1==p {print $4}')
        
        # Check for pod name changes (could be due to pod recreation)
        pod_short="${pod:0:38}"
        printf "│ %-38s │ %-10s │ %-12s │ %-10s │ %-12s │\n" \
            "$pod_short" \
            "${status_before:-MISSING}" \
            "${restarts_before:-N/A}" \
            "${status_after:-MISSING}" \
            "${restarts_after:-N/A}"
    done <<< "$all_pods"
    
    echo "└────────────────────────────────────────┴────────────┴──────────────┴────────────┴──────────────┘"

    # Count total restarts
    total_restarts_before=$(count_total_restarts "$BEFORE_DIR/kube_system_pods.txt")
    total_restarts_after=$(count_total_restarts "$AFTER_DIR/kube_system_pods.txt")
    
    echo ""
    echo "Kube-System Restart Summary:"
    echo "  Before: $total_restarts_before total restarts recorded"
    echo "  After:  $total_restarts_after total restarts recorded"

    # =============================================================================
    # EVENTS COMPARISON
    # =============================================================================
    print_section "EVENTS ANALYSIS"
    
    events_before=$(wc -l < "$BEFORE_DIR/events.txt" 2>/dev/null || echo 0)
    events_after=$(wc -l < "$AFTER_DIR/events.txt" 2>/dev/null || echo 0)
    
    echo ""
    echo "Event Count Summary:"
    echo "┌─────────────────────────────────┬─────────────────┬─────────────────┐"
    printf "│ %-31s │ %-15s │ %-15s │\n" "METRIC" "BEFORE" "AFTER"
    echo "├─────────────────────────────────┼─────────────────┼─────────────────┤"
    printf "│ %-31s │ %-15s │ %-15s │\n" "Total Events" "$((events_before-1))" "$((events_after-1))"
    echo "└─────────────────────────────────┴─────────────────┴─────────────────┘"
    
    echo ""
    echo "Events by Type (Before):"
    echo "─────────────────────────"
    count_events_by_type "$BEFORE_DIR/events.txt" | while read -r count type; do
        printf "  %-15s: %s\n" "$type" "$count"
    done
    
    echo ""
    echo "Events by Type (After):"
    echo "────────────────────────"
    count_events_by_type "$AFTER_DIR/events.txt" | while read -r count type; do
        printf "  %-15s: %s\n" "$type" "$count"
    done
    
    echo ""
    echo "Top Event Reasons (Before - top 15):"
    echo "─────────────────────────────────────"
    count_events_by_reason "$BEFORE_DIR/events.txt" | while read -r count reason; do
        printf "  %-45s: %s\n" "$reason" "$count"
    done
    
    echo ""
    echo "Top Event Reasons (After - top 15):"
    echo "────────────────────────────────────"
    count_events_by_reason "$AFTER_DIR/events.txt" | while read -r count reason; do
        printf "  %-45s: %s\n" "$reason" "$count"
    done

    # =============================================================================
    # PDB (PodDisruptionBudget) STATUS
    # =============================================================================
    print_section "PDB (POD DISRUPTION BUDGET) COMPARISON"
    
    echo ""
    echo "┌───────────────────────────────────────────────────────────────┬───────────────┬───────────────┐"
    printf "│ %-61s │ %-13s │ %-13s │\n" "NAMESPACE/PDB" "B-DISRUPTIONS" "A-DISRUPTIONS"
    echo "├───────────────────────────────────────────────────────────────┼───────────────┼───────────────┤"
    
    pdb_before=$(tail -n +2 "$BEFORE_DIR/pdbs.txt" 2>/dev/null | awk '{print $1"/"$2}' | sort)
    pdb_after=$(tail -n +2 "$AFTER_DIR/pdbs.txt" 2>/dev/null | awk '{print $1"/"$2}' | sort)
    all_pdbs=$(echo -e "$pdb_before\n$pdb_after" | sort -u)
    
    pdb_changes=0
    while IFS= read -r pdb; do
        [[ -z "$pdb" ]] && continue
        ns=$(echo "$pdb" | cut -d'/' -f1)
        name=$(echo "$pdb" | cut -d'/' -f2)
        
        disruptions_before=$(tail -n +2 "$BEFORE_DIR/pdbs.txt" 2>/dev/null | awk -v n="$ns" -v p="$name" '$1==n && $2==p {print $5}')
        disruptions_after=$(tail -n +2 "$AFTER_DIR/pdbs.txt" 2>/dev/null | awk -v n="$ns" -v p="$name" '$1==n && $2==p {print $5}')
        
        if [[ "$disruptions_before" != "$disruptions_after" ]]; then
            ((pdb_changes++))
            printf "│ %-61s │ %-13s │ %-13s │ *CHANGED*\n" "$pdb" "${disruptions_before:-N/A}" "${disruptions_after:-N/A}"
        else
            printf "│ %-61s │ %-13s │ %-13s │\n" "$pdb" "${disruptions_before:-N/A}" "${disruptions_after:-N/A}"
        fi
    done <<< "$all_pdbs"
    
    echo "└───────────────────────────────────────────────────────────────┴───────────────┴───────────────┘"
    echo ""
    echo "Total PDBs with disruption changes: $pdb_changes"

    # =============================================================================
    # LOCAL PVs
    # =============================================================================
    print_section "LOCAL PERSISTENT VOLUMES"
    
    pv_before=$(wc -l < "$BEFORE_DIR/local_pvs.txt" 2>/dev/null || echo 0)
    pv_after=$(wc -l < "$AFTER_DIR/local_pvs.txt" 2>/dev/null || echo 0)
    
    echo ""
    echo "Local PV Count:"
    echo "  Before: $pv_before"
    echo "  After:  $pv_after"
    
    if [[ -s "$BEFORE_DIR/local_pvs.txt" ]] || [[ -s "$AFTER_DIR/local_pvs.txt" ]]; then
        echo ""
        echo "Before Contents:"
        cat "$BEFORE_DIR/local_pvs.txt" 2>/dev/null | sed 's/^/  /' || echo "  (empty)"
        echo ""
        echo "After Contents:"
        cat "$AFTER_DIR/local_pvs.txt" 2>/dev/null | sed 's/^/  /' || echo "  (empty)"
    fi

    # =============================================================================
    # STANDALONE PODS
    # =============================================================================
    print_section "STANDALONE PODS"
    
    sp_before=$(wc -l < "$BEFORE_DIR/standalone_pods.txt" 2>/dev/null || echo 0)
    sp_after=$(wc -l < "$AFTER_DIR/standalone_pods.txt" 2>/dev/null || echo 0)
    
    echo ""
    echo "Standalone Pod Count:"
    echo "  Before: $sp_before"
    echo "  After:  $sp_after"
    
    if [[ -s "$BEFORE_DIR/standalone_pods.txt" ]] || [[ -s "$AFTER_DIR/standalone_pods.txt" ]]; then
        echo ""
        echo "Before Contents:"
        cat "$BEFORE_DIR/standalone_pods.txt" 2>/dev/null | sed 's/^/  /' || echo "  (empty)"
        echo ""
        echo "After Contents:"
        cat "$AFTER_DIR/standalone_pods.txt" 2>/dev/null | sed 's/^/  /' || echo "  (empty)"
    fi

    # =============================================================================
    # SUMMARY
    # =============================================================================
    print_section "COMPARISON SUMMARY"
    
    echo ""
    echo "┌────────────────────────────────────────────────┬─────────────────┬─────────────────┬──────────────┐"
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "METRIC" "BEFORE" "AFTER" "DELTA"
    echo "├────────────────────────────────────────────────┼─────────────────┼─────────────────┼──────────────┤"
    
    # Node count
    node_count_before=$(tail -n +2 "$BEFORE_DIR/nodes.txt" 2>/dev/null | wc -l || echo 0)
    node_count_after=$(tail -n +2 "$AFTER_DIR/nodes.txt" 2>/dev/null | wc -l || echo 0)
    node_delta=$((node_count_after - node_count_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "Node Count" "$node_count_before" "$node_count_after" "$node_delta"
    
    # Ready nodes
    ready_before=$(tail -n +2 "$BEFORE_DIR/nodes.txt" 2>/dev/null | grep -c "Ready" || echo 0)
    ready_after=$(tail -n +2 "$AFTER_DIR/nodes.txt" 2>/dev/null | grep -c "Ready" || echo 0)
    ready_delta=$((ready_after - ready_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "Ready Nodes" "$ready_before" "$ready_after" "$ready_delta"
    
    # StatefulSets
    sts_count_before=$(tail -n +2 "$BEFORE_DIR/statefulsets.txt" 2>/dev/null | wc -l || echo 0)
    sts_count_after=$(tail -n +2 "$AFTER_DIR/statefulsets.txt" 2>/dev/null | wc -l || echo 0)
    sts_delta=$((sts_count_after - sts_count_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "StatefulSet Count" "$sts_count_before" "$sts_count_after" "$sts_delta"
    
    # Kube-system pods
    ks_count_before=$(tail -n +2 "$BEFORE_DIR/kube_system_pods.txt" 2>/dev/null | wc -l || echo 0)
    ks_count_after=$(tail -n +2 "$AFTER_DIR/kube_system_pods.txt" 2>/dev/null | wc -l || echo 0)
    ks_delta=$((ks_count_after - ks_count_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "Kube-System Pod Count" "$ks_count_before" "$ks_count_after" "$ks_delta"
    
    # Total Kube-system restarts
    restart_delta=$((total_restarts_after - total_restarts_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "Kube-System Total Restarts" "$total_restarts_before" "$total_restarts_after" "$restart_delta"
    
    # Events
    events_delta=$((events_after - events_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "Total Events" "$((events_before-1))" "$((events_after-1))" "$events_delta"
    
    # PDBs
    pdb_count_before=$(tail -n +2 "$BEFORE_DIR/pdbs.txt" 2>/dev/null | wc -l || echo 0)
    pdb_count_after=$(tail -n +2 "$AFTER_DIR/pdbs.txt" 2>/dev/null | wc -l || echo 0)
    pdb_delta=$((pdb_count_after - pdb_count_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "PDB Count" "$pdb_count_before" "$pdb_count_after" "$pdb_delta"
    
    # Total cluster pods (from node JSON files)
    pods_delta=$((total_pods_after - total_pods_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "Total Cluster Pods" "$total_pods_before" "$total_pods_after" "$pods_delta"
    
    # Total CPU requests
    cpu_delta=$((total_cpu_req_after - total_cpu_req_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "Total CPU Requests (m)" "$total_cpu_req_before" "$total_cpu_req_after" "$cpu_delta"
    
    # Total Memory requests
    mem_delta=$((total_mem_req_after - total_mem_req_before))
    printf "│ %-46s │ %-15s │ %-15s │ %-12s │\n" "Total Memory Requests (Mi)" "$total_mem_req_before" "$total_mem_req_after" "$mem_delta"
    
    echo "└────────────────────────────────────────────────┴─────────────────┴─────────────────┴──────────────┘"
    
    # Key observations
    echo ""
    echo "Key Observations:"
    echo "─────────────────"
    
    # Check for node age changes (indicates recreated nodes)
    echo "• Node Age Changes (may indicate VM restart):"
    age_change_found=0
    while IFS= read -r node; do
        [[ -z "$node" ]] && continue
        age_before=$(tail -n +2 "$BEFORE_DIR/nodes.txt" 2>/dev/null | awk -v n="$node" '$1==n {print $4}')
        age_after=$(tail -n +2 "$AFTER_DIR/nodes.txt" 2>/dev/null | awk -v n="$node" '$1==n {print $4}')
        
        if [[ "$age_before" != "$age_after" ]]; then
            echo "  - $node: $age_before → $age_after"
            age_change_found=1
        fi
    done <<< "$all_nodes"
    [[ $age_change_found -eq 0 ]] && echo "  (No significant age changes detected)"
    
    # Check for new Warning events after
    echo ""
    echo "• New Warning Events After Scenario:"
    warning_count_before=$(tail -n +2 "$BEFORE_DIR/events.txt" 2>/dev/null | grep -c "Warning" || echo 0)
    warning_count_after=$(tail -n +2 "$AFTER_DIR/events.txt" 2>/dev/null | grep -c "Warning" || echo 0)
    echo "  Before: $warning_count_before warnings"
    echo "  After:  $warning_count_after warnings"
    echo "  Delta:  $((warning_count_after - warning_count_before))"

    print_header "END OF COMPARISON REPORT"
    
} | tee "$OUTPUT_FILE"

echo ""
echo -e "${GREEN}Report saved to: ${BOLD}$OUTPUT_FILE${NC}"


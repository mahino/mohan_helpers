#!/bin/bash

# Complete PostgreSQL Analysis - Single File Output
# Run this directly on PostgreSQL system - creates one comprehensive report

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="complete_pg_analysis_${TIMESTAMP}.txt"
DATABASES=("cg" "cg_cost" "cg_multicloud_metadata" "cg_nx" "cg_reports")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }


# Function to run SQL
run_sql() {
    local db_name=$1
    local sql_command=$2
    
    if command -v kubectl >/dev/null 2>&1; then
        kubectl exec -i -n ntnx-ncm-datastore cg-pg-1 -- psql -d "$db_name" -c "$sql_command" 2>/dev/null
    elif command -v psql >/dev/null 2>&1; then
        psql -d "$db_name" -c "$sql_command" 2>/dev/null
    fi
}

# Function to get row count (improved version)
get_row_count() {
    local db_name=$1
    local table_name=$2
    
    local result
    if command -v kubectl >/dev/null 2>&1; then
        result=$(kubectl exec -i -n ntnx-ncm-datastore cg-pg-1 -- psql -d "$db_name" -t -c "SELECT COUNT(*) FROM $table_name;" 2>/dev/null | tr -d ' ')
    elif command -v psql >/dev/null 2>&1; then
        result=$(psql -d "$db_name" -t -c "SELECT COUNT(*) FROM $table_name;" 2>/dev/null | tr -d ' ')
    fi
    
    # Return the result, or ERROR if empty
    if [[ -n "$result" && "$result" =~ ^[0-9]+$ ]]; then
        echo "$result"
    else
        echo "ERROR"
    fi
}

# Main analysis function
analyze_all_databases() {
    cat > "$OUTPUT_FILE" << EOF
================================================================================
COMPLETE POSTGRESQL DATABASE ANALYSIS
================================================================================
Generated: $(date)
Host: $(hostname)
Output File: $OUTPUT_FILE
================================================================================

EOF

    local total_db_size=0
    local total_tables=0
    local total_rows=0

    for db_name in "${DATABASES[@]}"; do
        echo_info "Analyzing database: $db_name"
        
        cat >> "$OUTPUT_FILE" << EOF

################################################################################
DATABASE: $db_name
################################################################################

EOF

        # Database size
        echo "DATABASE SIZE:" >> "$OUTPUT_FILE"
        echo "==============" >> "$OUTPUT_FILE"
        run_sql "$db_name" "SELECT datname as database_name, pg_size_pretty(pg_database_size(datname)) as database_size, pg_database_size(datname) as size_bytes FROM pg_database WHERE datname = '$db_name';" >> "$OUTPUT_FILE"
        echo >> "$OUTPUT_FILE"

        # Get all tables with sizes and estimated rows
        echo "ALL TABLES - SIZES AND ESTIMATED ROWS:" >> "$OUTPUT_FILE"
        echo "=======================================" >> "$OUTPUT_FILE"
        run_sql "$db_name" "
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
            COALESCE((SELECT reltuples::BIGINT FROM pg_class WHERE relname = tablename AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = schemaname)), 0) as estimated_rows
        FROM pg_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        " >> "$OUTPUT_FILE"
        
        echo >> "$OUTPUT_FILE"
        echo "EXACT ROW COUNTS FOR ALL TABLES:" >> "$OUTPUT_FILE"
        echo "=================================" >> "$OUTPUT_FILE"
        echo "Table Name                                              | Size       | Exact Row Count" >> "$OUTPUT_FILE"
        echo "--------------------------------------------------------|------------|----------------" >> "$OUTPUT_FILE"

        # Get all tables with their info (using the working method from simple script)
        local table_info
        if command -v kubectl >/dev/null 2>&1; then
            # First, let's see ALL tables including system ones for debugging
            echo_info "  Checking all tables in $db_name..."
            local all_tables=$(kubectl exec -i -n ntnx-ncm-datastore cg-pg-1 -- psql -d "$db_name" -t -c "
            SELECT 
                schemaname||'.'||tablename as full_name
            FROM pg_tables 
            ORDER BY schemaname, tablename;
            " 2>/dev/null)
            
            local user_table_count=$(echo "$all_tables" | grep -v '^[[:space:]]*$' | wc -l)
            echo_info "  Found $user_table_count total tables in $db_name"
            
            # Now get user tables with size info
            table_info=$(kubectl exec -i -n ntnx-ncm-datastore cg-pg-1 -- psql -d "$db_name" -t -c "
            SELECT 
                schemaname||'.'||tablename as full_name,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            " 2>/dev/null)
        elif command -v psql >/dev/null 2>&1; then
            # First, let's see ALL tables including system ones for debugging
            echo_info "  Checking all tables in $db_name..."
            local all_tables=$(psql -d "$db_name" -t -c "
            SELECT 
                schemaname||'.'||tablename as full_name
            FROM pg_tables 
            ORDER BY schemaname, tablename;
            " 2>/dev/null)
            
            local user_table_count=$(echo "$all_tables" | grep -v '^[[:space:]]*$' | wc -l)
            echo_info "  Found $user_table_count total tables in $db_name"
            
            # Now get user tables with size info
            table_info=$(psql -d "$db_name" -t -c "
            SELECT 
                schemaname||'.'||tablename as full_name,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            " 2>/dev/null)
        fi

        local db_table_count=0
        local db_total_rows=0
        
        # Count how many user tables we found
        local user_tables_found=$(echo "$table_info" | grep -v '^[[:space:]]*$' | wc -l)
        echo_info "  Found $user_tables_found user tables (excluding system tables) in $db_name"
        
        if [[ -n "$table_info" && "$user_tables_found" -gt 0 ]]; then
            while IFS='|' read -r table_name size_info; do
                # Clean up the data
                table_name=$(echo "$table_name" | tr -d ' ')
                size_info=$(echo "$size_info" | tr -d ' ')
                
                if [[ -n "$table_name" && "$table_name" != "" ]]; then
                    ((db_table_count++))
                    echo_info "  [$db_table_count] Counting rows in: $table_name"
                    
                    # Get exact row count
                    count_result=$(get_row_count "$db_name" "$table_name")
                    
                    if [[ -z "$count_result" ]]; then
                        count_result="ERROR"
                    fi
                    
                    # Add to total if it's a number
                    if [[ "$count_result" =~ ^[0-9]+$ ]]; then
                        ((db_total_rows += count_result))
                    fi
                    
                    # Format and write to file
                    printf "%-55s | %-10s | %15s\n" "$table_name" "$size_info" "$count_result" >> "$OUTPUT_FILE"
                fi
            done <<< "$table_info"
            
            echo >> "$OUTPUT_FILE"
            echo "ROW COUNT SUMMARY FOR $db_name:" >> "$OUTPUT_FILE"
            echo "Total Tables Processed: $db_table_count" >> "$OUTPUT_FILE"
            echo "Total Rows Counted: $db_total_rows" >> "$OUTPUT_FILE"
        else
            echo "No tables found in $db_name" >> "$OUTPUT_FILE"
        fi

        # Database summary
        echo >> "$OUTPUT_FILE"
        echo "DATABASE SUMMARY FOR $db_name:" >> "$OUTPUT_FILE"
        echo "==============================" >> "$OUTPUT_FILE"
        run_sql "$db_name" "
        SELECT 
            'Total Tables' as metric,
            COUNT(*)::text as value
        FROM pg_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        UNION ALL
        SELECT 
            'Total Indexes' as metric,
            COUNT(*)::text as value
        FROM pg_indexes 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast');
        " >> "$OUTPUT_FILE"

        echo >> "$OUTPUT_FILE"
        echo "SCHEMA BREAKDOWN FOR $db_name:" >> "$OUTPUT_FILE"
        echo "==============================" >> "$OUTPUT_FILE"
        run_sql "$db_name" "
        SELECT 
            schemaname,
            COUNT(*) as table_count,
            pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size
        FROM pg_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        GROUP BY schemaname
        ORDER BY SUM(pg_total_relation_size(schemaname||'.'||tablename)) DESC;
        " >> "$OUTPUT_FILE"

        echo >> "$OUTPUT_FILE"
    done

    # Overall summary
    cat >> "$OUTPUT_FILE" << EOF

################################################################################
OVERALL SUMMARY - ALL DATABASES
################################################################################

EOF

    echo "SUMMARY BY DATABASE:" >> "$OUTPUT_FILE"
    echo "====================" >> "$OUTPUT_FILE"
    
    for db_name in "${DATABASES[@]}"; do
        echo >> "$OUTPUT_FILE"
        echo "Database: $db_name" >> "$OUTPUT_FILE"
        echo "$(printf '=%.0s' {1..30})" >> "$OUTPUT_FILE"
        run_sql "$db_name" "
        SELECT 
            'Database Size: ' || pg_size_pretty(pg_database_size('$db_name')) as info
        UNION ALL
        SELECT 
            'Total Tables: ' || COUNT(*)::text as info
        FROM pg_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast');
        " >> "$OUTPUT_FILE"
    done

    cat >> "$OUTPUT_FILE" << EOF

################################################################################
TOP 20 LARGEST TABLES ACROSS ALL DATABASES
################################################################################

EOF

    echo "Rank | Database    | Table Name                                    | Size      | Est. Rows" >> "$OUTPUT_FILE"
    echo "-----|-------------|-----------------------------------------------|-----------|----------" >> "$OUTPUT_FILE"

    # Get top tables across all databases
    local rank=1
    for db_name in "${DATABASES[@]}"; do
        if command -v kubectl >/dev/null 2>&1; then
            kubectl exec -i -n ntnx-ncm-datastore cg-pg-1 -- psql -d "$db_name" -t -c "
            SELECT 
                '$db_name' as database,
                schemaname||'.'||tablename as table_name,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                COALESCE((SELECT reltuples::BIGINT FROM pg_class WHERE relname = tablename), 0) as estimated_rows,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 5;
            " 2>/dev/null | while IFS='|' read -r database table_name size estimated_rows size_bytes; do
                if [[ -n "$table_name" && "$table_name" != "" ]]; then
                    printf "%4d | %-11s | %-45s | %-9s | %s\n" "$rank" "$(echo $database | tr -d ' ')" "$(echo $table_name | tr -d ' ')" "$(echo $size | tr -d ' ')" "$(echo $estimated_rows | tr -d ' ')" >> "$OUTPUT_FILE"
                    ((rank++))
                fi
            done
        fi
    done

    cat >> "$OUTPUT_FILE" << EOF

################################################################################
ANALYSIS COMPLETE
################################################################################
Generated: $(date)
Total Databases Analyzed: ${#DATABASES[@]}
Output File: $OUTPUT_FILE
################################################################################

EOF
}

# Main execution
main() {
    echo_info "Starting Complete PostgreSQL Analysis..."
    echo_info "Output file: $OUTPUT_FILE"
    echo_info "Analyzing ${#DATABASES[@]} databases: ${DATABASES[*]}"
    echo

    # Check PostgreSQL access
    if command -v kubectl >/dev/null 2>&1; then
        echo_info "Using kubectl to access PostgreSQL pod"
        if ! kubectl get pods -n ntnx-ncm-datastore | grep -q cg-pg-1; then
            echo_error "PostgreSQL pod cg-pg-1 not found"
            exit 1
        fi
    elif command -v psql >/dev/null 2>&1; then
        echo_info "Using direct psql connection"
    else
        echo_error "Neither kubectl nor psql available"
        exit 1
    fi

    echo_success "PostgreSQL access confirmed"
    echo

    # Run complete analysis
    analyze_all_databases

    echo
    echo_success "Complete analysis finished!"
    echo_info "Results saved to: $OUTPUT_FILE"
    echo_info "File size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"
    echo
    echo_info "Quick preview of results:"
    echo "========================="
    head -50 "$OUTPUT_FILE"
    echo
    echo "... (see full results in $OUTPUT_FILE)"
}

# Parse arguments
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $0"
    echo "Complete PostgreSQL analysis - creates one comprehensive report"
    echo "Output: /tmp/complete_pg_analysis_TIMESTAMP.txt"
    exit 0
fi

# Run main function
main
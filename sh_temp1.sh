echo "Starting a time-consuming shell operation..."
sleep 2

log_file="time_script.log"
echo "Log file: $log_file"
echo "Script started at $(date)" > "$log_file"

function progress_bar() {
    local duration=$1
    local step=0
    local total=50
    echo -n "["
    while [ $step -le $total ]; do
        echo -n "#"
        sleep $((duration / total))
        ((step++))
    done
    echo "] Done!"
}

# Section 1: Fake System Check
echo -n "Checking system health..."
sleep 3
echo " OK"
echo "[INFO] System health: OK" >> "$log_file"

# Section 2: Fake CPU stress simulation
echo "Simulating CPU load..."
for i in {1..5}; do
    echo "CPU Load Phase $i/5..."
    sleep 2
    echo "[CPU] Load at $((RANDOM % 90 + 10))%" >> "$log_file"
done

# Section 3: Simulate memory diagnostics
echo "Running memory diagnostic..."
for i in {1..3}; do
    echo -n "Memory test $i... "
    sleep 2
    echo "PASSED"
    echo "[MEM] Test $i: PASSED" >> "$log_file"
done

# Section 4: Simulated File Scan
echo "Scanning files in /tmp (simulated)..."
file_count=0
for i in {1..10}; do
    echo "Scanning file_$i.tmp"
    sleep 1
    ((file_count++))
    echo "[SCAN] file_$i.tmp: OK" >> "$log_file"
done
echo "Total files scanned: $file_count"

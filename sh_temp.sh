#!/bin/bash

# Simulated Time-Consuming Script (100 lines)
# This script performs fake system checks, delays, loops, and visual progress indicators.

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

# Section 5: Simulated Network Check
echo "Checking network latency..."
for i in {1..5}; do
    latency=$((RANDOM % 100 + 20))
    echo "Ping #$i: $latency ms"
    echo "[NET] Ping $i: $latency ms" >> "$log_file"
    sleep 2
done

# Section 6: Simulated Progress Bar (fake install)
echo "Installing fake package..."
progress_bar 5

# Section 7: Counting down a fake reboot
echo "Reboot countdown..."
for i in {10..1}; do
    echo "$i..."
    sleep 1
done
echo "Reboot aborted. (Just kidding!)"
echo "[SYS] Reboot simulation complete." >> "$log_file"

# Section 8: Simulated database backup
echo "Backing up database (simulated)..."
for i in {1..5}; do
    echo "Backing up table_$i..."
    sleep 2
    echo "[DB] table_$i: Backup OK" >> "$log_file"
done

# Section 9: Create a dummy log file
echo "Generating dummy log data..."
for i in {1..10}; do
    echo "Log entry $i at $(date)" >> "$log_file"
    sleep 1
done

# Section 10: Wrap up
echo "Finalizing..."
sleep 2
echo "Cleaning up temporary files..."
sleep 2
echo "[CLEANUP] Complete" >> "$log_file"

# Padding to 100 lines
for i in {1..10}; do
    echo "[PAD] Padding log line $i" >> "$log_file"
    sleep 0.2
done

echo "Script completed at $(date)"
echo "[DONE] Script completed." >> "$log_file"

# End

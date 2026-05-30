#!/bin/bash

SCRIPT=$1

# Check if the script is running
if pgrep -f "$SCRIPT" >/dev/null; then
    exit 0  # Process is running, exit successfully
else
    echo "$SCRIPT is not running. Restarting..."
    /usr/local/bin/"$SCRIPT" &
    exit 1  # Process is not running, exit with error
fi

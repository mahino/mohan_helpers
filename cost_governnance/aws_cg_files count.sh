#!/bin/bash

# Loop through all buckets
for b in $(aws s3 ls --endpoint-url http://localhost:7200 | awk '{print $3}'); do
  # Get total size and file count
  summary=$(aws s3 ls s3://$b --recursive --human-readable --summarize --endpoint-url http://localhost:7200)
  
  # Extract total size and total file count
  size=$(echo "$summary" | grep "Total Size" | awk '{print $3 $4}')
  count=$(echo "$summary" | grep "Total Objects" | awk '{print $3}')
  
  # Print in desired format
  echo "Bucket: $b, File count: $count, Total size: $size"
done

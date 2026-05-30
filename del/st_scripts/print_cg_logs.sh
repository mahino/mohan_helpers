#!/bin/bash

NAMESPACE="ncm-cg"
DURATION=120000  # 20 minutes in seconds

mkdir -p pod-logs

# Check for 'ts' command
if ! command -v ts &>/dev/null; then
	  echo "'ts' not found. Installing moreutils is recommended for proper timestamping."
	    echo "Using fallback to awk for timestamping."
	      USE_AWK=true
      else
	        USE_AWK=false
	fi

	for pod in $(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}'); do
		  echo "Streaming logs for pod: $pod"
		    
		    if [ "$USE_AWK" = true ]; then
			        kubectl logs -n "$NAMESPACE" -f "$pod" --tail=0 2>&1 | awk '{ print strftime("[%Y-%m-%d %H:%M:%S]"), $0; fflush(); }' >> "pod-logs/${pod}.log" &
				  else
					      kubectl logs -n "$NAMESPACE" -f "$pod" --tail=0 2>&1 | ts '[%Y-%m-%d %H:%M:%S]' >> "pod-logs/${pod}.log" &
					        fi
					done

					sleep "$DURATION"
					echo "Stopping log streams..."
					kill $(jobs -p)

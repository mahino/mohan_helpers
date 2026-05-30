#!/bin/bash

# Set log file path (with timestamp)
LOG_FILE="data_loader_$(date +%Y-%m-%d_%H-%M-%S).log"

# Redirect all output (stdout + stderr) to log file AND console
exec > >(tee -a "$LOG_FILE") 2>&1

echo "===== Starting Data Loader Script ====="
date
echo "Logs will be saved to: $LOG_FILE"
echo


for i in {1..20}; do
	    echo "===== Iteration $i ====="
	        date

		    echo "Checking nutanix_backfill_job_run_status..."
		        kubectl exec -ti -n ntnx-ncm-datastore cg-pg-1 -- \
				        psql -d cg_nx -c "SELECT * FROM nutanix_backfill_job_run_status;"

			# Calculate epoch time 8 hours ago (8 hours = 28800 seconds)
			s=$(($(date +%s%3N) - 28810000))
			    echo "Updating nutanix_backfill_job_run_status..."
			        kubectl exec -ti -n ntnx-ncm-datastore cg-pg-1 -- \
					        psql -d cg_nx -c "UPDATE nutanix_backfill_job_run_status SET is_completed = false, last_persisted_epoch = $s, last_completed_date = $s;"

				    JOB_NAME="cron-nx-cg-data-loader-manual-trigger-$i-$(date +%Y-%m-%d-%H-%M-%S)"
				        echo "Creating job: $JOB_NAME"
					    kubectl create job --from=cronjob/cron-nx-cg-data-loader "$JOB_NAME" -n ncm-cg

					        echo "Data loader job created."
						    echo "Checking nutanix_backfill_job_run_status after job creation..."
						        kubectl exec -ti -n ntnx-ncm-datastore cg-pg-1 -- \
								        psql -d cg_nx -c "SELECT * FROM nutanix_backfill_job_run_status;"

							    echo "Sleeping for 10800 seconds (180 min) before next iteration..."
							        for j in {1..108}; do
									        date
										        sleep 100
											    done
										    done

										    echo "===== Data Loader Job Completed ====="
										    date



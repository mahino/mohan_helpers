sshpass -p "RDMCluster.123" ssh -o StrictHostKeyChecking=no nutanix@$1 "~/prism/cli/ncli cluster info"

# sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@$1 "echo nucalm; kubectl exec -i -n ntnx-ncm-self-service ncm-calm-0 -- cat home/calm/conf/commit_ids.txt ;echo epsilon; kubectl exec -i -n ntnx-ncm-common ncm-epsilon-0 -- cat home/epsilon/conf/commit_ids.txt;"

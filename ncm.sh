sshpass -p 'RDMCluster.123' ssh -o StrictHostKeyChecking=no nutanix@$1 "echo -e '$1 ss_decoupling.nu.com\n$1 ncm.ss_decoupling.nu.com' | sudo tee -a /etc/hosts"

# PUT https://10.115.150.160:9440/PrismGateway/services/rest/v1/cluster
# {"name":"PC_10.115.150.160","clusterExternalIPAddress":"10.115.150.160","clusterFullyQualifiedDomainName":"ss-decoupling.nutanix.com"}
# {"value":true}
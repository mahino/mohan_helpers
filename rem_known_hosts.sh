
for ip in 10.46.8.63 10.46.8.111 10.46.8.202
do
  echo $ip
  sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no ubuntu@$ip "sudo rm .ssh/known_hosts"
done

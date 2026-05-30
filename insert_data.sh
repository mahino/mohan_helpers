echo $3
sshpass -p "nutanix/4u" scp insert_data.py nutanix@$3:/home/nutanix/
sshpass -p "nutanix/4u" scp csv nutanix@$3:/home/nutanix/
echo lol
sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@$3 "python3 -m pip install pysocks --user; python3 insert_data.py $3 latencies $2 $1"

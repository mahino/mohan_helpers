rm -rf /home/mohan.as/.ssh/known_hosts
for pc in $2 $3 $4
do
sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@$pc "
docker ps;
/usr/local/nutanix/cluster/bin/genesis stop nucalm epsilon domain_manager
docker rmi -f nucalm epsilon domain_manager;
cd /home/docker/nucalm;
rm nucalm.tar.xz;
wget http://10.40.64.33:/GoldImages/NuCalm/docker/$1/nucalm.tar.xz;
cd ../epsilon;
rm epsilon.tar.xz;
wget http://10.40.64.33:/GoldImages/epsilon/docker/$1/epsilon.tar.xz

cd ../domain-manager;
rm domain-manager.tar.xz;
wget http://10.40.64.33:/GoldImages/domain_manager/docker/$1/domain_manager.tar.xz;
mv domain_manager.tar.xz domain-manager.tar.xz"
done
sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@$2 "/usr/local/nutanix/cluster/bin/cluster start"

for pc in $2 $3 $4
do
sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@$pc "
docker ps;
/usr/local/nutanix/cluster/bin/genesis stop nucalm epsilon
docker rmi nucalm epsilon -f;
cd /usr/local/nutanix/nucalm;
rm nucalm.tar.xz;
wget $1/nucalm.tar.xz;
cd ../epsilon;
rm epsilon.tar.xz;
wget $1/epsilon.tar.xz"
done
sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@$2 "/usr/local/nutanix/cluster/bin/cluster start"


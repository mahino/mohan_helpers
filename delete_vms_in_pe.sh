count=1
while true
do
  # sshpass -p RDMCluster.123 ssh nutanix@$1 '/usr/local/nutanix/bin/acli vm.list | grep ahv_ins_delete' > /home/mohan.as/mohan_helpers/vm_list
  # echo "sshpass -p RDMCluster.123 ssh nutanix@$1 '/usr/local/nutanix/bin/acli vm.list | grep ahv_ins_delete' > /home/mohan.as/mohan_helpers/vm_list"
  # sleep 1
  # python helper_delete_vms_in_pe.py
  for vm_name in `tac vm_list`
  do
    echo $vm_name
    sshpass -p RDMCluster.123 ssh nutanix@$1 "/usr/local/nutanix/bin/acli vm.delete $vm_name" < yes
  done
  echo "[$count] loop"
  date
  sleep 3600
  count=$((count+1))
done

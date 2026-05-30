#!/usr/bin/bash

mock_vm_status='export APP_MODE=TEST'
if [ "$MOCK_VM_STATUS" = "disable" ]; then
  mock_vm_status="#$mock_vm_status"
fi

for pc in $1 $2 $3
do

sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@$pc <<EOF
docker exec -i epsilon bash -c '
line_number=\$(grep -n "export APP_MODE=TEST" /home/epsilon/bin/indra.sh | cut -d: -f1)
if [ -z "\$line_number" ]; then
  line_number=3
fi
echo "Line number determined: \$line_number";
sed -i "\${line_number}s/.*/$mock_vm_status/" /home/epsilon/bin/indra.sh;
source /home/epsilon/venv/bin/activate supervisorctl -c /home/epsilon/conf/supervisor/supervisord.conf restart epsilon-engine:indra_0 epsilon-engine:indra_1'
EOF
sleep 10
done

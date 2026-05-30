#!/usr/bin/env bash

for pc in $1 $2 $3
do
sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@$pc << EOF
docker exec -i epsilon bash -c "sed -i '3s/.*/export APP_MODE=TEST/' /home/epsilon/bin/indra.sh;source /home/epsilon/venv/bin/activate;supervisorctl -c /home/epsilon/conf/supervisor/supervisord.conf restart epsilon-engine:indra_0 epsilon-engine:indra_1"
EOF
done

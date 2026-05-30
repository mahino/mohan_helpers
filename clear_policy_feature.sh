#!/usr/bin/env bash

sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@10.36.199.$1 << EOF
docker exec -i nucalm bash -c "/home/epsilon/venv/bin/activate;
wget http://10.40.64.33/GoldImages/Calm-Policy-Engine/scripts/clear_policy_feature.py;
python  clear_policy_feature.py"
EOF


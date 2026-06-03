# Quick Start Guide - PC Log Fetcher

## 🚀 Quick Start (3 Steps)

### Step 1: Test Connection
```bash
./test_pc_connection.sh 10.114.55.128 nutanix/4u
```

### Step 2: Fetch Logs (Single PC)
```bash
./fetch_pc_logs_auto.sh 10.114.55.128 nutanix/4u
```

### Step 3: View Logs
```bash
ls -lh pc_logs/10.114.55.128_*/logs/
```

---

## 📋 Common Commands

### Single PC - Manual Password Entry
```bash
./fetch_pc_logs.sh 10.114.55.128
```

### Single PC - Automated
```bash
export PC_PASSWORD="nutanix/4u"
./fetch_pc_logs_auto.sh 10.114.55.128
```

### Multiple PCs - Create List File
```bash
cat > pc_list.txt << EOF
10.114.55.128 nutanix/4u Production
10.114.55.129 nutanix/4u Staging
10.114.55.130 nutanix/4u Development
EOF

./fetch_multiple_pc_logs.sh pc_list.txt
```

### Using Environment Variables
```bash
export PC_PASSWORD="nutanix/4u"
export PC_USER="nutanix"
./fetch_pc_logs_auto.sh 10.114.55.128
```

---

## 📁 Output Location

**Kubeconfigs:**
```
./kubeconfigs/
└── 10.114.55.128_kubeconfig_20260601_120000
```

**Logs:**
```
./pc_logs/
└── 10.114.55.128_20260601_120000/
    └── logs/
        ├── fluentd.log
        ├── app.log
        └── ...
```

---

## 🔧 Troubleshooting One-Liners

### Test SSH Access
```bash
ssh nutanix@10.114.55.128
```

### Test mspctl Command
```bash
ssh nutanix@10.114.55.128 '/usr/local/nutanix/cluster/bin/mspctl cls kubeconfig nc'
```

### Check Fluentd Pod
```bash
kubectl --kubeconfig=kubeconfigs/10.114.55.128_kubeconfig_latest get pods -n ntnx-system | grep fluentd
```

### Manually Copy Logs
```bash
kubectl --kubeconfig=kubeconfigs/10.114.55.128_kubeconfig_latest cp \
  -n ntnx-system fluentd-aggregator-0:/fluentd/data/logs ./manual_logs/
```

---

## ⏰ Automation Examples

### Cron Job - Daily at 2 AM
```bash
crontab -e
# Add this line:
0 2 * * * cd /home/user/mohan_helpers && PC_PASSWORD="nutanix/4u" ./fetch_multiple_pc_logs.sh pc_list.txt >> /var/log/pc_fetch.log 2>&1
```

### Cron Job - Every 6 Hours
```bash
0 */6 * * * cd /home/user/mohan_helpers && ./fetch_pc_logs_auto.sh 10.114.55.128 >> /var/log/pc_logs.log 2>&1
```

### Systemd Timer (Alternative to Cron)
Create `/etc/systemd/system/pc-log-fetch.service`:
```ini
[Unit]
Description=PC Log Fetcher

[Service]
Type=oneshot
WorkingDirectory=/home/user/mohan_helpers
Environment="PC_PASSWORD=nutanix/4u"
ExecStart=/home/user/mohan_helpers/fetch_pc_logs_auto.sh 10.114.55.128
```

Create `/etc/systemd/system/pc-log-fetch.timer`:
```ini
[Unit]
Description=PC Log Fetch Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable --now pc-log-fetch.timer
```

---

## 🔐 Security Best Practices

### Use SSH Keys (Recommended)
```bash
# Generate key
ssh-keygen -t rsa -b 4096

# Copy to PC
ssh-copy-id nutanix@10.114.55.128

# Now you can run without password
./fetch_pc_logs.sh 10.114.55.128
```

### Secure Password Storage
```bash
# Store in encrypted file
echo "nutanix/4u" | gpg -e -r your@email.com > pc_password.gpg

# Use in script
export PC_PASSWORD=$(gpg -d pc_password.gpg)
./fetch_pc_logs_auto.sh 10.114.55.128
```

### Restrict File Permissions
```bash
chmod 600 pc_list.txt
chmod 600 kubeconfigs/*
chmod 700 fetch_*.sh
```

---

## 📊 Quick Analysis

### Count Log Files
```bash
find pc_logs -name "*.log" | wc -l
```

### Total Size of Logs
```bash
du -sh pc_logs/
```

### Latest Logs
```bash
find pc_logs -name "*.log" -mtime -1 -ls
```

### Search in Logs
```bash
grep -r "ERROR" pc_logs/*/logs/
```

### Archive Old Logs
```bash
# Archive logs older than 7 days
find pc_logs -type d -name "*_202*" -mtime +7 -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} \;
```

---

## 🆘 Quick Help

| Issue | Solution |
|-------|----------|
| Permission denied (SSH) | Check password or set up SSH keys |
| kubectl: command not found | Install kubectl |
| sshpass: command not found | Install sshpass or use manual entry |
| Pod not found | Verify pod name: `kubectl get pods -n ntnx-system` |
| Connection timeout | Check firewall and PC status |
| Kubeconfig invalid | Re-fetch kubeconfig |

---

## 📚 Full Documentation

For detailed information, see: [PC_LOG_FETCHER_README.md](PC_LOG_FETCHER_README.md)

---

## 🎯 Script Selection Guide

| Scenario | Use This Script |
|----------|-----------------|
| Test connectivity first | `test_pc_connection.sh` |
| Single PC, interactive | `fetch_pc_logs.sh` |
| Single PC, automated | `fetch_pc_logs_auto.sh` |
| Multiple PCs | `fetch_multiple_pc_logs.sh` |
| Scheduled/cron job | `fetch_pc_logs_auto.sh` or `fetch_multiple_pc_logs.sh` |

---

## 💡 Tips

1. **Always test first:** Run `test_pc_connection.sh` before fetching logs
2. **Use SSH keys:** Much more secure than passwords
3. **Archive old logs:** Set up automated cleanup
4. **Monitor disk space:** Logs can grow large
5. **Use latest symlink:** Scripts create symlinks to latest kubeconfig for easy access
6. **Check timestamps:** Output directories include timestamps for tracking
7. **Parallel processing:** Use `xargs -P` for faster batch processing
8. **Cleanup old kubeconfigs:** They contain sensitive tokens

---

## ⚡ One-Liner Examples

```bash
# Quick test all PCs in list
grep -v '^#' pc_list.txt | while read ip _; do ./test_pc_connection.sh $ip; done

# Fetch from all PCs in parallel (careful with this!)
grep -v '^#' pc_list.txt | xargs -P 3 -I {} ./fetch_pc_logs_auto.sh {}

# Clean up old logs (keep last 7 days)
find pc_logs -mtime +7 -type d -exec rm -rf {} \;

# List all collected kubeconfigs
ls -lht kubeconfigs/*_kubeconfig_* | head

# Check latest log size per PC
find pc_logs -maxdepth 1 -type d -exec du -sh {} \;
```

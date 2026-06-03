# Prism Central Log Fetcher Scripts

Automated scripts to fetch kubeconfig and fluentd logs from Nutanix Prism Central instances.

## Overview

These scripts automate the process of:
1. Fetching kubeconfig from Prism Central using `mspctl cls kubeconfig nc`
2. Copying fluentd aggregator logs from the Kubernetes pod
3. Organizing logs with timestamps and metadata

## Scripts

### 1. `fetch_pc_logs.sh` - Basic Interactive Script

Simple script that prompts for password during execution.

**Usage:**
```bash
./fetch_pc_logs.sh <pc_ip> [output_dir]
```

**Examples:**
```bash
# Basic usage (will prompt for password)
./fetch_pc_logs.sh 10.114.55.128

# With custom output directory
./fetch_pc_logs.sh 10.114.55.128 /tmp/pc_logs
```

**Features:**
- Interactive password prompt
- Color-coded output
- Automatic kubeconfig verification
- Log statistics and summary

---

### 2. `fetch_pc_logs_auto.sh` - Automated Script

Enhanced script with password automation using `sshpass` for unattended operation.

**Usage:**
```bash
./fetch_pc_logs_auto.sh <pc_ip> [password] [output_dir]
```

**Examples:**
```bash
# With password in command
./fetch_pc_logs_auto.sh 10.114.55.128 nutanix/4u

# Using environment variable
export PC_PASSWORD="nutanix/4u"
./fetch_pc_logs_auto.sh 10.114.55.128

# With custom output directory
./fetch_pc_logs_auto.sh 10.114.55.128 nutanix/4u /tmp/logs

# Custom SSH user
export PC_USER="admin"
./fetch_pc_logs_auto.sh 10.114.55.128
```

**Features:**
- Automated authentication (requires `sshpass`)
- Symlink to latest kubeconfig
- Detailed statistics
- Environment variable support
- Graceful fallback if sshpass not available

---

### 3. `fetch_multiple_pc_logs.sh` - Batch Processing Script

Process multiple Prism Central instances from a list file.

**Usage:**
```bash
./fetch_multiple_pc_logs.sh <pc_list_file>
```

**PC List File Format:**
```
# Format: <ip_address> [password] [custom_name]

10.114.55.128 nutanix/4u Production-PC
10.114.55.129 nutanix/4u Staging-PC
10.114.55.130 - Dev-PC
10.114.55.131
```

**Examples:**
```bash
# Process all PCs in list
./fetch_multiple_pc_logs.sh pc_list.txt

# With default password for all
export PC_PASSWORD="nutanix/4u"
./fetch_multiple_pc_logs.sh pc_list.txt
```

**Features:**
- Batch processing
- Per-PC custom names
- Mixed authentication (some with passwords, some without)
- Comprehensive summary report
- Individual PC success/failure tracking

---

## Requirements

### Required
- `ssh` - SSH client
- `kubectl` - Kubernetes CLI
- SSH access to Prism Central with `nutanix` user

### Optional
- `sshpass` - For automated password authentication (recommended for automation)

**Install sshpass:**
```bash
# RHEL/CentOS/Rocky
sudo yum install sshpass

# Ubuntu/Debian
sudo apt-get install sshpass

# macOS
brew install hudochenkov/sshpass/sshpass
```

---

## Output Structure

### Directory Layout
```
./kubeconfigs/
├── 10.114.55.128_kubeconfig_20260601_120000
├── 10.114.55.128_kubeconfig_latest -> 10.114.55.128_kubeconfig_20260601_120000
└── ...

./pc_logs/
├── 10.114.55.128_20260601_120000/
│   └── logs/
│       ├── fluentd.log
│       ├── app.log
│       └── ...
└── ...
```

### File Naming
- **Kubeconfig:** `<pc_ip>_kubeconfig_<timestamp>`
- **Latest Link:** `<pc_ip>_kubeconfig_latest` (symlink to most recent)
- **Logs:** `<pc_ip>_<timestamp>/logs/`

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PC_PASSWORD` | Default password for all PCs | none |
| `PC_USER` | SSH username | `nutanix` |

### Pod/Namespace Configuration

Edit these variables in the scripts if needed:

```bash
POD_NAME="fluentd-aggregator-0"
NAMESPACE="ntnx-system"
SOURCE_PATH="/fluentd/data/logs"
```

---

## Usage Examples

### Example 1: Single PC with Manual Password

```bash
./fetch_pc_logs.sh 10.114.55.128
# Will prompt for password
```

### Example 2: Single PC Automated

```bash
export PC_PASSWORD="nutanix/4u"
./fetch_pc_logs_auto.sh 10.114.55.128
```

### Example 3: Multiple PCs

Create `my_pcs.txt`:
```
10.114.55.128 nutanix/4u Prod-PC
10.114.55.129 nutanix/4u Test-PC
10.114.55.130 nutanix/4u Dev-PC
```

Run:
```bash
./fetch_multiple_pc_logs.sh my_pcs.txt
```

### Example 4: Cron Job for Daily Collection

Add to crontab:
```cron
# Fetch logs daily at 2 AM
0 2 * * * cd /home/user/mohan_helpers && PC_PASSWORD="nutanix/4u" ./fetch_multiple_pc_logs.sh pc_list.txt >> /var/log/pc_logs_$(date +\%Y\%m\%d).log 2>&1
```

---

## Troubleshooting

### SSH Connection Issues

**Problem:** `Permission denied` or connection timeout

**Solutions:**
1. Verify SSH access:
   ```bash
   ssh nutanix@10.114.55.128
   ```

2. Check SSH keys:
   ```bash
   ssh-copy-id nutanix@10.114.55.128
   ```

3. Verify firewall rules

### Kubeconfig Issues

**Problem:** `Unable to connect to the server`

**Solutions:**
1. Verify PC is running:
   ```bash
   ping 10.114.55.128
   ```

2. Check mspctl command on PC:
   ```bash
   ssh nutanix@10.114.55.128 '/usr/local/nutanix/cluster/bin/mspctl cls kubeconfig nc'
   ```

### kubectl Copy Issues

**Problem:** `pod not found` or `connection refused`

**Solutions:**
1. Verify pod is running:
   ```bash
   kubectl --kubeconfig=<kubeconfig_file> get pods -n ntnx-system
   ```

2. Check pod name matches:
   ```bash
   kubectl --kubeconfig=<kubeconfig_file> get pods -n ntnx-system | grep fluentd
   ```

3. Verify source path exists:
   ```bash
   kubectl --kubeconfig=<kubeconfig_file> exec -n ntnx-system fluentd-aggregator-0 -- ls /fluentd/data/logs
   ```

### sshpass Not Available

**Problem:** Script warns about missing sshpass

**Solutions:**
1. Install sshpass (see Requirements section)
2. Or use manual password entry (script will fallback automatically)
3. Or set up SSH key authentication

---

## Security Considerations

### Password Security

1. **Never commit passwords to git:**
   ```bash
   # Add to .gitignore
   echo "pc_list.txt" >> .gitignore
   echo "*_password*" >> .gitignore
   ```

2. **Use environment variables:**
   ```bash
   export PC_PASSWORD="nutanix/4u"
   # Clear after use
   unset PC_PASSWORD
   ```

3. **Prefer SSH keys over passwords:**
   ```bash
   ssh-copy-id nutanix@10.114.55.128
   ```

4. **Secure list files:**
   ```bash
   chmod 600 pc_list.txt
   ```

### Kubeconfig Security

Kubeconfigs contain tokens with cluster access. Protect them:

```bash
chmod 600 kubeconfigs/*
```

---

## Advanced Usage

### Custom Log Path

Modify the script to change source path:
```bash
SOURCE_PATH="/custom/path/to/logs"
```

### Different Pod/Namespace

```bash
POD_NAME="my-custom-pod-0"
NAMESPACE="my-namespace"
```

### Parallel Processing

Process multiple PCs in parallel:
```bash
cat pc_list.txt | xargs -P 5 -I {} bash -c './fetch_pc_logs_auto.sh {}'
```

### Scheduled Cleanup

Add cleanup job to remove old logs:
```bash
# Keep only last 7 days of logs
find ./pc_logs -type d -mtime +7 -exec rm -rf {} \;
find ./kubeconfigs -type f -mtime +7 -delete
```

---

## Sample Output

```
================================================================================
Prism Central Automated Log Fetcher
================================================================================
PC IP:          10.114.55.128
User:           nutanix
Password:       ***
Output Dir:     ./pc_logs
Kubeconfig Dir: ./kubeconfigs
Timestamp:      20260601_120000
Pod:            ntnx-system/fluentd-aggregator-0
Source Path:    /fluentd/data/logs

================================================================================
Step 1/3: Fetching Kubeconfig
================================================================================
ℹ Connecting to nutanix@10.114.55.128...
✓ Kubeconfig fetched successfully
ℹ Saved to: ./kubeconfigs/10.114.55.128_kubeconfig_20260601_120000
ℹ Latest link: ./kubeconfigs/10.114.55.128_kubeconfig_latest

================================================================================
Step 2/3: Verifying Kubeconfig
================================================================================
✓ Kubeconfig is valid and cluster is reachable

================================================================================
Step 3/3: Copying Fluentd Logs
================================================================================
ℹ Creating output directory: ./pc_logs/10.114.55.128_20260601_120000
ℹ Copying logs from fluentd-aggregator-0:/fluentd/data/logs...
✓ Logs copied successfully

================================================================================
Summary
================================================================================
✓ All operations completed successfully

📁 Files:
  Kubeconfig:  ./kubeconfigs/10.114.55.128_kubeconfig_20260601_120000
  Latest Link: ./kubeconfigs/10.114.55.128_kubeconfig_latest
  Logs:        ./pc_logs/10.114.55.128_20260601_120000/

📊 Statistics:
  Files:       127
  Total Size:  2.3G

📄 Latest Files:
  - fluentd.log.20260601 (456M)
  - app.log.20260601 (234M)
  - system.log.20260601 (123M)

================================================================================
✅ Done
================================================================================
```

---

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all requirements are installed
3. Test connectivity manually before running scripts
4. Check script permissions: `chmod +x *.sh`

---

## License

Internal use only - Nutanix

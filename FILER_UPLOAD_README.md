# PC Log Fetcher with Automatic Filer Upload

## Overview

Enhanced version of the PC log fetcher that automatically uploads logs to the filer server after fetching them from Prism Central. The script ensures safe operations by only deleting local logs after successful upload verification.

## New Scripts

### 1. `fetch_and_upload_pc_logs.sh` - Single PC with Upload

Fetches logs from one PC and uploads to filer.

**Usage:**
```bash
./fetch_and_upload_pc_logs.sh <pc_ip> [password] [bug_folder] [output_dir]
```

**Examples:**
```bash
# With bug folder (recommended)
./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u ENG-937578

# Without bug folder (creates temp folder)
./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u

# With environment variables
export PC_PASSWORD="nutanix/4u"
export FILER_PASSWORD="nutanix/4u"
./fetch_and_upload_pc_logs.sh 10.114.55.128 "" ENG-937578
```

---

### 2. `fetch_and_upload_multiple_pcs.sh` - Multiple PCs with Upload

Batch processes multiple PCs and uploads all to the same bug folder.

**Usage:**
```bash
./fetch_and_upload_multiple_pcs.sh <pc_list_file> <bug_folder>
```

**Examples:**
```bash
# Basic usage
./fetch_and_upload_multiple_pcs.sh pc_list.txt ENG-937578

# With environment variables
export PC_PASSWORD="nutanix/4u"
export FILER_PASSWORD="nutanix/4u"
./fetch_and_upload_multiple_pcs.sh pc_list.txt ENG-937578
```

---

## Workflow

The enhanced scripts follow this workflow:

```
1. Fetch kubeconfig from PC ✓
   ↓
2. Verify kubeconfig ✓
   ↓
3. Copy logs from fluentd pod ✓
   ↓
4. Create folder on filer ✓
   ↓
5. Upload logs to filer ✓
   ↓
6. Verify upload on filer ✓
   ↓
7. Delete local logs (only if upload verified) ✓
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PC_PASSWORD` | Password for PC SSH | none |
| `PC_USER` | PC SSH username | `nutanix` |
| `FILER_HOST` | Filer server IP | `10.46.1.165` |
| `FILER_USER` | Filer SSH username | `nutanix` |
| `FILER_PASSWORD` | Filer SSH password | none |
| `FILER_BASE_PATH` | Base path on filer | `/home/nutanix/data/bugs/MA/NCM2_1` |

### Filer Path Structure

```
/home/nutanix/data/bugs/MA/NCM2_1/
├── ENG-937578/
│   ├── 10.114.55.128_20260601_120000/
│   │   └── logs/
│   │       ├── fluentd.log
│   │       └── ...
│   └── 10.114.55.129_20260601_120000/
│       └── logs/
└── ENG-123456/
    └── ...
```

### Access URLs

After upload, logs are accessible at:
```
http://10.46.1.165/bugs/MA/NCM2_1/<bug_folder>/<pc_folder>/
```

Example:
```
http://10.46.1.165/bugs/MA/NCM2_1/ENG-937578/10.114.55.128_20260601_120000/
```

---

## Usage Examples

### Example 1: Single PC with Bug Folder

```bash
export PC_PASSWORD="nutanix/4u"
export FILER_PASSWORD="nutanix/4u"

./fetch_and_upload_pc_logs.sh 10.114.55.128 "" ENG-937578
```

**Output:**
```
================================================================================
PC Log Fetcher with Filer Upload
================================================================================
PC IP:           10.114.55.128
Bug Folder:      ENG-937578
Filer Target:    /home/nutanix/data/bugs/MA/NCM2_1/ENG-937578

✓ Kubeconfig fetched
✓ Logs copied from pod (127 files, 2.3G)
✓ Folder created on filer
✓ Logs uploaded to filer
✓ Upload verified (127 files)
✓ Local logs deleted

🌐 Access URL:
  http://10.46.1.165/bugs/MA/NCM2_1/ENG-937578/10.114.55.128_20260601_120000/
```

---

### Example 2: Multiple PCs to Same Bug Folder

Create `pc_list.txt`:
```
10.114.55.128 nutanix/4u PC1
10.114.55.129 nutanix/4u PC2
10.114.55.130 nutanix/4u PC3
```

Run:
```bash
export FILER_PASSWORD="nutanix/4u"
./fetch_and_upload_multiple_pcs.sh pc_list.txt ENG-937578
```

**Result:**
All PC logs uploaded to:
```
http://10.46.1.165/bugs/MA/NCM2_1/ENG-937578/
├── 10.114.55.128_20260601_120000/
├── 10.114.55.129_20260601_120100/
└── 10.114.55.130_20260601_120200/
```

---

### Example 3: Without Bug Folder (Auto-Generated)

```bash
./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u
```

Creates folder: `temp_10.114.55.128_20260601_120000`

---

### Example 4: Custom Filer Configuration

```bash
export PC_PASSWORD="nutanix/4u"
export FILER_HOST="10.46.1.119"
export FILER_USER="admin"
export FILER_PASSWORD="custom_password"
export FILER_BASE_PATH="/mnt/logs/NCM"

./fetch_and_upload_pc_logs.sh 10.114.55.128 "" ENG-937578
```

---

## Safety Features

### 1. Upload Verification

The script verifies upload by:
- Counting files on filer
- Checking directory size
- Only proceeding with cleanup after successful verification

### 2. Local Log Preservation

Local logs are **only deleted** after:
1. ✓ Upload completes successfully
2. ✓ Upload is verified on filer
3. ✓ File counts match

If upload fails at any step, local logs are preserved.

### 3. Error Handling

```bash
# If upload fails
✗ Upload failed
⚠ Local logs preserved at: ./pc_logs/10.114.55.128_20260601_120000

# If verification fails
✗ Upload verification failed
⚠ Local logs preserved at: ./pc_logs/10.114.55.128_20260601_120000
```

---

## Troubleshooting

### Issue: Cannot Connect to Filer

**Error:**
```
✗ Failed to create folder on filer
```

**Solutions:**
1. Verify filer is reachable:
   ```bash
   ping 10.46.1.165
   ssh nutanix@10.46.1.165
   ```

2. Check filer password:
   ```bash
   export FILER_PASSWORD="nutanix/4u"
   ```

3. Test SSH access:
   ```bash
   ssh nutanix@10.46.1.165 'pwd'
   ```

---

### Issue: Upload Fails

**Error:**
```
✗ Failed to upload logs to filer
```

**Solutions:**
1. Check disk space on filer:
   ```bash
   ssh nutanix@10.46.1.165 'df -h /home/nutanix/data'
   ```

2. Verify permissions:
   ```bash
   ssh nutanix@10.46.1.165 'ls -ld /home/nutanix/data/bugs/MA/NCM2_1'
   ```

3. Try manual SCP:
   ```bash
   scp -r ./pc_logs/10.114.55.128_*/ nutanix@10.46.1.165:/home/nutanix/data/bugs/MA/NCM2_1/test/
   ```

---

### Issue: Upload Verification Fails

**Error:**
```
✗ Upload verification failed
```

**Solutions:**
1. Check if files exist on filer:
   ```bash
   ssh nutanix@10.46.1.165 'ls -lR /home/nutanix/data/bugs/MA/NCM2_1/ENG-937578/'
   ```

2. Compare file counts:
   ```bash
   # Local
   find ./pc_logs/10.114.55.128_*/logs -type f | wc -l
   
   # Filer
   ssh nutanix@10.46.1.165 'find /home/nutanix/data/bugs/MA/NCM2_1/ENG-937578/ -type f | wc -l'
   ```

---

### Issue: Local Logs Not Deleted

If you want to manually clean up:

```bash
# Find old log directories
find ./pc_logs -type d -name "*_202*" -mtime +7

# Delete old logs (be careful!)
find ./pc_logs -type d -name "*_202*" -mtime +7 -exec rm -rf {} \;
```

---

## Manual Upload (If Script Fails)

If the automatic upload fails, you can manually upload:

### Step 1: Create Folder on Filer
```bash
ssh nutanix@10.46.1.165 'mkdir -p /home/nutanix/data/bugs/MA/NCM2_1/ENG-937578'
```

### Step 2: Upload Logs
```bash
scp -r ./pc_logs/10.114.55.128_20260601_120000 \
  nutanix@10.46.1.165:/home/nutanix/data/bugs/MA/NCM2_1/ENG-937578/
```

### Step 3: Verify
```bash
ssh nutanix@10.46.1.165 \
  'find /home/nutanix/data/bugs/MA/NCM2_1/ENG-937578/ -type f | wc -l'
```

### Step 4: Clean Up Local (Optional)
```bash
rm -rf ./pc_logs/10.114.55.128_20260601_120000
```

---

## Automation

### Cron Job Example

```bash
crontab -e

# Daily log collection and upload at 2 AM
0 2 * * * cd /home/user/mohan_helpers && \
  PC_PASSWORD="nutanix/4u" FILER_PASSWORD="nutanix/4u" \
  ./fetch_and_upload_multiple_pcs.sh pc_list.txt ENG-$(date +\%Y\%m\%d) \
  >> /var/log/pc_upload_$(date +\%Y\%m\%d).log 2>&1
```

---

## Comparison: Old vs New Workflow

### Old Workflow (Manual)
```bash
# Step 1: Fetch kubeconfig
ssh nutanix@10.114.55.128 '/usr/local/nutanix/cluster/bin/mspctl cls kubeconfig nc' > kubeconfig

# Step 2: Copy logs
kubectl --kubeconfig=kubeconfig cp -n ntnx-system fluentd-aggregator-0:/fluentd/data/logs ./flue_logs/

# Step 3: Create folder on filer
ssh nutanix@10.46.1.165 'mkdir -p /home/nutanix/data/bugs/MA/NCM2_1/ENG-937578'

# Step 4: Upload to filer
scp -r flue_logs nutanix@10.46.1.165:/home/nutanix/data/bugs/MA/NCM2_1/ENG-937578/

# Step 5: Clean up
rm -rf flue_logs
```

### New Workflow (Automated)
```bash
# One command!
./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u ENG-937578
```

---

## Best Practices

1. **Always specify bug folder:** Makes logs easier to find
   ```bash
   ./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u ENG-937578  # Good
   ./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u              # Creates temp folder
   ```

2. **Use environment variables for passwords:** Avoid passwords in command history
   ```bash
   export PC_PASSWORD="nutanix/4u"
   export FILER_PASSWORD="nutanix/4u"
   ./fetch_and_upload_pc_logs.sh 10.114.55.128 "" ENG-937578
   ```

3. **Batch similar PCs:** Process multiple PCs for same bug together
   ```bash
   ./fetch_and_upload_multiple_pcs.sh pc_list.txt ENG-937578
   ```

4. **Monitor disk space:** Check filer space regularly
   ```bash
   ssh nutanix@10.46.1.165 'df -h /home/nutanix/data'
   ```

5. **Document in bug tracker:** Add filer URL to bug description
   ```
   Logs: http://10.46.1.165/bugs/MA/NCM2_1/ENG-937578/
   ```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Single PC | `./fetch_and_upload_pc_logs.sh <ip> <pass> <bug>` |
| Multiple PCs | `./fetch_and_upload_multiple_pcs.sh list.txt <bug>` |
| Custom filer | `FILER_HOST=<ip> ./fetch_and_upload_pc_logs.sh ...` |
| Check filer | `ssh nutanix@10.46.1.165 'ls -lh /home/nutanix/data/bugs/MA/NCM2_1/<bug>/'` |
| Manual upload | `scp -r logs/ nutanix@10.46.1.165:/home/nutanix/data/bugs/MA/NCM2_1/<bug>/` |
| Access logs | `http://10.46.1.165/bugs/MA/NCM2_1/<bug>/` |

---

## Support

For issues:
1. Check network connectivity to both PC and filer
2. Verify passwords are correct
3. Ensure sufficient disk space on filer
4. Try manual upload to isolate the issue
5. Check PC_LOG_FETCHER_README.md for general troubleshooting

---

## Migration from Old Scripts

If you were using the old scripts:

**Old:**
```bash
./fetch_pc_logs_auto.sh 10.114.55.128 nutanix/4u
# Then manually upload...
```

**New:**
```bash
./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u ENG-937578
# Upload happens automatically!
```

All old scripts still work if you don't need automatic upload.

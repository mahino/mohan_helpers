# Quick Start - PC Logs with Filer Upload

## 🚀 Quick Commands

### Single PC
```bash
# Set passwords once
export PC_PASSWORD="nutanix/4u"
export FILER_PASSWORD="nutanix/4u"

# Fetch and upload
./fetch_and_upload_pc_logs.sh 10.114.55.128 "" ENG-937578
```

### Multiple PCs
```bash
# Create PC list
cat > pc_list.txt << EOF
10.114.55.128 nutanix/4u PC1
10.114.55.129 nutanix/4u PC2
10.114.55.130 nutanix/4u PC3
EOF

# Set filer password
export FILER_PASSWORD="nutanix/4u"

# Fetch and upload all
./fetch_and_upload_multiple_pcs.sh pc_list.txt ENG-937578
```

---

## 📋 What Happens

1. ✅ Fetches kubeconfig from PC
2. ✅ Copies logs from fluentd pod
3. ✅ Creates folder on filer: `/home/nutanix/data/bugs/MA/NCM2_1/ENG-937578/`
4. ✅ Uploads logs to filer
5. ✅ Verifies upload succeeded
6. ✅ Deletes local logs (only if upload OK)

---

## 🌐 Access Your Logs

After upload completes:
```
http://10.46.1.165/bugs/MA/NCM2_1/ENG-937578/
```

---

## ⚙️ Configuration

### Required Variables
```bash
export PC_PASSWORD="nutanix/4u"      # PC SSH password
export FILER_PASSWORD="nutanix/4u"   # Filer SSH password
```

### Optional Variables
```bash
export FILER_HOST="10.46.1.165"                                # Filer IP
export FILER_USER="nutanix"                                    # Filer user
export FILER_BASE_PATH="/home/nutanix/data/bugs/MA/NCM2_1"    # Base path
```

---

## 🔧 Troubleshooting

### Can't connect to PC
```bash
ssh nutanix@10.114.55.128
```

### Can't connect to filer
```bash
ssh nutanix@10.46.1.165
```

### Check filer space
```bash
ssh nutanix@10.46.1.165 'df -h /home/nutanix/data'
```

### Manual upload
```bash
scp -r ./pc_logs/10.114.55.128_*/ nutanix@10.46.1.165:/home/nutanix/data/bugs/MA/NCM2_1/ENG-937578/
```

---

## 📊 Example Output

```
================================================================================
Step 1/6: Fetching Kubeconfig
✓ Kubeconfig fetched successfully

Step 2/6: Verifying Kubeconfig
✓ Kubeconfig is valid

Step 3/6: Copying Fluentd Logs from Pod
✓ Logs copied successfully
ℹ Local logs: 127 files, 2.3G

Step 4/6: Creating Folder on Filer
✓ Folder created on filer

Step 5/6: Uploading Logs to Filer
✓ Upload completed

Step 6/6: Verification and Cleanup
✓ Upload verified (127 files)
✓ Local logs deleted

🌐 Access URL:
  http://10.46.1.165/bugs/MA/NCM2_1/ENG-937578/10.114.55.128_20260601_120000/
```

---

## ⚡ One-Liners

### Single PC - Everything
```bash
PC_PASSWORD="nutanix/4u" FILER_PASSWORD="nutanix/4u" ./fetch_and_upload_pc_logs.sh 10.114.55.128 "" ENG-937578
```

### Multiple PCs - Auto temp folder
```bash
PC_PASSWORD="nutanix/4u" FILER_PASSWORD="nutanix/4u" ./fetch_and_upload_multiple_pcs.sh pc_list.txt "temp_$(date +%Y%m%d_%H%M%S)"
```

### With custom filer
```bash
FILER_HOST="10.46.1.119" FILER_PASSWORD="pass" ./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u ENG-937578
```

---

## 🎯 Common Workflows

### Daily Bug Log Collection
```bash
#!/bin/bash
export PC_PASSWORD="nutanix/4u"
export FILER_PASSWORD="nutanix/4u"

BUG_ID="ENG-937578"
./fetch_and_upload_multiple_pcs.sh prod_pcs.txt "$BUG_ID"
```

### Emergency Log Grab
```bash
#!/bin/bash
PC_IP="10.114.55.128"
BUG_ID="ENG-$(date +%Y%m%d)"

PC_PASSWORD="nutanix/4u" FILER_PASSWORD="nutanix/4u" \
  ./fetch_and_upload_pc_logs.sh "$PC_IP" "" "$BUG_ID"

echo "Logs at: http://10.46.1.165/bugs/MA/NCM2_1/$BUG_ID/"
```

---

## 📚 Full Documentation

- **Complete Guide:** [FILER_UPLOAD_README.md](FILER_UPLOAD_README.md)
- **General Usage:** [PC_LOG_FETCHER_README.md](PC_LOG_FETCHER_README.md)
- **Quick Reference:** [QUICK_START.md](QUICK_START.md)

---

## 💡 Tips

1. **Always specify bug folder** - makes logs easy to find
2. **Use environment variables** - keeps passwords out of history
3. **Batch similar PCs** - upload multiple PCs to same bug folder
4. **Verify upload** - script automatically verifies before cleanup
5. **Safe by default** - local logs preserved if upload fails

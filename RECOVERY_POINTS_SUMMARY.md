# Recovery Points Management - Complete Solution

## Overview

This document provides a complete overview of the recovery points management tools for Nutanix Prism Central.

## Available Scripts

### 1. Analyze Recovery Points (`analyze_recovery_points.py`)

**Purpose**: Analyze VMs and calculate reclaimable space from recovery points

**Key Features**:
- Lists all VMs with recovery points
- Calculates reclaimable space per VM
- Provides cluster-level summary
- Supports JSON export

**Usage**:
```bash
cd /home/mohan.as1/mohan_helpers
python3 analyze_recovery_points.py
```

**API Used**:
- v3 Groups API: `/api/nutanix/v3/groups` (list VMs)
- v4 Recovery Points API: `/api/dataprotection/v4.3/config/recovery-points` (get details)

---

### 2. Delete Recovery Points (`delete_recovery_points.py`) ⭐ NEW

**Purpose**: Delete recovery points for one or more VMs

**Key Features**:
- Interactive mode to select VMs
- Bulk deletion support
- Real-time task monitoring
- Safety confirmations
- Comprehensive logging

**Usage**:

**Interactive mode** (safest):
```bash
cd /home/mohan.as1/mohan_helpers
python3 delete_recovery_points.py
```

**Delete all** (with confirmation):
```bash
python3 delete_recovery_points.py --all
```

**Delete specific VM**:
```bash
python3 delete_recovery_points.py --vm-name "my-vm-01"
python3 delete_recovery_points.py --vm-uuid "12345678-1234-1234-1234-123456789abc"
```

**API Used**:
- v3 Groups API: `/api/nutanix/v3/groups` (list VMs)
- v3 VMs API: `/api/nutanix/v3/vms/{uuid}` (get VM details)
- v4 Protected Resources API: `/api/dataprotection/v4.3/config/protected-resources/{extId}/$actions/force-delete-all-recovery-points` (delete)
- v3 Tasks API: `/api/nutanix/v3/tasks/{task_id}` (monitor status)

---

## UI Integration (Bulk Snapshots UI)

### Currently Integrated:

✅ **Recovery Points Analysis** (`/recovery_points`)
- Analyze VMs with recovery points
- Show detailed statistics
- Display reclaimable space
- Cache results for performance
- Pagination (20 VMs per page)
- VM-level actions (Snapshot, Disk Update)

### Available for Integration:

🔄 **Recovery Points Deletion**

Can be added to the UI with:
- Delete button for each VM in the table
- Bulk delete checkbox selection
- Confirmation modal
- Live progress tracking (SSE)
- Task status monitoring

---

## Typical Workflow

### Analysis → Decision → Action

```
1. ANALYZE
   └─ Run analyze_recovery_points.py
      └─ Or use UI: http://10.46.117.165:5005/recovery_points
         └─ View VMs with recovery points
         └─ See reclaimable space
         └─ Identify VMs to clean up

2. DECIDE
   └─ Review the list
   └─ Identify VMs with excessive recovery points
   └─ Check business requirements
   └─ Get approval if needed

3. DELETE
   └─ Run delete_recovery_points.py
      └─ Interactive mode: Select specific VMs
      └─ Or bulk mode: Delete all
      └─ Confirm deletion
      └─ Monitor progress

4. VERIFY
   └─ Re-run analysis to confirm deletion
   └─ Check reclaimable space reduced
   └─ Verify VMs still operational
```

---

## API Reference

### Nutanix v3 APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/nutanix/v3/groups` | POST | List VMs with recovery points |
| `/api/nutanix/v3/vms/{uuid}` | GET | Get VM details |
| `/api/nutanix/v3/vms/{uuid}/snapshot` | POST | Create snapshot |
| `/api/nutanix/v3/tasks/{task_id}` | GET | Monitor task status |

### Nutanix v4 APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/dataprotection/v4.3/config/recovery-points` | GET | List recovery points for a VM |
| `/api/dataprotection/v4.3/config/protected-resources/{extId}/$actions/force-delete-all-recovery-points` | POST | Delete all recovery points for a VM |

---

## Configuration

All scripts use these default settings:

```python
PRISM_IP = "10.114.55.128"
PRISM_PORT = "9440"
USERNAME = "admin"
PASSWORD = "Nutanix.123"
```

Override via command-line:
```bash
python3 script.py --pc-ip 10.46.117.165 --username myuser --password mypass
```

---

## Files Location

```
/home/mohan.as1/mohan_helpers/
├── analyze_recovery_points.py          # Analysis script
├── delete_recovery_points.py           # Deletion script (NEW)
├── DELETE_RECOVERY_POINTS.md           # Detailed deletion guide
└── bulk_snapshots_ui/                  # Web UI
    ├── app.py                          # Flask application
    ├── recovery_points_analyzer.py     # Analysis module
    ├── templates/
    │   ├── index.html                  # Main page
    │   └── recovery_points.html        # Analysis page
    └── data/
        └── recovery_points_cache/      # Cached results
```

---

## Safety Warnings ⚠️

### For Delete Operations:

1. **DESTRUCTIVE**: Deletion is permanent and irreversible
2. **NO UNDO**: Recovery points cannot be restored once deleted
3. **PRODUCTION**: Always test in non-production first
4. **BACKUPS**: Ensure alternative backups exist
5. **APPROVAL**: Get proper authorization before mass deletion
6. **VERIFICATION**: Always analyze before deleting

### Best Practices:

- ✅ Run analysis first to understand impact
- ✅ Use interactive mode for first-time use
- ✅ Test with a single VM before bulk operations
- ✅ Verify VMs are still operational after deletion
- ✅ Keep audit logs of deletion operations
- ❌ Never use `--yes` flag in production without verification
- ❌ Don't delete during business-critical hours
- ❌ Avoid deleting all recovery points unless necessary

---

## Comparison: Analysis vs Deletion

| Feature | Analyze | Delete |
|---------|---------|--------|
| **Read-only** | ✅ Yes | ❌ No (destructive) |
| **Safety** | ✅ Safe | ⚠️ Requires confirmation |
| **Speed** | Fast (read-only) | Slower (tasks + polling) |
| **Reversible** | N/A | ❌ No |
| **UI Integration** | ✅ Integrated | 🔄 Available |
| **Concurrency** | ✅ Yes (5 workers) | Sequential (safer) |
| **Caching** | ✅ Yes | No (always live) |

---

## Future Enhancements

### Planned Features:

1. **Selective Deletion**: Delete specific recovery points (not all)
2. **Retention Policy**: Keep N most recent recovery points
3. **Age-Based Deletion**: Delete recovery points older than X days
4. **Dry Run Mode**: Preview what would be deleted
5. **UI Integration**: Add delete functionality to web UI
6. **Parallel Processing**: Process multiple VMs concurrently
7. **Rollback**: Create new recovery point before deletion
8. **Scheduling**: Automated cleanup based on policies

---

## Troubleshooting

### Common Issues:

**Issue**: "No VMs with recovery points found"
- **Solution**: Run analysis script first, check PC connectivity

**Issue**: "Failed to delete recovery points (status 404)"
- **Solution**: VM may have been deleted or moved

**Issue**: "Task timeout after 600s"
- **Solution**: Increase timeout or check cluster health

**Issue**: "Failed to fetch VM extId"
- **Solution**: Verify VM exists and is accessible

---

## Support & Documentation

- **Analysis Documentation**: See `analyze_recovery_points.py` docstring
- **Deletion Documentation**: See `DELETE_RECOVERY_POINTS.md`
- **UI Documentation**: See `bulk_snapshots_ui/VM_ACTIONS_IMPLEMENTATION.md`
- **Main Page Analysis**: See `bulk_snapshots_ui/MAIN_PAGE_ANALYSIS.md`

---

## Quick Reference

### Get Help:
```bash
python3 analyze_recovery_points.py --help
python3 delete_recovery_points.py --help
```

### View Logs:
```bash
cd /home/mohan.as1/mohan_helpers/bulk_snapshots_ui
./view_log.sh follow      # Follow live logs
./view_log.sh errors      # Show errors only
./view_log.sh search "VM" # Search logs
```

### Access UI:
```
http://10.46.117.165:5005/              # Main page
http://10.46.117.165:5005/recovery_points  # Analysis page
```

### Restart Service:
```bash
cd /home/mohan.as1/mohan_helpers/bulk_snapshots_ui
./service-manager.sh restart
```

---

## Version History

- **v1.0** (Initial): Analysis script created
- **v1.1** (UI Integration): Added web UI for analysis
- **v1.2** (VM Actions): Added snapshot and disk update per VM
- **v1.3** (Pagination): Added pagination to results
- **v2.0** (Deletion): Added recovery points deletion script ⭐ NEW

---

## License

Internal Nutanix tool - Not for external distribution

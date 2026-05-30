# Delete Recovery Points Script

## Overview

The `delete_recovery_points.py` script provides functionality to delete VM recovery points (snapshots) in Nutanix Prism Central using the v4 Data Protection API.

## Features

- **Interactive Mode**: Select specific VMs from a list
- **Bulk Deletion**: Delete recovery points for all VMs at once
- **Selective Deletion**: Target specific VMs by name or UUID
- **Task Monitoring**: Real-time progress tracking with task polling
- **Safety Confirmations**: Built-in prompts to prevent accidental deletions
- **Comprehensive Logging**: Detailed timestamped logs with emoji indicators

## API Details

### Nutanix API Endpoint

The script uses the Nutanix v4 Data Protection API:

```
POST /api/dataprotection/v4.3/config/protected-resources/{vm_ext_id}/$actions/force-delete-all-recovery-points
```

**Required Headers:**
- `Authorization`: Basic auth (base64 encoded username:password)
- `Content-Type`: application/json
- `Accept`: application/json
- `NTNX-Request-Id`: UUID (for idempotency)

**Payload:**
```json
{}
```

**Response:**
Returns a task object with `extId` that can be polled for status.

### Task Monitoring

Tasks are monitored using the v3 Tasks API:

```
GET /api/nutanix/v3/tasks/{task_id}
```

Status values:
- `SUCCEEDED`: Deletion completed successfully
- `FAILED`: Deletion failed
- `RUNNING`, `QUEUED`, `PENDING`: In progress

## Usage

### Interactive Mode (Recommended for First-Time Use)

```bash
cd /home/mohan.as1/mohan_helpers
python3 delete_recovery_points.py
```

This will:
1. Fetch all VMs with recovery points
2. Display a numbered list
3. Prompt you to select VMs (by number, range, or 'all')
4. Ask for confirmation before deletion
5. Monitor task completion

### Delete All Recovery Points (With Confirmation)

```bash
python3 delete_recovery_points.py --all
```

### Delete for Specific VM by Name

```bash
python3 delete_recovery_points.py --vm-name "my-test-vm"
```

### Delete for Specific VM by UUID

```bash
python3 delete_recovery_points.py --vm-uuid "12345678-1234-1234-1234-123456789abc"
```

### Non-Interactive Mode (Skip Confirmation)

**⚠️ USE WITH EXTREME CAUTION!**

```bash
python3 delete_recovery_points.py --all --yes
```

### Custom Prism Central

```bash
python3 delete_recovery_points.py \
  --pc-ip 10.114.55.128 \
  --username admin \
  --password "Nutanix.123" \
  --all
```

## Configuration

Edit these variables at the top of the script:

```python
PRISM_IP = "10.114.55.128"
PRISM_PORT = "9440"
USERNAME = "admin"
PASSWORD = "Nutanix.123"
```

Or use command-line arguments to override.

## Task Polling Settings

```python
TASK_POLL_INTERVAL = 5  # seconds between status checks
TASK_TIMEOUT = 600      # maximum wait time (10 minutes)
```

## Example Output

```
[2026-05-30 11:30:45] ℹ️ Fetching VMs with recovery points...
[2026-05-30 11:30:46] ⚡ 📥 Fetched 60 VMs (offset: 0)
[2026-05-30 11:30:47] ✅ ✅ Found 150 VMs with recovery points

================================================================================
BULK DELETION STARTED
================================================================================
Total VMs to process: 150

⚠️  WARNING: This will delete ALL recovery points for 150 VMs!

Do you want to continue? (yes/no): yes

[1/150] ⚡ Processing: ahv_ins_delete-0
   🔍 UUID: 64b1c2c5-fe9c-4465-55ae-c7f19eca291f
   🔍 Recovery Points: 45
   🗑️  Deleting recovery points for VM: ahv_ins_delete-0
   ✅ Delete initiated for ahv_ins_delete-0, Task ID: 4d120b11-619f-404f-b36a-229487066885
   🔄 Polling task 4d120b11-619f-404f-b36a-229487066885 for VM: ahv_ins_delete-0
   🔍 Task status: RUNNING, Progress: 50%
   🔍 Task status: SUCCEEDED, Progress: 100%
   ✅ Task completed successfully for ahv_ins_delete-0

[2/150] ⚡ Processing: my-test-vm-02
...

================================================================================
DELETION COMPLETE
================================================================================
Total VMs Processed: 150
✅ Successful: 148
❌ Failed: 1
⚠️  Skipped: 1
ℹ️ Duration: 450.23 seconds
================================================================================
```

## Error Handling

The script handles:
- **API failures**: Logs detailed error messages
- **Task failures**: Reports task failure reasons
- **Timeouts**: Warns when tasks exceed timeout
- **Missing VMs**: Skips VMs that can't be found
- **Network errors**: Retries task polling on connection issues

## Integration with Bulk Snapshots UI

This script can be integrated into the Flask UI at `/home/mohan.as1/mohan_helpers/bulk_snapshots_ui/` similar to how `analyze_recovery_points.py` was integrated.

### UI Integration Points:

1. **New Route**: `/delete_recovery_points`
2. **API Endpoint**: `/api/delete_recovery_points` (POST with SSE)
3. **Frontend**: Add delete button to recovery points table
4. **Features**:
   - Select VMs from the table
   - Confirm deletion with modal
   - Live progress with Server-Sent Events
   - Task status monitoring

## Safety Considerations

1. **⚠️ DESTRUCTIVE OPERATION**: This script permanently deletes recovery points
2. **No Undo**: Deleted recovery points cannot be restored
3. **Production Use**: Always test in non-production environment first
4. **Backup**: Ensure you have alternative backups before mass deletion
5. **Confirmation**: Never use `--yes` flag unless you're absolutely certain
6. **Review**: Always review the VM list before confirming deletion

## Troubleshooting

### Issue: "Failed to delete recovery points (status 404)"

**Cause**: VM extId not found in v4 API

**Solution**: Verify VM exists and has data protection enabled

### Issue: "Task timeout after 600s"

**Cause**: Deletion taking longer than expected

**Solution**: 
- Increase `TASK_TIMEOUT` value
- Check Prism Central logs
- Verify cluster health

### Issue: "Failed to fetch VM extId"

**Cause**: VM not accessible via v3 API

**Solution**: Check VM UUID is correct and VM still exists

### Issue: "No VMs with recovery points found"

**Cause**: No VMs have snapshots or query failed

**Solution**:
- Run `analyze_recovery_points.py` first to verify
- Check Prism Central connectivity
- Verify authentication credentials

## Related Scripts

- **analyze_recovery_points.py**: Analyze and list VMs with recovery points
- **bulk_snapshots_ui**: Web UI for bulk snapshot operations

## Technical Notes

### VM Identification

The script uses two ID formats:
1. **v3 UUID**: Used for groups API and VM details (`vm_uuid`)
2. **v4 extId**: Required for data protection API operations

The script automatically converts between these formats.

### API Version Differences

- **v3 API**: Used for querying VMs and tasks
- **v4 API**: Used for data protection operations (delete recovery points)

### Concurrency

Current implementation processes VMs sequentially to:
- Better monitor task status
- Avoid overwhelming Prism Central
- Provide clear progress indication

Future enhancement: Add parallel processing with worker pools.

## License

Internal Nutanix tool - Not for external distribution

## Support

For issues or questions:
1. Check Prism Central logs
2. Review application logs
3. Contact internal support team

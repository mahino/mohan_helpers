# HAR File Analysis: VM Memory Resize Operations

## Source File
`10.46.117.165.har` - Network traffic capture from Nutanix Prism UI

## Analysis Date
2026-05-28

## VM Under Test
- **Name**: ahv_ins_delete-0-260519-032946
- **UUID**: 1145a8a7-7f5c-430c-4c71-f47c91f517df
- **VM ID**: 00065035-b0c9-5144-07ad-7cc255864212::1145a8a7-7f5c-430c-4c71-f47c91f517df
- **Cluster**: SSCG_NCM_2_1_Small_PE1 (10.46.117.165)

---

## Key API Endpoints Identified

### 1. List VMs (v1 API)
**Request**:
```
GET https://10.46.117.165:9440/PrismGateway/services/rest/v1/vms
```

**Query Parameters**:
- `count=50` - Number of VMs per page
- `page=1` - Page number
- `sortCriteria=-hypervisor_cpu_usage_ppm` - Sort by CPU usage (descending)
- `searchAttributeList=vm_uuid` - Search in VM UUID field
- `projection=stats,basicInfo,alerts` - Include stats, basic info, and alerts
- `filterCriteria=is_control_domain!=1;is_cvm==0` - Exclude control domains and CVMs
- `_=<timestamp>` - Cache buster

**Response Fields** (per VM):
```json
{
  "vmId": "00065035-b0c9-5144-07ad-7cc255864212::1145a8a7-7f5c-430c-4c71-f47c91f517df",
  "uuid": "1145a8a7-7f5c-430c-4c71-f47c91f517df",
  "powerState": "on",
  "vmName": "ahv_ins_delete-0-260519-032946",
  "ipAddresses": ["10.114.113.24"],
  "hypervisorType": "kKvm",
  "hostName": "lumiya03-1"
}
```

---

### 2. Get VM Details (v2 API)
**Request**:
```
GET https://10.46.117.165:9440/PrismGateway/services/rest/v2.0/vms/1145a8a7-7f5c-430c-4c71-f47c91f517df
```

**Query Parameters**:
- `include_vm_disk_config=true` - Include disk configuration
- `include_vm_nic_config=true` - Include NIC configuration
- `__=<timestamp>` - Cache buster

**Response Fields**:
```json
{
  "allow_live_migrate": true,
  "gpus_assigned": false,
  "boot": {
    "disk_address": {
      "device_bus": "scsi",
      "device_index": 0
    },
    "boot_device_type": "disk",
    "uefi_boot": false,
    "secure_boot": false
  },
  "ha_priority": 0,
  "host_uuid": "32a28f85-647d-45fa-9aa3-8f36b531533a",
  "memory_mb": 256,
  "name": "ahv_ins_delete-0-260519-032946",
  "num_cores_per_vcpu": 1,
  "num_vcpus": 1,
  "power_state": "on",
  "timezone": "UTC",
  "uuid": "1145a8a7-7f5c-430c-4c71-f47c91f517df",
  "vm_disk_info": [...],
  "vm_features": {
    "AGENT_VM": false,
    "VGA_CONSOLE": true
  },
  "vm_nics": [...],
  "machine_type": "pc"
}
```

---

### 3. Power Off VM (v2 API)
**Request**:
```
POST https://10.46.117.165:9440/PrismGateway/services/rest/v2.0/vms/1145a8a7-7f5c-430c-4c71-f47c91f517df/set_power_state
```

**Request Payload**:
```json
{
  "transition": "off"
}
```

**Response**:
```json
{
  "task_uuid": "36140bca-d983-4df5-8f5f-e50aabd95f6a"
}
```

---

### 4. Power On VM (v2 API)
**Request**:
```
POST https://10.46.117.165:9440/PrismGateway/services/rest/v2.0/vms/1145a8a7-7f5c-430c-4c71-f47c91f517df/set_power_state
```

**Request Payload**:
```json
{
  "transition": "on"
}
```

**Response**:
```json
{
  "task_uuid": "<task_uuid>"
}
```

---

### 5. Update VM Memory (v2 API)
**Request**:
```
PUT https://10.46.117.165:9440/PrismGateway/services/rest/v2.0/vms/1145a8a7-7f5c-430c-4c71-f47c91f517df
```

**Query Parameters**:
- `include_vm_disk_config=true`
- `include_vm_nic_config=true`
- `includeVMDiskSizes=true`
- `includeAddressAssignments=true`

**Request Payload** (Minimal example for memory update):
```json
{
  "name": "ahv_ins_delete-0-260519-032946",
  "memory_mb": 10496,
  "num_vcpus": 1,
  "description": "",
  "num_cores_per_vcpu": 1,
  "timezone": "UTC",
  "boot": {
    "uefi_boot": false,
    "boot_device_type": "DISK",
    "disk_address": {
      "device_bus": "scsi",
      "device_index": 0,
      "disk_label": "scsi.0",
      "is_cdrom": false,
      "vmdisk_uuid": "91185d5a-ff90-4f95-79f4-07fe50a8f66d"
    }
  },
  "machine_type": "PC",
  "vm_features": {
    "FLASH_MODE": false,
    "AGENT_VM": false
  }
}
```

**Key Observation**: Memory values observed in HAR:
- Initial memory: `256 MB` (256MB)
- Updated to: `10496 MB` (~10.25 GB)
- This represents a memory resize operation from 256MB to ~10GB

**Response**:
```json
{
  "task_uuid": "<task_uuid>"
}
```

---

### 6. Check Task Status (v1 API)
**Request**:
```
GET https://10.46.117.165:9440/PrismGateway/services/rest/v1/progress_monitors
```

**Query Parameters**:
- `filterCriteria=uuid==36140bca-d983-4df5-8f5f-e50aabd95f6a` - Filter by task UUID

**Response**:
```json
{
  "metadata": {
    "grandTotalEntities": 1,
    "totalEntities": 1,
    "filterCriteria": "uuid==36140bca-d983-4df5-8f5f-e50aabd95f6a"
  },
  "entities": [
    {
      "operation": "VmChangePowerState",
      "entity": ["vm"],
      "entityId": ["1145a8a7-7f5c-430c-4c71-f47c91f517df"],
      "component": "Uhura",
      "id": "36140bca-d983-4df5-8f5f-e50aabd95f6a",
      "clusterUuid": "00065035-b0c9-5144-07ad-7cc255864212",
      "taskName": "",
      "taskDisplayName": "Power off the VM",
      "subTaskMessage": "",
      "status": "running",
      "percentageCompleted": 1,
      "createTimeUsecs": 1779988504500083,
      "startTimeUsecs": 1779988504507009,
      "lastUpdateTimeUsecs": 1779988504530629
    }
  ]
}
```

**Task Status Values**:
- `running` - Task in progress
- `succeeded` - Task completed successfully
- `failed` - Task failed
- `aborted` - Task was aborted

---

### 7. Get VM CPU Statistics (v1 API)
**Request**:
```
GET https://10.46.117.165:9440/PrismGateway/services/rest/v1/vms/00065035-b0c9-5144-07ad-7cc255864212::1145a8a7-7f5c-430c-4c71-f47c91f517df/stats
```

**Query Parameters**:
- `metrics=hypervisor_cpu_usage_ppm,memory_usage_ppm,controller_num_iops,controller_io_bandwidth_kBps,controller_avg_io_latency_usecs`
- `startTimeInUsecs=1779977700268000` - Start time in microseconds
- `endTimeInUsecs=1779988500268000` - End time in microseconds
- `intervalInSecs=60` - Data point interval (60 seconds)
- `__=<timestamp>` - Cache buster

**Response**:
```json
{
  "statsSpecificResponses": [
    {
      "successful": true,
      "message": null,
      "startTimeInUsecs": 1779977700000000,
      "intervalInSecs": 60,
      "metric": "hypervisor_cpu_usage_ppm",
      "values": [0, 0, ..., 998304, 998996, 999303, ...]
    },
    {
      "metric": "memory_usage_ppm",
      "values": [...]
    }
  ]
}
```

**CPU Usage Notes**:
- Values are in **parts per million (ppm)**
- 1,000,000 ppm = 100% CPU usage
- 100,000 ppm = 10% CPU usage
- 0 ppm = 0% CPU usage

---

## Observed Operation Sequence in HAR

The HAR file captured the following sequence:

1. **VM Search/List** - User searched for VM "ahv_ins_delete-0-260519-032946"
2. **VM Details Fetch** - UI loaded full VM configuration (showing 256MB memory)
3. **Power Off Initiated** - User clicked power off button
4. **Task Monitoring** - UI polled task status until power off completed
5. **VM Config Update** - User updated memory from 256MB to 10496MB (~10GB)
6. **Power On Initiated** - User powered VM back on
7. **CPU Stats Monitoring** - UI continuously fetched CPU/memory stats
8. **Subsequent Operations** - Additional power state changes observed

---

## Script Implementation Notes

### Memory Values Used in Script
- **10GB**: `10240 MB` (10 * 1024 MB)
- **256MB**: `256 MB`

### Task Waiting Strategy
1. Submit operation (returns `task_uuid`)
2. Poll `/progress_monitors` with `filterCriteria=uuid=={task_uuid}`
3. Check `status` field until it's `succeeded`, `failed`, or timeout
4. Use 5-second intervals between checks

### CPU Monitoring Strategy
1. Fetch stats with `metrics=hypervisor_cpu_usage_ppm`
2. Get last 5 minutes of data with 60-second intervals
3. Extract most recent non-zero value from `values` array
4. Compare against threshold (100,000 ppm = 10%)
5. Use 10-second intervals between checks

---

## API Version Summary

### v1 APIs (Legacy, but still functional)
- VM listing
- Task status monitoring
- VM statistics (CPU, memory, I/O)

### v2 APIs (Current standard for PE operations)
- VM power state changes
- VM configuration updates
- VM details retrieval

**Note**: v3 and v4 APIs are available for Prism Central operations but were not used in this HAR capture as it was from a Prism Element (PE) cluster.

---

## Security Considerations

- All requests use HTTPS
- Basic authentication with username/password
- SSL certificate verification should be enabled in production
- Credentials should be stored securely (not hardcoded)

---

## Related Documentation

- Nutanix Prism Element API v1: Legacy REST API
- Nutanix Prism Element API v2: Current REST API
- VM Power State Transitions: off → on → off
- VM Memory Resize: Requires VM to be powered off

---

## Summary

The HAR file analysis revealed a complete workflow for:
1. Listing and searching VMs
2. Power state management (on/off)
3. VM configuration updates (memory resize)
4. Task status monitoring
5. VM statistics monitoring (CPU, memory)

All APIs identified were from Prism Element (PE) v1 and v2 endpoints, consistent with the cluster IP being a PE cluster (10.46.117.165) rather than Prism Central.

The script `vm_memory_resize_test.py` implements this workflow using the identified APIs to automate the test sequence requested by the user.

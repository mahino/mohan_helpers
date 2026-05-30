# VM Memory Resize Test Script

## Overview

This script performs an automated test sequence on **ALL VMs** in the cluster to validate memory resize operations. It cycles through power states and memory configurations to test each VM's behavior under different memory settings.

## Test Sequence

The script executes the following sequence for **each VM** in the cluster:

1. **Get VM List** - Fetches list of ALL VMs from the cluster (all pages)
2. **Power Off VM** - Powers off the VM if it's running (waits for completion)
3. **Update Memory to 10GB** - Resizes VM memory to 10GB (waits for completion)
4. **Power On VM** - Powers the VM back on (waits for completion)
5. **Wait for Low CPU** - Monitors CPU usage until it drops below 10%
6. **Sleep 5 seconds** - Waits for 5 seconds
7. **Power Off VM** - Powers off the VM again (waits for completion)
8. **Update Memory to 256MB** - Resizes VM memory to 256MB (waits for completion)
9. **Power On VM** - Powers the VM back on (waits for completion)

The script processes VMs sequentially, one at a time, with a 10-second delay between VMs.

## Prerequisites

- Python 3.6 or higher
- `requests` library: `pip3 install requests`
- Network access to Nutanix Prism Central
- Valid credentials with permissions to:
  - List VMs
  - Power on/off VMs
  - Update VM configuration
  - Read VM statistics

## Configuration

Edit the following variables in the script:

```python
PRISM_IP = "10.46.117.165"       # Prism Central IP
PRISM_PORT = "9440"               # Prism Central port
USERNAME = "admin"                # Prism Central username
PASSWORD = "Nutanix.123"          # Prism Central password

CHECK_INTERVAL = 5                # Seconds between task status checks
MAX_RETRIES = 60                  # Max task status checks (5 minutes)
CPU_CHECK_INTERVAL = 10           # Seconds between CPU checks
MAX_CPU_RETRIES = 60              # Max CPU checks (10 minutes)
CPU_THRESHOLD_PPM = 100000        # 10% CPU threshold (in parts per million)
```

## Usage

### Basic Execution

```bash
# Make the script executable
chmod +x vm_memory_resize_test.py

# Run the script
./vm_memory_resize_test.py

# Or run with python3
python3 vm_memory_resize_test.py
```

### Sample Output

```
[2026-05-28 22:45:00] [INFO] ================================================================================
[2026-05-28 22:45:00] [INFO] VM MEMORY RESIZE TEST SCRIPT - ALL VMS
[2026-05-28 22:45:00] [INFO] ================================================================================
[2026-05-28 22:45:00] [INFO] Prism Central: 10.46.117.165
[2026-05-28 22:45:00] [INFO] Check Interval: 5s
[2026-05-28 22:45:00] [INFO] Max Retries: 60
[2026-05-28 22:45:00] [INFO] CPU Check Interval: 10s
[2026-05-28 22:45:00] [INFO] CPU Threshold: 10.0%
[2026-05-28 22:45:00] [INFO] ================================================================================

[2026-05-28 22:45:00] [INFO] STEP 1: Getting all VMs from cluster...
[2026-05-28 22:45:00] [INFO] --------------------------------------------------------------------------------
[2026-05-28 22:45:00] [INFO] Fetching VM list (page 1)...
[2026-05-28 22:45:01] [INFO] Found 50 VMs in page 1
[2026-05-28 22:45:02] [INFO] Fetching VM list (page 2)...
[2026-05-28 22:45:03] [INFO] Found 5 VMs in page 2
[2026-05-28 22:45:03] [INFO] Fetched all VMs (total: 55)
[2026-05-28 22:45:03] [INFO] Found 55 VMs to process

[2026-05-28 22:45:03] [INFO] VM LIST:
[2026-05-28 22:45:03] [INFO] --------------------------------------------------------------------------------
[2026-05-28 22:45:03] [INFO] 1. test-vm-01 (UUID: 1145a8a7-..., Power State: off)
[2026-05-28 22:45:03] [INFO] 2. test-vm-02 (UUID: 2245a8a7-..., Power State: on)
[2026-05-28 22:45:03] [INFO] 3. test-vm-03 (UUID: 3345a8a7-..., Power State: on)
... (rest of VMs)

[2026-05-28 22:45:03] [INFO] ================================================================================
[2026-05-28 22:45:03] [INFO] PROCESSING VM 1/55: test-vm-01
[2026-05-28 22:45:03] [INFO] ================================================================================
[2026-05-28 22:45:03] [INFO] UUID: 1145a8a7-7f5c-430c-4c71-f47c91f517df
[2026-05-28 22:45:03] [INFO] Initial Power State: off

[2026-05-28 22:45:03] [INFO] [VM 1/55] [test-vm-01] STEP 2: VM is already powered off. Skipping.
[2026-05-28 22:45:03] [INFO] [VM 1/55] [test-vm-01] STEP 3: Updating memory to 10GB...
[2026-05-28 22:45:03] [INFO] --------------------------------------------------------------------------------
[2026-05-28 22:45:03] [INFO] [VM 1/55] [test-vm-01] Fetching current VM configuration for memory update
[2026-05-28 22:45:04] [INFO] [VM 1/55] [test-vm-01] Updating memory to 10240 MB (10.0 GB)
[2026-05-28 22:45:05] [INFO] [VM 1/55] [test-vm-01] Memory update task initiated: a1b2c3d4-...
[2026-05-28 22:45:05] [INFO] [VM 1/55] [test-vm-01] Waiting for Memory update to 10GB to complete...
[2026-05-28 22:45:10] [INFO] [VM 1/55] [test-vm-01] Check 1/60: Status = succeeded, Progress = 100%
[2026-05-28 22:45:10] [SUCCESS] [VM 1/55] [test-vm-01] ✓ Memory update to 10GB completed successfully

... (rest of steps for VM 1)

[2026-05-28 22:50:00] [INFO] ================================================================================
[2026-05-28 22:50:00] [SUCCESS] [VM 1/55] [test-vm-01] ✓ VM COMPLETED SUCCESSFULLY
[2026-05-28 22:50:00] [INFO] ================================================================================
[2026-05-28 22:50:00] [INFO] VM Name: test-vm-01
[2026-05-28 22:50:00] [INFO] UUID: 1145a8a7-7f5c-430c-4c71-f47c91f517df
[2026-05-28 22:50:00] [INFO] Final State: Powered On with 256MB RAM
[2026-05-28 22:50:00] [INFO] ================================================================================

[2026-05-28 22:50:10] [INFO] Waiting 10 seconds before processing next VM...

... (processing VMs 2-55)

[2026-05-28 23:45:00] [INFO] ================================================================================
[2026-05-28 23:45:00] [INFO] ALL VMS PROCESSING COMPLETED
[2026-05-28 23:45:00] [INFO] ================================================================================
[2026-05-28 23:45:00] [INFO] Total VMs: 55
[2026-05-28 23:45:00] [INFO] Successful: 53
[2026-05-28 23:45:00] [INFO] Failed: 2
[2026-05-28 23:45:00] [INFO] Success Rate: 96.4%
[2026-05-28 23:45:00] [INFO] Total Duration: 60.2 minutes (3612 seconds)
[2026-05-28 23:45:00] [INFO] Average Time per VM: 65.7 seconds
[2026-05-28 23:45:00] [INFO] ================================================================================

[2026-05-28 23:45:00] [INFO] SUCCESSFUL VMs:
[2026-05-28 23:45:00] [INFO]   ✓ test-vm-01
[2026-05-28 23:45:00] [INFO]   ✓ test-vm-02
... (all successful VMs)

[2026-05-28 23:45:00] [INFO] FAILED VMs:
[2026-05-28 23:45:00] [INFO]   ✗ test-vm-45
[2026-05-28 23:45:00] [INFO]   ✗ test-vm-51
[2026-05-28 23:45:00] [INFO] ================================================================================
```

## APIs Used

### Prism v1 APIs

1. **List VMs**
   - Endpoint: `GET /PrismGateway/services/rest/v1/vms`
   - Purpose: Fetch list of VMs from the cluster
   - Parameters:
     - `count`: Number of VMs per page
     - `page`: Page number
     - `sortCriteria`: Sort field
     - `searchAttributeList`: Attributes to search
     - `filterCriteria`: Filter conditions
     - `projection`: Data fields to include

2. **Get VM CPU Statistics**
   - Endpoint: `GET /PrismGateway/services/rest/v1/vms/{vmId}/stats`
   - Purpose: Retrieve VM CPU usage metrics
   - Parameters:
     - `metrics`: Metric names (e.g., `hypervisor_cpu_usage_ppm`)
     - `startTimeInUsecs`: Start time in microseconds
     - `endTimeInUsecs`: End time in microseconds
     - `intervalInSecs`: Interval between data points

3. **Check Task Status**
   - Endpoint: `GET /PrismGateway/services/rest/v1/progress_monitors`
   - Purpose: Monitor task progress and status
   - Parameters:
     - `filterCriteria`: Filter by task UUID

### Prism v2 APIs

1. **Get VM Details**
   - Endpoint: `GET /PrismGateway/services/rest/v2.0/vms/{uuid}`
   - Purpose: Retrieve detailed VM configuration
   - Parameters:
     - `include_vm_disk_config`: Include disk configuration
     - `include_vm_nic_config`: Include NIC configuration

2. **Power Off VM**
   - Endpoint: `POST /PrismGateway/services/rest/v2.0/vms/{uuid}/set_power_state`
   - Purpose: Power off a VM
   - Payload: `{"transition": "off"}`
   - Returns: `task_uuid` for tracking

3. **Power On VM**
   - Endpoint: `POST /PrismGateway/services/rest/v2.0/vms/{uuid}/set_power_state`
   - Purpose: Power on a VM
   - Payload: `{"transition": "on"}`
   - Returns: `task_uuid` for tracking

4. **Update VM Memory**
   - Endpoint: `PUT /PrismGateway/services/rest/v2.0/vms/{uuid}`
   - Purpose: Update VM configuration (memory, CPU, etc.)
   - Parameters:
     - `include_vm_disk_config`: Include disk config in response
     - `include_vm_nic_config`: Include NIC config in response
     - `includeVMDiskSizes`: Include disk sizes in response
     - `includeAddressAssignments`: Include address assignments in response
   - Payload: Full VM configuration with updated `memory_mb` field
   - Returns: `task_uuid` for tracking (or immediate completion)

## HAR File Analysis

This script was created based on analysis of the HAR file `10.46.117.165.har`, which captured the following operations in the Prism UI:

- VM listing and search operations
- VM power state changes (on/off)
- VM configuration updates (memory resize)
- VM statistics queries (CPU usage monitoring)
- Task status monitoring

Key findings from HAR analysis:
- Power operations use v2 `set_power_state` endpoint with `{"transition": "on/off"}` payload
- Memory updates use v2 PUT endpoint with full VM config including `memory_mb` field
- Task monitoring uses v1 `progress_monitors` endpoint with UUID filtering
- CPU stats use v1 stats endpoint with `hypervisor_cpu_usage_ppm` metric

## Error Handling

The script includes comprehensive error handling:

- Network connectivity issues
- API authentication failures
- Task execution failures
- Timeout scenarios
- Invalid responses

Each operation checks for success and logs detailed error information if failures occur.

## Timeouts and Retries

- **Task Completion**: Max 5 minutes (60 checks × 5 seconds)
- **CPU Monitoring**: Max 10 minutes (60 checks × 10 seconds)
- **API Requests**: 60 second timeout per request

## Exit Codes

- `0` - Success
- `1` - Error or failure

## Safety Considerations

- The script processes all VMs in the cluster sequentially
- All power state changes wait for task completion before proceeding
- Memory updates are only performed when VM is powered off
- CPU monitoring includes timeout to prevent infinite waiting
- 10-second delay between VMs to avoid overwhelming the cluster
- Each VM is processed independently - failures don't stop the entire run
- Comprehensive logging with VM name and count for easy tracking

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify Prism IP and port
   - Check network connectivity
   - Ensure SSL certificate trust

2. **Authentication Failed**
   - Verify username and password
   - Check user permissions

3. **VM Not Found**
   - Ensure cluster has at least one VM
   - Check filter criteria

4. **Task Timeout**
   - Increase `MAX_RETRIES` value
   - Check cluster performance
   - Review Prism task logs

5. **CPU Never Drops Below Threshold**
   - Increase `MAX_CPU_RETRIES` value
   - Adjust `CPU_THRESHOLD_PPM` value
   - Check VM workload

## Related Scripts

- `vm_power_on_pe.py` - Sequential VM power-on automation
- `power_off_vms_sequential.py` - Sequential VM power-off automation
- `analyze_recovery_points.py` - VM recovery point analysis

## Author

Created based on HAR file analysis from Nutanix Prism UI operations.

## Version

2.0.0 - All VMs processing (2026-05-28)
- Process all VMs in the cluster instead of just one
- Added VM count tracking (e.g., "VM 1/55")
- Added VM name to all log messages
- Added comprehensive summary statistics
- Added successful/failed VM lists at the end
- Added pagination support for large VM lists

1.0.0 - Initial release (2026-05-28)
- Single VM processing

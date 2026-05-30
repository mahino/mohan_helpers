# NCM Cost Governance API Endpoints

This document lists all unique API endpoints discovered across the cost governance scripts.

## Base URLs
- Primary: `https://ncm.services.nconprem-10-53-55-30.ccpnx.com`
- Secondary: `https://ncm.services.nconprem-10-53-58-35.ccpnx.com`
- Tertiary: `https://ncm.services.nconprem-10-53-60-173.ccpnx.com`

## Authentication
- Method: HTTP Basic Authentication
- Credentials: `admin:Nutanix.123`
- Header: `Authorization: Basic YWRtaW46TnV0YW5peC4xMjM=`

## API Categories

### 1. Reports APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/reports/download` | POST | Download reports | cg_random_reports_download.py, cc_reports_download.py, system_reports_download.py |
| `/v1/reports/download/status?downloadId={id}` | GET | Check report status | cg_random_reports_download.py, cc_reports_download.py |
| `/v1/reports/share` | POST | Share reports | cg_random_report_shares.py, cc_reports_share.py |

### 2. Budget APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/global/budgets/listResourceGroups` | GET | List resource groups for budgets | create_budget.py |
| `/v1/cg/budgets/analysis?search=&limit=15&offset=1` | GET | Get budget analysis | cg_random_reports_download.py |
| `/v1/cg/global/budgets` | POST | Create budgets | create_budget.py |
| `/v1/cg/budgets/{budget_uuid}/report/download` | POST | Download budget reports | cg_random_reports_download.py |

### 3. Cost Center APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/global/costCenters?limit={limit}&offset={offset}` | GET | List cost centers | create_business_unit.py |
| `/v1/cg/global/costCenter` | POST | Create cost center | create_cost_center_v2.py |
| `/v1/cg/global/costCenter/{id}` | DELETE | Delete cost center | delete_business_unit.py |

### 4. Business Unit APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/global/businessUnit` | POST | Create business unit | create_business_unit.py |
| `/v1/cg/global/businessUnit/{id}` | DELETE | Delete business unit | delete_business_unit.py |

### 5. Chargeback APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/global/chargeback/configuration` | GET | Get chargeback configuration | delete_business_unit.py |
| `/v1/cg/global/chargeback/availableAccounts` | GET | Get available accounts | create_cost_center_v2.py |
| `/v1/cg/global/chargeback/availableAccounts/usedTags?provider=nx&parentAccount={uuid}` | GET | Get used tags for account | create_cost_center_v2.py |
| `/v1/cg/global/chargeback/uploadConfiguration` | POST | Upload chargeback configuration | upload_parallel.py, upload_cc.py |
| `/v1/cg/global/chargeback/getAllUploadConfig` | GET | Get all upload configurations | upload_parallel.py, upload_cc.py |

### 6. Metering APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/nutanix/metering/clusters?limit=500&offset=1` | POST | Get metering clusters | cg_random_reports_download.py, cg_random_report_shares.py |

### 7. Analysis APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/nx/analysis/dimensions/values?resourceGroupIds={id}&dimensions=tagKeys&resourceGroupType=billingAccount` | GET | Get dimension values (tag keys) | create_cost_center_v2.py |
| `/v1/cg/nx/analysis/dimensions/values?resourceGroupIds={id}&dimensions={tag}&resourceGroupType=billingAccount` | GET | Get dimension values (specific tag) | create_cost_center_v2.py |

### 8. Rate Cards APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/config/rate-cards` | GET | Get rate cards | get_active_tcos.py, create_rate_cards.py |
| `/v1/cg/config/rate-cards/actions/download?cloud=Nutanix` | GET | Download rate cards | download_UDM.py, download_parallel.py |

### 9. TCO (Total Cost of Ownership) APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/config/tco/purchases` | GET/POST | TCO purchases | download_TCO.py, download_parallel.py, upload_parallel.py, upload_tco.py |
| `/v1/cg/config/tco/configs?limit={limit}&offset={offset}&costHeadAction={action}` | POST | TCO configurations | fetch_TCOs_count.py |

### 10. User APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/v1/cg/users/list` | GET | List users | create_budget.py |

### 11. Nutanix v3 APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `/api/nutanix/v3/accounts/list` | POST | List accounts | create_cost_center_v2.py |

### 12. External APIs
| Endpoint | Method | Description | Used In |
|----------|--------|-------------|---------|
| `{ARGO_BASE_URL}/api/v1/workflows/{NAMESPACE}` | GET | Argo workflows | scrape_argo_workflows.py |

## API Testing Framework

Use the `api_parallel_tester.py` script to test these APIs:

### Basic Usage
```bash
# Test all APIs with different APIs per worker (5 iterations)
python api_parallel_tester.py --mode different --iterations 5

# Test with same API for all workers (10 iterations)
python api_parallel_tester.py --mode same --iterations 10

# Test for a specific duration (5 minutes)
python api_parallel_tester.py --mode different --duration 300

# Test for 1 minute with specific APIs
python api_parallel_tester.py --mode same --duration 60 --apis reports_download,budgets_analysis

# Test specific APIs only (3 iterations)
python api_parallel_tester.py --mode different --iterations 3 --apis reports_download,budgets_analysis

# Test each API 3 times per iteration (nested loops)
python api_parallel_tester.py --mode same --iterations 5 --api-iterations 3

# Test different APIs, each 2 times, for 2 minutes
python api_parallel_tester.py --mode different --duration 120 --api-iterations 2

# List all available APIs
python api_parallel_tester.py --list-apis
```

### Features
- **5 Parallel Workers**: Configurable parallel execution
- **Two Execution Modes**:
  - **Iterations Mode**: Run for a specific number of iterations (`--iterations`)
  - **Duration Mode**: Run for a specific time duration (`--duration` in seconds)
- **Two Testing Modes**:
  - `same`: All workers test the same API (randomly selected each iteration)
  - `different`: Each worker tests a different API
- **API Iterations**: Each API can be tested multiple times within each iteration (nested loops)
- **Comprehensive Metrics**: Response times, status codes, success rates, percentiles
- **Enhanced Report Download Handling**: Automatic status polling for report APIs with download duration tracking
- **Rate Limiting Detection**: Identifies and reports 429 rate limit responses
- **Thread-Safe**: Safe for parallel execution
- **Detailed Logging**: Full request/response logging with timing
- **Real-time Progress**: Shows remaining time in duration mode

### Metrics Tracked
- Response times (min, max, avg, median, P90, P95, P99)
- Status code distribution
- Success/failure rates
- Error counts
- Rate limiting hits (429 responses)
- Throughput (calls per second)
- Per-API performance breakdown
- **Report-specific metrics**:
  - Download duration (API success to completion)
  - Status check counts
  - End-to-end processing times

## Status API Changes

Both `cg_random_reports_download.py` and `cc_reports_download.py` have been updated with:
- **Timeout**: 10 minutes maximum (20 retries × 30 seconds)
- **Frequency**: 30 seconds between status checks
- **Enhanced Metrics**: Download duration tracking from API success to completion

## Configuration Notes

1. **SSL Verification**: Disabled (`verify=False`) for all requests
2. **Timeouts**: 300 seconds (5 minutes) for most API calls
3. **Rate Limiting**: Implemented in download scripts (3 requests per minute)
4. **Authentication**: Basic auth with admin credentials
5. **Content Type**: `application/json` for all requests

## Nested Loop Behavior

The `--api-iterations` parameter creates nested loops for more intensive testing:

```
For each main iteration:
  For each worker (5 parallel workers):
    For each API iteration (--api-iterations):
      Execute API call
```

**Example with `--api-iterations 3`:**
- **Same Mode**: All 5 workers test the same API 3 times each = 15 parallel API calls per iteration
- **Different Mode**: Workers test different APIs, each 3 times = 15 parallel API calls per iteration

This allows for more intensive load testing and better statistical sampling of API performance.

## Error Handling

Common HTTP status codes:
- `200, 201, 202, 204`: Success
- `429`: Rate limited (handled with backoff)
- `400, 401, 403, 404`: Client errors
- `500, 502, 503`: Server errors

All scripts include comprehensive error handling and logging for debugging API issues.

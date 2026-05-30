# Generic Logging Utility

A reusable logging utility for all Python scripts across the project.

## Features

- ✅ **Automatic log directory creation** - Creates a `logs` folder in the same directory as your script
- ✅ **Timestamped log files** - Format: `scriptname_YYYYMMDD_HHMMSS.log`
- ✅ **Dual output** - Logs to both file and console
- ✅ **Easy to use** - Just 2 lines of code to set up
- ✅ **Consistent formatting** - Standardized log format across all scripts

## Quick Start

### Basic Usage

```python
from logger_util import get_logger

# Initialize logger (pass __file__ to auto-detect script location)
logger = get_logger(__file__)

# Use it!
logger.info("Script started")
logger.warning("This is a warning")
logger.error("An error occurred")
logger.debug("Debug information")
```

### Get Logger and Log File Path

```python
from logger_util import get_logger_with_path

logger, log_path = get_logger_with_path(__file__)
logger.info(f"Logging to: {log_path}")
```

### Custom Log Level

```python
import logging
from logger_util import get_logger

# Set to DEBUG to see more detailed logs
logger = get_logger(__file__, log_level=logging.DEBUG)
```

## Log Levels

- `logger.debug()` - Detailed information for debugging
- `logger.info()` - General informational messages
- `logger.warning()` - Warning messages
- `logger.error()` - Error messages
- `logger.critical()` - Critical errors

## File Structure

```
your_project/
├── logger_util.py          # The logging utility (in root)
└── cost_governnance/
    ├── create_cost_center.py
    ├── download_TCO.py
    └── logs/                # Auto-created logs folder
        ├── create_cost_center_20251126_143022.log
        └── download_TCO_20251126_150145.log
```

## Log File Format

Each log entry includes:
- Timestamp (YYYY-MM-DD HH:MM:SS)
- Script name
- Log level (INFO, WARNING, ERROR, etc.)
- Message

Example:
```
2025-11-26 14:30:22 - create_cost_center - INFO - Starting cost center creation process
2025-11-26 14:30:23 - create_cost_center - INFO - Found 5 available accounts
2025-11-26 14:30:25 - create_cost_center - ERROR - Error creating cost center: API returned 400
```

## Console Output

Console output is simplified (no script name) for better readability:
```
2025-11-26 14:30:22 - INFO - Starting cost center creation process
2025-11-26 14:30:23 - INFO - Found 5 available accounts
2025-11-26 14:30:25 - ERROR - Error creating cost center: API returned 400
```

## Migration Guide

### Before (using print statements):
```python
print("Processing account...")
print(f"Error: {error_message}")
```

### After (using logger):
```python
from logger_util import get_logger

logger = get_logger(__file__)
logger.info("Processing account...")
logger.error(f"Error: {error_message}")
```

## Best Practices

1. **Initialize logger at the top of your script** (after imports)
2. **Use appropriate log levels**:
   - `info()` for normal operations
   - `warning()` for potential issues
   - `error()` for errors that don't stop execution
   - `debug()` for detailed debugging information
3. **Include context in log messages**:
   ```python
   logger.info(f"Processing account: {account_name}")
   logger.error(f"Failed to create cost center '{name}': {error}")
   ```

## Examples

### Example 1: API Script with Error Handling

```python
import requests
from logger_util import get_logger

logger = get_logger(__file__)

def fetch_data(url):
    logger.info(f"Fetching data from: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logger.info("✓ Successfully fetched data")
            return response.json()
        else:
            logger.error(f"API returned status {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        return None
```

### Example 2: Processing Multiple Items

```python
from logger_util import get_logger

logger = get_logger(__file__)

items = ["item1", "item2", "item3"]
logger.info(f"Processing {len(items)} items")

success_count = 0
error_count = 0

for item in items:
    logger.info(f"Processing: {item}")
    try:
        # Process item
        success_count += 1
        logger.info(f"✓ Successfully processed: {item}")
    except Exception as e:
        error_count += 1
        logger.error(f"✗ Failed to process {item}: {str(e)}")

logger.info(f"Summary: {success_count} succeeded, {error_count} failed")
```

## Troubleshooting

### Import Error
If you get `ModuleNotFoundError: No module named 'logger_util'`:

```python
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger
```

### Permission Error
If you get a permission error when creating the logs folder, ensure your script has write permissions in its directory.

## Future Enhancements

Potential features to add:
- Log rotation (automatic cleanup of old logs)
- Remote logging (send logs to a central server)
- JSON formatted logs for easier parsing
- Email alerts for critical errors


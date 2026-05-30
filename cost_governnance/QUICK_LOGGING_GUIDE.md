# Quick Logging Guide - Copy & Paste Ready

## 🚀 Add Logging to Any Script (2 Steps)

### Step 1: Add imports at the top
```python
import sys
from pathlib import Path

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger

# Initialize logger
logger = get_logger(__file__)
```

### Step 2: Replace print statements
```python
# Before:
print("Processing started")
print(f"Error: {error_message}")

# After:
logger.info("Processing started")
logger.error(f"Error: {error_message}")
```

## 🌐 Add HTTP Request Logging (Automatic!)

### For scripts using the requests library:

```python
import sys
from pathlib import Path

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger, LoggedRequests

# Initialize logger
logger = get_logger(__file__)

# Initialize logged requests (replaces: import requests)
requests = LoggedRequests(logger)

# Use exactly like normal requests - logging is automatic!
response = requests.get(url, headers=headers)
response = requests.post(url, data=data, headers=headers)
```

**What gets logged automatically:**
- ✅ Request method and URL
- ✅ Response status code
- ✅ Time taken (seconds and milliseconds)
- ✅ Error messages if request fails
- ✅ Error response body for 4xx/5xx errors

**Example log output:**
```
2025-11-26 14:30:22 - INFO - [API REQUEST] GET https://api.example.com/data
2025-11-26 14:30:23 - INFO - [API RESPONSE] GET https://api.example.com/data
2025-11-26 14:30:23 - INFO - [STATUS CODE] 200
2025-11-26 14:30:23 - INFO - [TIME TAKEN] 1.2345 seconds (1234.56 ms)
```

## 📝 Common Patterns

### API Requests
```python
logger.info(f"Fetching data from: {url}")
response = requests.get(url, headers=headers)
if response.status_code == 200:
    logger.info("✓ Successfully fetched data")
else:
    logger.error(f"API returned status {response.status_code}: {response.content}")
```

### Processing Items
```python
logger.info(f"Processing {len(items)} items")
for item in items:
    logger.info(f"Processing: {item}")
    try:
        # do something
        logger.info(f"✓ Successfully processed: {item}")
    except Exception as e:
        logger.error(f"✗ Failed to process {item}: {str(e)}")
```

### Summary Statistics
```python
logger.info("=" * 80)
logger.info(f"Processing completed!")
logger.info(f"Total successful: {success_count}")
logger.info(f"Total errors: {error_count}")
logger.info("=" * 80)
```

## 📂 Where Logs Are Saved

Logs are automatically saved to: `<script_directory>/logs/<script_name>_YYYYMMDD_HHMMSS.log`

Example:
- Script: `/home/mohan.as1/mohan_helpers/cost_governnance/create_cost_center.py`
- Log: `/home/mohan.as1/mohan_helpers/cost_governnance/logs/create_cost_center_20251126_143022.log`

## 🎯 Log Levels

```python
logger.debug("Detailed debug information")    # Only shown if debug mode enabled
logger.info("General information")            # Normal operations
logger.warning("Warning message")             # Potential issues
logger.error("Error message")                 # Errors that don't stop execution
logger.critical("Critical error")             # Critical failures
```

## 🔧 Enable Debug Mode

```python
import logging
from logger_util import get_logger

logger = get_logger(__file__, log_level=logging.DEBUG)
```

## ✅ That's It!

Your script now has:
- ✅ Automatic log file creation
- ✅ Timestamped logs
- ✅ Console + file output
- ✅ Organized in `logs/` folder
- ✅ Easy to debug and track

For more details, see: `/home/mohan.as1/mohan_helpers/LOGGING_README.md`


# ✅ HTTP Request Logging Added!

## 🎉 What's New

The logging system now includes **automatic HTTP request logging**! Every API call made using the `LoggedRequests` wrapper is automatically logged with detailed information.

## 📋 What Gets Logged

For every HTTP request, the following is automatically logged:

1. **Request Information**
   - HTTP Method (GET, POST, PUT, DELETE, etc.)
   - Full URL

2. **Response Information**
   - HTTP Status Code
   - Time Taken (in seconds and milliseconds)

3. **Error Information** (if request fails)
   - Error message
   - Response body (first 500 characters for 4xx/5xx errors)

## 🚀 How to Use

### Before (without HTTP logging):
```python
import requests
import json

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
```

### After (with automatic HTTP logging):
```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger, LoggedRequests

logger = get_logger(__file__)
requests = LoggedRequests(logger)  # ← Use this instead of import requests

# Use exactly like normal requests - logging happens automatically!
response = requests.get(url, headers=headers)
```

## 📝 Example Log Output

### Console Output:
```
2025-11-26 14:30:22 - INFO - [API REQUEST] GET https://ncm.services.example.com/v1/accounts
2025-11-26 14:30:23 - INFO - [API RESPONSE] GET https://ncm.services.example.com/v1/accounts
2025-11-26 14:30:23 - INFO - [STATUS CODE] 200
2025-11-26 14:30:23 - INFO - [TIME TAKEN] 1.8833 seconds (1883.32 ms)
```

### Log File:
```
2025-11-26 14:30:22 - create_cost_center - INFO - [API REQUEST] GET https://ncm.services.example.com/v1/accounts
2025-11-26 14:30:23 - create_cost_center - INFO - [API RESPONSE] GET https://ncm.services.example.com/v1/accounts
2025-11-26 14:30:23 - create_cost_center - INFO - [STATUS CODE] 200
2025-11-26 14:30:23 - INFO - [TIME TAKEN] 1.8833 seconds (1883.32 ms)
```

## 🔧 Supported HTTP Methods

The `LoggedRequests` wrapper supports all standard HTTP methods:

- ✅ `requests.get(url, **kwargs)`
- ✅ `requests.post(url, **kwargs)`
- ✅ `requests.put(url, **kwargs)`
- ✅ `requests.patch(url, **kwargs)`
- ✅ `requests.delete(url, **kwargs)`
- ✅ `requests.head(url, **kwargs)`
- ✅ `requests.options(url, **kwargs)`

All parameters work exactly the same as the standard `requests` library!

## ✅ Updated Files

1. **logger_util.py**
   - Added `LoggedRequests` class for HTTP logging
   - Added timing for each request
   - Added error handling and logging

2. **create_cost_center.py**
   - Updated to use `LoggedRequests` instead of `requests`
   - All API calls now automatically logged

## 📊 Benefits

1. **Automatic Logging**: No need to manually log each API call
2. **Consistent Format**: All HTTP logs follow the same format
3. **Performance Tracking**: See exactly how long each API call takes
4. **Error Debugging**: Automatically logs error responses
5. **Drop-in Replacement**: Works exactly like the `requests` library

## 🎯 Migration Example

### Old Code:
```python
import requests
import json

headers = {'Content-Type': 'application/json'}
url = "https://api.example.com/data"

print(f"Fetching from {url}")
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code != 200:
    print(f"Error: {response.content}")
```

### New Code (with automatic logging):
```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger, LoggedRequests

logger = get_logger(__file__)
requests = LoggedRequests(logger)

headers = {'Content-Type': 'application/json'}
url = "https://api.example.com/data"

# All of this is now logged automatically!
response = requests.get(url, headers=headers)

# No need for manual status logging - it's automatic!
# Error responses are also logged automatically!
```

## 🔍 Error Logging Example

When an API returns an error:

```
2025-11-26 14:30:22 - INFO - [API REQUEST] POST https://api.example.com/create
2025-11-26 14:30:23 - INFO - [API RESPONSE] POST https://api.example.com/create
2025-11-26 14:30:23 - INFO - [STATUS CODE] 400
2025-11-26 14:30:23 - INFO - [TIME TAKEN] 0.5432 seconds (543.21 ms)
2025-11-26 14:30:23 - ERROR - [ERROR RESPONSE] {"errorCode":"IM2037","errorMessage":"Invalid input"}
```

## 📚 Documentation

For more details, see:
- `/home/mohan.as1/mohan_helpers/LOGGING_README.md` - Full logging guide
- `/home/mohan.as1/mohan_helpers/cost_governnance/QUICK_LOGGING_GUIDE.md` - Quick reference

## 🎉 Ready to Use!

The HTTP logging is now active in `create_cost_center.py` and ready to be used in any other script!

Simply replace:
```python
import requests
```

With:
```python
from logger_util import get_logger, LoggedRequests
logger = get_logger(__file__)
requests = LoggedRequests(logger)
```

And you're done! 🚀


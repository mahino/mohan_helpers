import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.nseindia.com/',
    'Connection': 'keep-alive',
}

# First, get cookies by visiting the homepage
session = requests.Session()
session.headers.update(headers)

# NSE requires a cookie from the homepage before allowing API access
homepage = session.get('https://www.nseindia.com')

# Now make your actual request
url = 'https://www.nseindia.com/get-quotes/equity?symbol=TATACHEM'
response = session.get(url)

print(response.status_code)
print(response.text)

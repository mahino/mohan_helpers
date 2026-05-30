import requests
import time

def fetch_stock_data(symbol, session):
    # First hit the HTML page to get cookies/session setup
    session.get(f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}", timeout=5)
    
    # Now call the API for data
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    response = session.get(url, timeout=10)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for {symbol}")
        return None

def print_stock_info(symbol, data):
    price_info = data.get("priceInfo", {})
    security_info = data.get("securityInfo", {})
    order_book = data.get("marketDeptOrderBook", {})

    print(f"--- {symbol} ---")
    print(f"Last Price     : {price_info.get('lastPrice')}")
    print(f"Change         : {price_info.get('change')}")
    print(f"P Change       : {price_info.get('pChange')}%")
    print(f"Day High       : {price_info.get('intraDayHighLow', {}).get('max')}")
    print(f"Day Low        : {price_info.get('intraDayHighLow', {}).get('min')}")
    print(f"52 Week High   : {price_info.get('weekHighLow', {}).get('max')}")
    print(f"52 Week Low    : {price_info.get('weekHighLow', {}).get('min')}")
    print(f"P/E Ratio      : {security_info.get('pe')}")
    print(f"Volume (Alt)   : {order_book.get('quantityTraded') or 'N/A'}")
    print()


def main():
    # Read symbols from stocks.txt
    with open("stocks.txt", "r") as file:
        symbols = [line.strip().upper() for line in file if line.strip()]

    # Setup session with headers
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    })

    # Initial visit to set cookies
    session.get("https://www.nseindia.com", timeout=5)

    for symbol in symbols:
        print(f"Fetching data for: {symbol}")
        data = fetch_stock_data(symbol, session)
        if data:
            print_stock_info(symbol, data)
        time.sleep(1)  # Prevent hammering the server

if __name__ == "__main__":
    main()

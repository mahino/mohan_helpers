import requests
import json
import time
from datetime import datetime

import os
import json
from datetime import datetime

def load_historical_files(folder_path, days=15):
    files = [
        f for f in os.listdir(folder_path)
        if f.startswith("daily_stats_") and f.endswith(".json")
    ]
    files = sorted(files)[-days:]  # Pick last N files (sorted by name/date)
    data = []

    for f in files:
        path = os.path.join(folder_path, f)
        with open(path, "r") as file:
            try:
                json_data = json.load(file)
                data.append(json_data)
            except Exception as e:
                print(f"⚠️ Failed to load {f}: {e}")
    return data

def build_price_history(data_by_day):
    symbol_history = {}

    for daily_data in data_by_day:
        for symbol, values in daily_data.items():
            price = values.get("lastPrice", None)
            if price is not None:
                symbol_history.setdefault(symbol, []).append(price)

    return symbol_history

def compute_changes(price_list, interval):
    if len(price_list) >= interval + 1:
        return round(price_list[-1] - price_list[-interval - 1], 2)
    return None

def enrich_with_trends(today_data, price_history):
    for symbol, prices in price_history.items():
        if symbol in today_data:
            today_data[symbol]["last5Days"] = compute_changes(prices, 5)
            today_data[symbol]["last10Days"] = compute_changes(prices, 10)
            today_data[symbol]["last15Days"] = compute_changes(prices, 15)
    return today_data

def update_todays_file(folder_path="."):
    today_str = datetime.now().strftime("%Y%m%d")
    expected_filename = None

    # Find today's file
    for f in os.listdir(folder_path):
        if f.startswith(f"daily_stats_{today_str}") and f.endswith(".json"):
            expected_filename = f
            break

    if not expected_filename:
        print(f"❌ No file found for today ({today_str})")
        return

    today_file = os.path.join(folder_path, expected_filename)
    print(f"📦 Updating today's file: {today_file}")

    with open(today_file, "r") as file:
        today_data = json.load(file)

    # Load up to 15 days historical data (including today)
    historical_data = load_historical_files(folder_path, days=15)
    price_history = build_price_history(historical_data)
    enriched_data = enrich_with_trends(today_data, price_history)

    # Overwrite today’s file with enriched data
    with open(today_file, "w") as file:
        json.dump(enriched_data, file, indent=2)

    print("✅ Today's data enriched with last5Days, last10Days, last15Days changes.")

# Run the updater



# Usage


def fetch_stock_data(symbol, session):
    # Required to set cookies properly
    url = f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
    session.get(url, timeout=5)
    response = session.get(url, timeout=10)
    print(response.status_code)
    print(response.content)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for {symbol}")
        return None

def fetch_historical_data(symbol, session):
    url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[%22EQ%22]&from=2024-01-01&to=2025-12-31"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price_data = data.get("data", [])
            # Get last 6 closes (5 changes = 6 points)
            last_closes = [
                float(entry["CH_CLOSING_PRICE"])
                for entry in price_data[-6:]
                if "CH_CLOSING_PRICE" in entry
            ]
            return last_closes
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
    return []

def extract_relevant_data(symbol, data, history):
    price_info = data.get("priceInfo", {})
    security_info = data.get("securityInfo", {})
    meta = data.get("meta", {})
    corporate_info = data.get("corporateActions", {})
    order_book = data.get("marketDeptOrderBook", {})

    def safe_get(d, key, default=None):
        return d.get(key) if key in d and d.get(key) is not None else default

    # Calculate last 5 changes
    last_5_changes = []
    if len(history) >= 2:
        for i in range(1, len(history)):
            change = round(history[i] - history[i - 1], 2)
            last_5_changes.append(change)

    return {
        "symbol": symbol,
        "companyName": safe_get(meta, "companyName", "N/A"),
        "lastPrice": safe_get(price_info, "lastPrice", 0.0),
        "change": safe_get(price_info, "change", 0.0),
        "dayHigh": safe_get(price_info.get("intraDayHighLow", {}), "max", 0.0),
        "dayLow": safe_get(price_info.get("intraDayHighLow", {}), "min", 0.0),
        "open": safe_get(price_info, "open", 0.0),
        "previousClose": safe_get(price_info, "previousClose", 0.0),
        "closePrice": safe_get(price_info, "close", 0.0),
        "averagePrice": safe_get(price_info, "averagePrice", 0.0),
        "quantityTraded": safe_get(order_book, "quantityTraded", 0),
        "pricebandupper": safe_get(price_info, "priceBandUpper", 0.0),
        "pricebandlower": safe_get(price_info, "priceBandLower", 0.0),
        "high52": safe_get(price_info.get("weekHighLow", {}), "max", 0.0),
        "low52": safe_get(price_info.get("weekHighLow", {}), "min", 0.0),
        "basePrice": safe_get(price_info, "basePrice", 0.0),
        "applicableMargin": safe_get(security_info, "applicableMargin", 0.0),
        "securityVar": safe_get(security_info, "securityVar", 0.0),
        "marketType": safe_get(meta.get("marketDeptOrderBook", {}), "marketType", "N"),
        "purpose": safe_get(corporate_info, "purpose", "N/A"),
        "exDate": safe_get(corporate_info, "exDate", "N/A"),
        "last5DayChanges": last_5_changes
    }

import requests

def is_nse_market_open(session):
    try:
        url = "https://www.nseindia.com/api/marketStatus"
        session.get("https://www.nseindia.com", timeout=5)  # to set cookies
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for market in data.get("marketState", []):
                if market.get("market") == "Capital Market":
                    return market.get("marketStatus") == "Open"
    except Exception as e:
        print(f"⚠️ Could not determine NSE status: {e}")
    return False

import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def load_today_data(folder_path="."):
    today_str = datetime.now().strftime("%Y%m%d")
    for f in os.listdir(folder_path):
        if f.startswith(f"daily_stats_{today_str}") and f.endswith(".json"):
            with open(os.path.join(folder_path, f), "r") as file:
                return json.load(file)
    print("❌ Today's data file not found.")
    return {}

def filter_stocks(data):
    daily_moves = []
    last5day_moves = []

    for symbol, info in data.items():
        prev = info.get("previousClose", 0)
        last = info.get("lastPrice", 0)
        last5 = info.get("last5Days", 0)

        if prev:
            daily_change = ((last - prev) / prev) * 100
            if abs(daily_change) >= 2:
                daily_moves.append((symbol, round(daily_change, 2)))

        if last5:
            last5_change = (last5 / (last - last5)) * 100 if (last - last5) else 0
            if abs(last5) >= 5:
                last5day_moves.append((symbol, round(last5, 2)))

    return daily_moves, last5day_moves

def send_email_alert(daily_changes, last5_changes, sender, password, recipient):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📊 NSE Stock Movement Alert"
    msg["From"] = sender
    msg["To"] = recipient

    html_content = "<h2>📈 Daily Stock Alerts</h2>"
    if daily_changes:
        html_content += "<b>±2% Daily Movers:</b><ul>"
        for sym, change in daily_changes:
            html_content += f"<li>{sym}: {change}%</li>"
        html_content += "</ul>"
    else:
        html_content += "<p>No daily movers found.</p>"

    if last5_changes:
        html_content += "<br><b>±5% Change Over Last 5 Days:</b><ul>"
        for sym, change in last5_changes:
            html_content += f"<li>{sym}: {change}</li>"
        html_content += "</ul>"
    else:
        html_content += "<p>No 5-day movers found.</p>"

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# === MAIN USAGE ===
import os

def notify_stock_alerts():
    data = load_today_data(folder_path=".")
    if not data:
        return

    daily, last5 = filter_stocks(data)

    # Your email credentials
    sender_email = "as.mohan9999@gmail.com"
    sender_password = "gwlk ybgr zhle amoq"
    recipient_email = "as.mohan9999@gmail.com"

    send_email_alert(daily, last5, sender_email, sender_password, recipient_email)

# Call this after enriching today's data


def main():
    if not is_nse_market_open:
        return None
    # Load symbols
    with open("stocks.txt", "r") as file:
        symbols = [line.strip().upper() for line in file if line.strip()]

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        'Cookie': '_abck=2DF8286029C845885A4325A06A8B0F15~-1~YAAQPqIauH67MMSWAQAACyWJ0w1Q2HbCWzBqwdhLCpN1/OzHy85s110Z8f9g8G+wOyLC9lNtZnCY2Q3JkY+M5migCvwlPDZ5z7FN/oYRijvr+WXGqQ5k51oGrFsZMrJPgQqxdmlQhyKyDpxhaO7sJyk5dEIsEYqae9OlV8r0Mz9Up/wXHlW6203Xk2lh1tI9FWdTdw2LH5rJxns0C2KhqiRW8IVAWGEwv7ZXU/8s9WcnBR7eWyCyDBwmmfzkvYVKP/22YC7bUgO6cHk/OsfmSpgDNMlK+Wedk8czjhKTirmiv+PwokkV50Jxeq593d9hKMuvXOCS61ycmDWafg9RhKJ1Ai6tQfPeJaDp+w5F9O9wM/q/egLCWAHPpNQn78wnEwZl+K+KBdsfK8b6Ngyi/+Gs3BTd3upJuNyWCMVLqlrqmOvUghOfZEnVtAYnYNVtJwCV~-1~-1~-1; ak_bmsc=BB81A044EB0F3783D07FC7ACC5FB5989~000000000000000000000000000000~YAAQPqIauM/7MMSWAQAAYJWT0xsU1sPjdOf1MS/prD0YS7TQp9EP2h3l+oiD2I73tIVKK3cemMbcHyY8FpwM8sqiJmb1bovqQkCbJV+r+/jD4/dF3l1Dk+wblqiCvxavumxopoTub8BQYGD85VcxwS6833ermccDcqt9lSV9EEng7OTmwuvoQvBOVFlGn5qPfRETUxus71TAB6+EbEFAB9vjOIGUayFoCrOufoCEmUziXXYiNwX8tXaLeZ/uiPBTjFBDvXnJ3GGu/4LLFi/URxjneY9zNQt1l/byZP6sKsBkwUGEDZVtCFXFXYaOaKrqR44Qn/VO+4pj0uZoJh80UpElLyQycvmXUvQWtPAP; bm_sz=BBFE507943E34CA3467F9F5EC5B794A1~YAAQPqIauH+7MMSWAQAACyWJ0xs4xy9D+8WZzM8lI/K9tsDvd/8yzsLEamwD1P+pr7nLfS+yQ6K8byZNO4bNHVtauUGfdFoWUH7ZNAPqH67+pqghLUBAgkyjbLVrSBfEp5xW+7phWC2WoOUFzCBXmi1syoIDE0kV5gJKf8w8Dtwp+8d5vuYiDwagYNJ8UYxabg6E0wVRCPp5+p2jh8Q0NlFQNbK3TD1OyAAjoIPAXi7a8R4wLNDf+imdu5ceUQnilnuP2A5t2KHJM9Q1fBC7ZnKifdXVm0kIQbeK3JUwc3ErAInde1ma4OSXiNyFuK2Q62wAdwZMAOfQ9MrzU+4mGb26MJsBryHZTNY02RxXxQ==~3617861~3487030; nseappid=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcGkubnNlIiwiYXVkIjoiYXBpLm5zZSIsImlhdCI6MTc0NzMwNjM4NiwiZXhwIjoxNzQ3MzEzNTg2fQ.XNO188aYOZJ0KsxzGb_KAiiIykc4GzxgBRL_aMpgjOU; nsit=dPthaHTIUXSKzX68ucFbQsML'
    })

    # Set cookies
    session.get("https://www.nseindia.com", timeout=5)

    all_stock_data = {}

    for symbol in symbols:
      print(f"Fetching: {symbol}")
      stock_data = fetch_stock_data(symbol, session)
      if not stock_data:
          continue

      history = fetch_historical_data(symbol, session)
      extracted = extract_relevant_data(symbol, stock_data, history)
      all_stock_data[symbol] = extracted

      # Detect significant move (±2%)
      prev_close = extracted.get("previousClose", 0)
      last_price = extracted.get("lastPrice", 0)

      if prev_close:
          percent_change = ((last_price - prev_close) / prev_close) * 100
          if abs(percent_change) >= 2:
              print(f"📈 {symbol}: {round(percent_change, 2)}% (from {prev_close} to {last_price})")

      time.sleep(1)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"./historic_stats/daily_stats_{timestamp}.json"
    with open(filename, "w") as outfile:
        json.dump(all_stock_data, outfile, indent=2)
    # update_today_file(folder_path="./historic_stats")
    update_todays_file(folder_path="./historic_stats")
    print(f"\n✅ Data saved to: {filename}")
    notify_stock_alerts()

if __name__ == "__main__":
    main()

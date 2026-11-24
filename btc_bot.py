import requests
import time
import csv
import os
from datetime import datetime

URL = "https://api.exchange.coinbase.com/products/BTC-USD/ticker"
FILE = "btc_history.csv"

previous_price = None

if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Price", "Change_Percent", "Volume"])

while True:
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        price = float(data["price"])
        volume = float(data["volume"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        change = 0

        if previous_price is not None:
            change = ((price - previous_price) / previous_price) * 100

        with open(FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, price, change, volume])

        print(f"{timestamp} | BTC: ${price:,.2f} | {change:+.4f}%")

        previous_price = price

    except Exception as e:
        print("Error:", e)

    time.sleep(10)
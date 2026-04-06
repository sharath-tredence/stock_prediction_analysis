import yfinance as yf
import pandas as pd

INTERVALS = {
    "1 Minute": "1m",
    "5 Minutes": "5m",
    "15 Minutes": "15m",
    "30 Minutes": "30m",
    "1 Hour": "1h",
    "1 Day": "1d",
    "1 Week": "1wk",
    "1 Month": "1mo"
}

def fetch_stock_data(symbol, interval_label):

    if interval_label not in INTERVALS:
        return None

    interval = INTERVALS[interval_label]

    if interval in ["1m", "5m", "15m", "30m"]:
        period = "7d"
    elif interval == "1h":
        period = "60d"
    else:
        period = "1y"

    stock = yf.Ticker(symbol)
    df = stock.history(period=period, interval=interval)

    if df.empty:
        return None

    df.reset_index(inplace=True)
    return df


def get_latest_price(symbol):
    stock = yf.Ticker(symbol)
    df = stock.history(period="1d")

    if df.empty:
        return None

    return round(df["Close"].iloc[-1], 2)

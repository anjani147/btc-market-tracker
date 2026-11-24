import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="BTC Market Tracker", page_icon="₿", layout="wide")
st.title("₿ Bitcoin Market Tracker")
st.caption("BTC/USD Monitoring | Coinbase API")
FILE = Path(__file__).resolve().parent / "btc_history.csv"

@st.fragment(run_every="10s")
def dashboard():
    if not FILE.exists():
        st.warning("Start btc_bot.py to collect data in the same folder.")
        return
    try:
        df = pd.read_csv(FILE)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
        df = df.dropna(subset=["Timestamp", "Price"])
    except (OSError, ValueError, KeyError, pd.errors.ParserError):
        st.warning("Waiting for valid price data...")
        return
    if df.empty:
        st.info("Waiting for price data...")
        return
    current_price = df["Price"].iloc[-1]
    change = df["Change_Percent"].iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BTC Price", f"${current_price:,.2f}", f"{change:.4f}%")
    col2.metric("Recorded High", f"${df['Price'].max():,.2f}")
    col3.metric("Recorded Low", f"${df['Price'].min():,.2f}")
    col4.metric("Data Points", len(df))
    st.subheader("Bitcoin Price Chart")
    fig = px.line(df.tail(360), x="Timestamp", y="Price", template="plotly_dark")
    fig.update_traces(line_color="#F7931A", line_width=2)
    fig.update_layout(xaxis_title="Time", yaxis_title="BTC Price (USD)", height=450)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Recent Market Data")
    st.dataframe(df.tail(10).iloc[::-1], use_container_width=True)
    last = df["Timestamp"].iloc[-1]
    st.caption(f"Last recorded update: {last} | Dashboard refreshes every 10 seconds")
    if (pd.Timestamp.now() - last).total_seconds() > 60:
        st.warning("Price data is stale. Check whether btc_bot.py is still running.")

dashboard()

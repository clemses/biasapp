# biasapp.py

import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Bias Dashboard", layout="wide")
st.title("📊 Bias Dashboard – Daily & 4H Pattern Recognition")

# Upload
st.sidebar.header("📂 Upload Files")
daily_file = st.sidebar.file_uploader("Upload Daily File (CSV or TXT)", type=["csv", "txt"])
fourh_file = st.sidebar.file_uploader("Upload 4H File (CSV or TXT)", type=["csv", "txt"])

# Helper
def load_and_clean(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    for col in ['Open', 'Close', 'POC', 'VAL', 'VAH']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna().sort_values("Date")

def detect_bias(df):
    results = []
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]

        bias_flags = []

        # POC Trend
        if curr["POC"] > prev["POC"]:
            bias_flags.append("↑ POC Up")
        elif curr["POC"] < prev["POC"]:
            bias_flags.append("↓ POC Down")

        # VAL / VAH proximity
        range_size = curr["VAH"] - curr["VAL"]
        if abs(curr["Close"] - curr["VAL"]) < range_size * 0.2:
            bias_flags.append("🔵 Near VAL")
        if abs(curr["Close"] - curr["VAH"]) < range_size * 0.2:
            bias_flags.append("🔴 Near VAH")

        # Value Area Compression
        if range_size < (prev["VAH"] - prev["VAL"]) * 0.7:
            bias_flags.append("🟡 VA Compression")

        # Candle Direction
        if curr["Close"] > curr["Open"]:
            bias_flags.append("✅ Bullish Close")
        elif curr["Close"] < curr["Open"]:
            bias_flags.append("❌ Bearish Close")

        results.append({
            "Date": curr["Date"],
            "Bias": ", ".join(bias_flags) if bias_flags else "Neutral"
        })
    return pd.DataFrame(results)

# Display Daily Bias
if daily_file:
    st.subheader("📅 Daily Bias Analysis")
    daily_df = load_and_clean(daily_file)
    daily_bias = detect_bias(daily_df)
    st.dataframe(daily_bias)

# Display 4H Bias
if fourh_file:
    st.subheader("⏱️ 4H Bias Analysis")
    fourh_df = load_and_clean(fourh_file)
    fourh_bias = detect_bias(fourh_df)
    st.dataframe(fourh_bias)

# Template download
if st.sidebar.button("📥 Download CSV Template"):
    template = pd.DataFrame(columns=["Date", "Open", "Close", "VAL", "VAH", "POC"])
    st.sidebar.download_button("Download Template", template.to_csv(index=False), "bias_template.csv")

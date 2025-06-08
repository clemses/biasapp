
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bias Dashboard – Enhanced", layout="wide")
st.title("📊 Enhanced Bias Dashboard – Daily & 4H with Multi-Candle Logic and Signal Log")

# Sidebar: Upload
st.sidebar.header("📂 Upload Files")
daily_file = st.sidebar.file_uploader("Upload Daily CSV", type=["csv", "txt"])
fourh_file = st.sidebar.file_uploader("Upload 4H CSV", type=["csv", "txt"])
lookback_n = st.sidebar.slider("🔁 Lookback Period for Trend/Compression", min_value=2, max_value=10, value=3)

# Helper
def clean_df(df):
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    for col in ['Open', 'Close', 'POC', 'VAL', 'VAH']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna().sort_values("Date").reset_index(drop=True)

def summarize_bias(row):
    parts = []
    if "↑" in row['POC Trend']: parts.append("POC Up")
    if "↓" in row['POC Trend']: parts.append("POC Down")
    if row['Near VAL']: parts.append("Near VAL")
    if row['Near VAH']: parts.append("Near VAH")
    if row['Compression']: parts.append("Compression")
    if row['Close Bias'] == "Bullish": parts.append("Bullish Close")
    if row['Close Bias'] == "Bearish": parts.append("Bearish Close")
    return ", ".join(parts) if parts else "Neutral"

def analyze(df, tf_label):
    signals = []
    for i in range(lookback_n, len(df)):
        window = df.iloc[i - lookback_n:i]
        curr = df.iloc[i]
        prev = df.iloc[i - 1]

        # Trend
        poc_trend = "↑" if curr["POC"] > window["POC"].mean() else "↓" if curr["POC"] < window["POC"].mean() else "-"

        # Compression
        va_now = curr["VAH"] - curr["VAL"]
        va_avg = window["VAH"].mean() - window["VAL"].mean()
        compression = va_now < va_avg * 0.7

        # VAL/VAH Proximity
        near_val = abs(curr["Close"] - curr["VAL"]) < va_now * 0.2
        near_vah = abs(curr["Close"] - curr["VAH"]) < va_now * 0.2

        # Close Bias
        close_bias = "Bullish" if curr["Close"] > curr["Open"] else "Bearish" if curr["Close"] < curr["Open"] else "Neutral"

        # Signal text
        label = summarize_bias({
            "POC Trend": poc_trend,
            "Near VAL": near_val,
            "Near VAH": near_vah,
            "Compression": compression,
            "Close Bias": close_bias
        })

        signals.append({
            "Date": curr["Date"].date(),
            "Timeframe": tf_label,
            "POC Trend": poc_trend,
            "Compression": compression,
            "Near VAL": near_val,
            "Near VAH": near_vah,
            "Close Bias": close_bias,
            "Bias Summary": label
        })
    return pd.DataFrame(signals)

# Output columns
col1, col2 = st.columns(2)

# Process Daily
if daily_file:
    daily_df = clean_df(pd.read_csv(daily_file))
    daily_signals = analyze(daily_df, "Daily")
    with col1:
        st.subheader("📅 Daily Bias Summary")
        st.dataframe(daily_signals)

# Process 4H
if fourh_file:
    fourh_df = clean_df(pd.read_csv(fourh_file))
    fourh_signals = analyze(fourh_df, "4H")
    with col2:
        st.subheader("⏱️ 4H Bias Summary")
        st.dataframe(fourh_signals)

# Merge for signal log
if daily_file and fourh_file:
    combined = pd.concat([daily_signals, fourh_signals]).sort_values("Date")
    st.subheader("🧠 Signal Log (Merged)")
    st.dataframe(combined[["Date", "Timeframe", "Bias Summary"]])

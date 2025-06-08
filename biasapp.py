
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bias Dashboard – Enhanced", layout="wide")
st.title("📊 Bias Dashboard – Daily & 4H Pattern Analysis")

# === SIDEBAR UPLOAD ===
st.sidebar.header("📂 Upload CSV Files")
daily_file = st.sidebar.file_uploader("Upload Daily CSV", type=["csv", "txt"])
fourh_file = st.sidebar.file_uploader("Upload 4H CSV", type=["csv", "txt"])

# === CLEANING FUNCTION ===
def clean_df(df):
    df.columns = df.columns.str.strip()
    col_map = {
        'Last': 'Close',
        'Point of Control': 'POC',
        'Value Area Low Value': 'VAL',
        'Value Area High Value': 'VAH',
        'Volume Weighted Average Price': 'VWAP'
    }
    df = df.rename(columns=col_map)
    required = ['Date', 'Open', 'Close', 'POC', 'VAL', 'VAH']
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"❌ Missing columns: {', '.join(missing)}")
        return pd.DataFrame()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    for col in required[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna().sort_values("Date").reset_index(drop=True)

# === ANALYSIS FUNCTION ===
def analyze_candle_bias(df, date_selected, lookback):
    if df.empty or date_selected not in df["Date"].dt.date.values:
        return None, None

    idx = df[df["Date"].dt.date == date_selected].index[0]
    if idx < lookback:
        return None, None

    window = df.iloc[idx - lookback:idx]
    curr = df.iloc[idx]

    bias_explanation = []
    trade_reco = []

    # POC Trend
    poc_trend = "POC is rising" if curr["POC"] > window["POC"].mean() else "POC is falling"
    bias_explanation.append(poc_trend)
    if "rising" in poc_trend:
        trade_reco.append("Look for long continuation")
    else:
        trade_reco.append("Look for short opportunities")

    # Value Area Compression
    va_now = curr["VAH"] - curr["VAL"]
    va_avg = (window["VAH"] - window["VAL"]).mean()
    if va_now < va_avg * 0.7:
        bias_explanation.append("Value area is compressed")
        trade_reco.append("Watch for breakout from range")

    # Close vs VAL/VAH
    if abs(curr["Close"] - curr["VAL"]) < va_now * 0.2:
        bias_explanation.append("Close near VAL")
        trade_reco.append("Possible long from lower range")
    if abs(curr["Close"] - curr["VAH"]) < va_now * 0.2:
        bias_explanation.append("Close near VAH")
        trade_reco.append("Consider short near upper range")

    # Candle Bias
    if curr["Close"] > curr["Open"]:
        bias_explanation.append("Candle closed bullish")
    elif curr["Close"] < curr["Open"]:
        bias_explanation.append("Candle closed bearish")

    return bias_explanation, trade_reco

# === DAILY SECTION ===
if daily_file:
    st.subheader("📅 Daily Bias Analysis")
    df_daily = clean_df(pd.read_csv(daily_file))

    with st.expander("🔎 Analyze Daily Bias"):
        available_dates = df_daily["Date"].dt.date.unique()
        selected_date = st.date_input("Select Daily Candle Date", value=available_dates[-1], min_value=min(available_dates), max_value=max(available_dates))
        daily_lookback = st.slider("Lookback candles (Daily)", min_value=2, max_value=10, value=3)

        bias, reco = analyze_candle_bias(df_daily, selected_date, daily_lookback)
        if bias:
            st.markdown("### 🧠 Bias Explanation")
            st.write("- " + "
- ".join(bias))
            st.markdown("### 🎯 Trade Recommendation")
            st.write("- " + "
- ".join(reco))
        else:
            st.warning("Not enough data before selected candle.")

# === 4H SECTION ===
if fourh_file:
    st.subheader("⏱️ 4H Bias Analysis")
    df_4h = clean_df(pd.read_csv(fourh_file))

    with st.expander("🔎 Analyze 4H Bias"):
        available_dates = df_4h["Date"].dt.date.unique()
        selected_date = st.date_input("Select 4H Candle Date", value=available_dates[-1], key="4h_date", min_value=min(available_dates), max_value=max(available_dates))
        fourh_lookback = st.slider("Lookback candles (4H)", min_value=2, max_value=12, value=4)

        bias, reco = analyze_candle_bias(df_4h, selected_date, fourh_lookback)
        if bias:
            st.markdown("### 🧠 Bias Explanation")
            st.write("- " + "
- ".join(bias))
            st.markdown("### 🎯 Trade Recommendation")
            st.write("- " + "
- ".join(reco))
        else:
            st.warning("Not enough data before selected candle.")

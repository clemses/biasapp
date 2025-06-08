
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bias Dashboard – Interpretive Mode", layout="wide")
st.title("📊 Bias Dashboard – Interpretation, Levels & Market Behavior")

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

# === INTERPRETATION FUNCTION ===
def interpret_bias(curr, window):
    va_range = curr["VAH"] - curr["VAL"]
    center = curr["VAL"] + va_range / 2
    summary = []
    reco = []

    # Interpretation logic
    if abs(curr["POC"] - center) < va_range * 0.1:
        summary.append("POC near center → balanced")
    if curr["POC"] < window["POC"].mean():
        summary.append("POC falling → bearish migration")
    if "VWAP" in curr and abs(curr["VWAP"] - curr["POC"]) < va_range * 0.1:
        summary.append("VWAP ≈ POC → fair value consensus")
    if curr["Close"] < curr["VAL"] and curr["Close"] > curr["Open"]:
        summary.append("Failed breakdown (below VAL rejected)")

    # Trade recommendations
    if curr["Close"] > curr["VAL"] and abs(curr["Close"] - curr["VAL"]) < va_range * 0.1:
        reco.append("🟢 Reversal: VAL tested and rejected, watch for bounce.")
    if "VWAP" in curr and abs(curr["POC"] - curr["VWAP"]) < va_range * 0.1:
        reco.append("📯 POC ≈ VWAP → balanced zone, fade extremes.")

    return summary, reco

# === DISPLAY SECTION ===
def display_analysis(df, tf_label):
    st.subheader(f"🔎 {tf_label} Bias Interpretation")

    dates = df["Date"].dt.date.unique()
    selected_date = st.date_input(f"Select {tf_label} Candle", value=dates[-1], key=f"{tf_label}_date", min_value=min(dates), max_value=max(dates))
    lookback = st.slider(f"Lookback candles ({tf_label})", min_value=2, max_value=10, value=3, key=f"{tf_label}_slider")

    if selected_date not in df["Date"].dt.date.values:
        st.warning("Selected date not found in data.")
        return

    idx = df[df["Date"].dt.date == selected_date].index[0]
    if idx < lookback:
        st.warning("Not enough data before selected date.")
        return

    curr = df.iloc[idx]
    window = df.iloc[idx - lookback:idx]

    summary, reco = interpret_bias(curr, window)

    st.markdown("### 🧠 Bias Interpretation")
    for item in summary:
        st.write("- " + item)

    st.markdown("### 🎯 Trade Recommendation")
    for item in reco:
        st.write("- " + item)

    st.markdown("### 🧭 Key Price Levels")
    st.code(f"VAL: {curr['VAL']:.2f} | POC: {curr['POC']:.2f} | VAH: {curr['VAH']:.2f} | Close: {curr['Close']:.2f}")

    st.markdown("### 📌 What to Watch For")
    st.markdown("""
    - **Volume spikes** at VAL/VAH → strong rejection or breakout.
    - **Fast push through levels** → likely stop runs or directional conviction.
    - **Long dwell time at VAL/VAH** → indecision, wait for follow-through.
    - **Fade the extremes** if POC ≈ VWAP and no expansion.
    """)

# === MAIN SECTIONS ===
if daily_file:
    df_daily = clean_df(pd.read_csv(daily_file))
    display_analysis(df_daily, "Daily")

if fourh_file:
    df_4h = clean_df(pd.read_csv(fourh_file))
    display_analysis(df_4h, "4H")

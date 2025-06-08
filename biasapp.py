
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bias Dashboard – Enhanced Ruleset", layout="wide")
st.title("📊 Bias Dashboard – Structure + Volume & Time-Based Signals")

# === FILE UPLOAD ===
st.sidebar.header("📂 Upload Daily CSV File")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv", "txt"])

# === DATA CLEANING ===
def clean_df(df):
    df.columns = df.columns.str.strip()
    col_map = {
        'Last': 'Close',
        'Point of Control': 'POC',
        'Value Area Low Value': 'VAL',
        'Value Area High Value': 'VAH',
        'Volume Weighted Average Price': 'VWAP',
        '# of Trades': 'Trades'
    }
    df = df.rename(columns=col_map)
    required = ['Date', 'Open', 'Close', 'POC', 'VAL', 'VAH', 'VWAP', 'Volume', 'Trades']
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        return pd.DataFrame()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    for col in required[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna().sort_values("Date").reset_index(drop=True)

# === INTERPRETATION LOGIC ===
def interpret_bias(curr, window):
    va_range = curr["VAH"] - curr["VAL"]
    center = curr["VAL"] + va_range / 2
    bias = []
    reco = []

    # Structural analysis
    if abs(curr["POC"] - center) < va_range * 0.1:
        bias.append("POC near center → balanced")
    if curr["POC"] < window["POC"].mean():
        bias.append("POC falling → bearish migration")
    if abs(curr["VWAP"] - curr["POC"]) < va_range * 0.1:
        bias.append("VWAP ≈ POC → fair value consensus")
    if curr["Close"] < curr["VAL"] and curr["Close"] > curr["Open"]:
        bias.append("Failed breakdown (below VAL rejected)")
    if curr["Close"] > curr["VAL"] and abs(curr["Close"] - curr["VAL"]) < va_range * 0.2:
        reco.append("🟢 Reversal: VAL tested and rejected")
    if abs(curr["VWAP"] - curr["POC"]) < va_range * 0.1:
        reco.append("📯 POC ≈ VWAP → fade extremes")

    # Volume and trade count logic
    avg_vol = window["Volume"].mean()
    if curr["Volume"] > 1.3 * avg_vol:
        bias.append("High volume day → expansion or strong interest")
        if abs(curr["Close"] - curr["Open"]) < va_range * 0.2:
            bias.append("Volume spike but small body → absorption")
            reco.append("Fade reaction unless confirmed")

    avg_trades = window["Trades"].mean()
    if curr["Trades"] < 0.8 * avg_trades and abs(curr["Close"] - curr["Open"]) > va_range * 0.5:
        bias.append("Large range but low trade count → inefficient move")
        reco.append("Caution: may reverse if no follow-through")

    if curr["Volume"] < 0.7 * avg_vol and va_range < (window["VAH"] - window["VAL"]).mean() * 0.7:
        bias.append("Low volume + narrow VA → coiling")
        reco.append("Watch for breakout or trap behavior")

    return bias, reco

# === MAIN DISPLAY ===
if uploaded_file:
    df = clean_df(pd.read_csv(uploaded_file))
    if not df.empty:
        dates = df["Date"].dt.date.unique()
        selected_date = st.date_input("Select Candle Date", value=dates[-1], min_value=min(dates), max_value=max(dates))
        lookback = st.slider("Lookback candles", 3, 10, 5)

        if selected_date not in df["Date"].dt.date.values:
            st.warning("Date not in dataset.")
        else:
            idx = df[df["Date"].dt.date == selected_date].index[0]
            if idx < lookback:
                st.warning("Not enough lookback candles.")
            else:
                window = df.iloc[idx - lookback:idx]
                curr = df.iloc[idx]
                bias, reco = interpret_bias(curr, window)

                st.markdown("### 🧠 Bias Interpretation")
                for b in bias:
                    st.write("- " + b)
                st.markdown("### 🎯 Trade Recommendation")
                for r in reco:
                    st.write("- " + r)
                st.markdown("### 📌 Key Price Levels")
                st.code(f"VAL: {curr['VAL']:.2f} | POC: {curr['POC']:.2f} | VAH: {curr['VAH']:.2f} | VWAP: {curr['VWAP']:.2f} | Close: {curr['Close']:.2f} | Volume: {curr['Volume']:.0f} | Trades: {curr['Trades']:.0f}")

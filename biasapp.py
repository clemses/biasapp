import streamlit as st
import pandas as pd

st.title("📊 Bias & Trade App – 60m Pattern Scanner")

st.sidebar.header("📁 Upload 60-Min Chart File")
file_60m = st.sidebar.file_uploader("Upload 60-Min Chart CSV", type=["csv", "txt"])

def load_data(file):
    try:
        df = pd.read_csv(file)
    except:
        file.seek(0)
        df = pd.read_csv(file, delimiter='\t')
    return df

def clean_and_format(df):
    df.columns = df.columns.str.strip().str.replace('"', '')
    df.rename(columns={
        "Last": "Close",
        "Point of Control": "POC",
        "Value Area High Value": "VAH",
        "Value Area Low Value": "VAL",
        "Volume Weighted Average Price": "VWAP"
    }, inplace=True)
    df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    return df.dropna(subset=["Datetime", "POC", "VAH", "VAL", "Close"]).sort_values("Datetime").reset_index(drop=True)

def scan_structures(df, lookback, tolerance):
    results = []
    for i in range(lookback, len(df)):
        window = df.iloc[i - lookback:i + 1].copy()
        poc_rising = (window["POC"].diff() > 0).fillna(True)
        poc_falling = (window["POC"].diff() < 0).fillna(True)
        higher_lows = (window["Low"] > window["Low"].shift(1)).fillna(True)
        lower_highs = (window["High"] < window["High"].shift(1)).fillna(True)
        va_width = window["VAH"] - window["VAL"]
        va_narrow = va_width < va_width.rolling(lookback).median() * 0.7

        def pass_with_tolerance(series):
            return series.sum() >= len(series) - tolerance

        if pass_with_tolerance(poc_rising) and pass_with_tolerance(higher_lows):
            results.append({
                "Start": window.iloc[0]["Datetime"],
                "End": window.iloc[-1]["Datetime"],
                "Pattern": "🟢 Bullish Structure",
                "Entry (last close)": window.iloc[-1]["Close"]
            })
        elif pass_with_tolerance(poc_falling) and pass_with_tolerance(lower_highs):
            results.append({
                "Start": window.iloc[0]["Datetime"],
                "End": window.iloc[-1]["Datetime"],
                "Pattern": "🔴 Bearish Structure",
                "Entry (last close)": window.iloc[-1]["Close"]
            })
        elif pass_with_tolerance(va_narrow.fillna(False)):
            results.append({
                "Start": window.iloc[0]["Datetime"],
                "End": window.iloc[-1]["Datetime"],
                "Pattern": "⚠️ Consolidation (Narrow VA)",
                "Entry (last close)": window.iloc[-1]["Close"]
            })

    return pd.DataFrame(results)

if file_60m:
    df = clean_and_format(load_data(file_60m))

    st.subheader("🧠 Structural Pattern Recognition")
    lookback = st.slider("🔁 Lookback Window (candles)", 3, 12, 6)
    tolerance = st.slider("⚙️ Pattern Tolerance (how many violations allowed)", 0, 3, 1)

    pattern_df = scan_structures(df, lookback, tolerance)

    if not pattern_df.empty:
        st.success(f"✅ {len(pattern_df)} patterns detected.")
        st.dataframe(pattern_df)
    else:
        st.warning("No qualifying patterns found with the current settings.")

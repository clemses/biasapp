import streamlit as st
import pandas as pd

st.title("📊 Bias & Trade App – With Pattern Recognition")

st.sidebar.header("📁 Upload Files")
file_60m = st.sidebar.file_uploader("Upload 60-Min Chart File", type=["csv", "txt"])

def load_file(file):
    try:
        df = pd.read_csv(file)
    except:
        file.seek(0)
        df = pd.read_csv(file, delimiter='\t')
    return df

def clean_df(df):
    df.columns = df.columns.str.strip().str.replace('"', '')
    df.rename(columns={
        "Open": "Open", "High": "High", "Low": "Low", "Last": "Close", "Date": "Date", "Time": "Time",
        "Point of Control": "POC", "Value Area High Value": "VAH", "Value Area Low Value": "VAL",
        "Volume Weighted Average Price": "VWAP"
    }, inplace=True)
    df["Datetime"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), errors="coerce")
    df = df.dropna(subset=["Datetime", "Open", "High", "Low", "Close", "POC", "VAH", "VAL", "VWAP"]).sort_values("Datetime")
    return df.reset_index(drop=True)

def analyze_pattern(df, selected_time, lookback):
    if selected_time not in df["Datetime"].values:
        return [], "⚠️ Selected time not in dataset."
    idx = df[df["Datetime"] == selected_time].index[0]
    if idx < lookback:
        return [], "⚠️ Not enough candles before selected time for this lookback range."

    window = df.iloc[idx - lookback:idx+1].copy()
    notes = []
    va_width = window["VAH"] - window["VAL"]
    window["VA Width"] = va_width
    window["POC Rising"] = window["POC"].diff() > 0
    window["POC Falling"] = window["POC"].diff() < 0
    window["Higher Low"] = window["Low"] > window["Low"].shift(1)
    window["Lower High"] = window["High"] < window["High"].shift(1)
    window["VA Narrow"] = va_width < va_width.rolling(lookback).median() * 0.7

    if all(window["POC Rising"].fillna(True)) and all(window["Higher Low"].fillna(True)):
        notes.append("🟢 Bullish: Rising POC and Higher Lows across selected window.")
    if all(window["POC Falling"].fillna(True)) and all(window["Lower High"].fillna(True)):
        notes.append("🔴 Bearish: Falling POC and Lower Highs across selected window.")
    if all(window["VA Narrow"].fillna(False)):
        notes.append("⚠️ Consolidation: Narrow Value Areas, potential breakout setup.")

    return notes, window

if file_60m:
    df = clean_df(load_file(file_60m))
    st.subheader("🔍 Structural Pattern Recognition")

    options = df["Datetime"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    selected_label = st.selectbox("Select the last candle to analyze", options)
    selected_time = pd.to_datetime(selected_label)
    lookback = st.slider("How many candles to look back?", min_value=2, max_value=12, value=4)

    notes, pattern_window = analyze_pattern(df, selected_time, lookback)

    if notes:
        st.markdown("### 🧠 Pattern Analysis Results:")
        for note in notes:
            st.markdown(f"- {note}")
        st.dataframe(pattern_window[["Datetime", "Open", "High", "Low", "Close", "POC", "VAH", "VAL", "VWAP"]])
    else:
        st.warning("No strong structural pattern found in selected range.")

import streamlit as st
import pandas as pd

st.set_page_config(page_title="BiasApp 📈", layout="wide")
st.title("🧠 Bias Decision Support App")

# --- Sidebar Uploads ---
st.sidebar.header("📁 Upload Data Files")
daily_file = st.sidebar.file_uploader("Upload Daily Chart CSV", type=["csv", "txt"])
h4_file = st.sidebar.file_uploader("Upload 4H Chart CSV", type=["csv", "txt"])
h1_file = st.sidebar.file_uploader("Upload 60-Min Chart CSV", type=["csv", "txt"])

# --- Utility Functions ---
def load_csv(file):
    try:
        df = pd.read_csv(file)
    except:
        file.seek(0)
        df = pd.read_csv(file, delimiter='\t')
    return df

def preprocess(df):
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

# --- DAILY ANALYSIS ---
if daily_file:
    st.header("📊 Daily Bias Analysis")
    df_daily = preprocess(load_csv(daily_file))

    recent = df_daily.iloc[-1]
    prior = df_daily.iloc[-2]

    st.write("**Last Close vs Previous Day POC**")
    st.write(f"🟢 Bullish Bias" if recent["Close"] > prior["POC"] else "🔴 Bearish Bias")

    st.write("**POC Movement**")
    st.write(f"⬆️ Rising" if recent["POC"] > prior["POC"] else "⬇️ Falling")

# --- 4H ANALYSIS ---
if h4_file:
    st.header("⏱️ 4H Bias Comparison")
    df_h4 = preprocess(load_csv(h4_file))

    candle_choice = st.selectbox("Choose recent 4H candle to analyze", df_h4["Datetime"].dt.strftime("%Y-%m-%d %H:%M"))
    idx = df_h4[df_h4["Datetime"].dt.strftime("%Y-%m-%d %H:%M") == candle_choice].index[0]
    compare_to = st.radio("Compare to:", ["Previous Candle", "2 Back"])
    ref_idx = idx - 1 if compare_to == "Previous Candle" else idx - 2

    if ref_idx >= 0:
        current = df_h4.iloc[idx]
        ref = df_h4.iloc[ref_idx]
        st.write("**Close vs Ref POC**")
        st.write(f"🟢 Bullish" if current["Close"] > ref["POC"] else "🔴 Bearish")

        st.write("**POC Movement**")
        st.write(f"⬆️ Upward" if current["POC"] > ref["POC"] else "⬇️ Downward")

# --- 60-MIN STRUCTURE SCAN ---
if h1_file:
    st.header("🔍 60-Min Structural Pattern Scanner")
    df_h1 = preprocess(load_csv(h1_file))

    lookback = st.slider("🔁 Lookback Window (candles)", 3, 12, 6)
    tolerance = st.slider("⚙️ Tolerance (violations allowed)", 0, 3, 1)

    results = []
    for i in range(lookback, len(df_h1)):
        win = df_h1.iloc[i - lookback:i + 1].copy()
        poc_rise = (win["POC"].diff() > 0).fillna(True)
        poc_fall = (win["POC"].diff() < 0).fillna(True)
        hi_low = (win["Low"] > win["Low"].shift(1)).fillna(True)
        lo_hi = (win["High"] < win["High"].shift(1)).fillna(True)
        va_w = win["VAH"] - win["VAL"]
        va_n = va_w < va_w.rolling(lookback).median() * 0.7

        def tolerate(series):
            return series.sum() >= len(series) - tolerance

        if tolerate(poc_rise) and tolerate(hi_low):
            results.append({
                "Start": win.iloc[0]["Datetime"],
                "End": win.iloc[-1]["Datetime"],
                "Pattern": "🟢 Bullish Structure",
                "Entry (Close)": win.iloc[-1]["Close"]
            })
        elif tolerate(poc_fall) and tolerate(lo_hi):
            results.append({
                "Start": win.iloc[0]["Datetime"],
                "End": win.iloc[-1]["Datetime"],
                "Pattern": "🔴 Bearish Structure",
                "Entry (Close)": win.iloc[-1]["Close"]
            })
        elif tolerate(va_n.fillna(False)):
            results.append({
                "Start": win.iloc[0]["Datetime"],
                "End": win.iloc[-1]["Datetime"],
                "Pattern": "⚠️ Consolidation Zone",
                "Entry (Close)": win.iloc[-1]["Close"]
            })

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        st.success(f"✅ {len(result_df)} patterns found.")
        st.dataframe(result_df)
    else:
        st.warning("No structural patterns found.")

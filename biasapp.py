import streamlit as st
import pandas as pd
from datetime import date

st.title("📈 Sierra Chart Bias Comparator – Daily & 4H View")

uploaded_file = st.file_uploader("Upload Sierra Chart .txt/.csv file (with Date, Open, Close, VAL, VAH, POC)", type=["txt", "csv"])

def interpret_bias(current, reference):
    va_width = current["VAH"] - current["VAL"]
    poc_position = (current["POC"] - current["VAL"]) / va_width if va_width else 0.5
    close_vs_poc = current["Close"] - current["POC"]
    poc_vs_ref_poc = current["POC"] - reference["POC"]
    close_vs_ref_close = current["Close"] - reference["Close"]

    if current["Close"] > current["POC"] and poc_position > 0.66 and current["POC"] > reference["POC"]:
        return "📈 Bullish Initiative + Value Higher"
    elif current["Close"] < current["POC"] and poc_position < 0.33 and current["POC"] < reference["POC"]:
        return "📉 Bearish Initiative + Value Lower"
    elif current["Close"] > reference["POC"] and current["POC"] > reference["POC"] and close_vs_ref_close > 0:
        return "📈 Trend Continuation – Bullish Bias"
    elif current["Close"] < reference["POC"] and current["POC"] < reference["POC"] and close_vs_ref_close < 0:
        return "📉 Trend Continuation – Bearish Bias"
    elif abs(close_vs_poc) < (va_width * 0.15) and va_width < 10:
        return "⚖️ Balanced Auction – fade extremes"
    elif va_width >= 15 and abs(close_vs_poc) > (va_width * 0.5):
        return "⚠️ Transitional / Volatile Day – caution"
    else:
        return "➖ No clear bias – wait for intraday confirmation"

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.replace('"', '')
    df.rename(columns={
        "Open": "Open",
        "Last": "Close",
        "Point of Control": "POC",
        "Value Area High Value": "VAH",
        "Value Area Low Value": "VAL",
        "Date": "Date"
    }, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)

    st.success("✅ File loaded and processed.")
    st.markdown("## 🗓️ Daily Bias Comparison")
    date_options = df["Date"].dt.date.astype(str).tolist()
    selected_dates = st.multiselect("Select two dates for daily comparison", options=date_options, default=date_options[-2:])

    if len(selected_dates) == 2:
        daily_df = df[df["Date"].dt.date.astype(str).isin(selected_dates)].sort_values("Date")
        today, prev = daily_df.iloc[1], daily_df.iloc[0]
        bias_result = interpret_bias(today, prev)

        st.markdown(f"### 🧭 Daily Bias: **{bias_result}**")
        st.dataframe(daily_df[["Date", "Open", "Close", "VAL", "VAH", "POC"]])

    st.markdown("---")
    st.markdown("## ⏱️ 4-Hour Bias Comparison")
    st.info("This section compares the most recent 4H candle to either the previous or the one before that.")

    last_n = st.selectbox("Compare last 4H candle to:", options=[1, 2], format_func=lambda x: f"{x}-back")
    if len(df) > last_n + 1:
        current_4h = df.iloc[-1]
        reference_4h = df.iloc[-(last_n + 1)]

        bias_4h = interpret_bias(current_4h, reference_4h)
        st.markdown(f"### 🧭 4H Bias ({current_4h['Date'].date()} vs {reference_4h['Date'].date()}): **{bias_4h}**")

        st.dataframe(pd.DataFrame([reference_4h, current_4h])[["Date", "Open", "Close", "VAL", "VAH", "POC"]])
    else:
        st.warning("Not enough rows in the file to compare 4H bias with that setting.")
else:
    st.info("Please upload a valid Sierra Chart export file with necessary columns.")

import streamlit as st
import pandas as pd

st.title("📊 Bias App – Compare Daily and 4H Bias from Separate Sierra Chart Files")

st.sidebar.header("📁 Upload Files")

daily_file = st.sidebar.file_uploader("Upload Daily File (CSV/TXT)", type=["csv", "txt"], key="daily")
h4_file = st.sidebar.file_uploader("Upload 4H File (CSV/TXT)", type=["csv", "txt"], key="4h")

def clean_df(df):
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
    return df

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

if daily_file:
    st.subheader("🗓️ Daily Bias Analysis")
    daily_df = clean_df(pd.read_csv(daily_file))
    date_options = daily_df["Date"].dt.date.astype(str).tolist()
    selected = st.multiselect("Select two dates for comparison", date_options, default=date_options[-2:])

    if len(selected) == 2:
        today, prev = daily_df[daily_df["Date"].dt.date.astype(str).isin(selected)].sort_values("Date").iloc[-2:]
        bias = interpret_bias(today, prev)
        st.markdown(f"### 🧭 Daily Bias: **{bias}**")
        st.dataframe(pd.DataFrame([prev, today])[["Date", "Open", "Close", "VAL", "VAH", "POC"]])
    else:
        st.info("Please select exactly 2 dates.")

if h4_file:
    st.subheader("⏱️ 4H Bias Analysis")
    h4_df = clean_df(pd.read_csv(h4_file))

    if len(h4_df) >= 3:
        last_n = st.selectbox("Compare last 4H candle to:", options=[1, 2], format_func=lambda x: f"{x}-back")
        current_4h = h4_df.iloc[-1]
        reference_4h = h4_df.iloc[-(last_n + 1)]

        bias = interpret_bias(current_4h, reference_4h)
        st.markdown(f"### 🧭 4H Bias: **{bias}**")
        st.dataframe(pd.DataFrame([reference_4h, current_4h])[["Date", "Open", "Close", "VAL", "VAH", "POC"]])
    else:
        st.warning("You need at least 3 rows in the 4H file for comparison.")

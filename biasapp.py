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
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date", "Open", "Close", "POC", "VAH", "VAL"], inplace=True)
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
    if len(daily_df) >= 2:
        date_options = daily_df["Date"].dt.date.astype(str).tolist()
        selected = st.multiselect("Select two dates for comparison (Daily)", date_options, default=date_options[-2:])

        if len(selected) == 2:
            selection = daily_df[daily_df["Date"].dt.date.astype(str).isin(selected)].sort_values("Date")
            if len(selection) == 2:
                today, prev = selection.iloc[1], selection.iloc[0]
                bias = interpret_bias(today, prev)
                st.markdown(f"### 🧭 Daily Bias: **{bias}**")
                st.dataframe(selection[["Date", "Open", "Close", "VAL", "VAH", "POC"]])
        else:
            st.info("Please select exactly 2 dates.")
    else:
        st.warning("Daily file must contain at least 2 rows.")

if h4_file:
    st.subheader("⏱️ 4H Bias Analysis")
    h4_df = clean_df(pd.read_csv(h4_file))
    if len(h4_df) >= 3:
        date_options_4h = h4_df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
        selected_4h = st.multiselect("Select two 4H candles to compare", options=date_options_4h, default=date_options_4h[-2:])

        if len(selected_4h) == 2:
            selection_4h = h4_df[h4_df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S").isin(selected_4h)].sort_values("Date")
            if len(selection_4h) == 2:
                current_4h, reference_4h = selection_4h.iloc[1], selection_4h.iloc[0]
                bias_4h = interpret_bias(current_4h, reference_4h)
                st.markdown(f"### 🧭 4H Bias: **{bias_4h}**")
                st.dataframe(selection_4h[["Date", "Open", "Close", "VAL", "VAH", "POC"]])
        else:
            st.info("Please select exactly 2 4H candles.")
    else:
        st.warning("4H file must contain at least 3 rows.")

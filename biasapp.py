import streamlit as st
import pandas as pd

st.title("📊 Enhanced Bias App – With Rule-Based Market Signals")

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
        "Date": "Date",
        "Volume Weighted Average Price": "VWAP"
    }, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date", "Open", "Close", "POC", "VAH", "VAL"], inplace=True)
    df.sort_values("Date", inplace=True)
    return df

def interpret_bias(current, reference):
    notes = []
    va_width_today = current["VAH"] - current["VAL"]
    va_width_yesterday = reference["VAH"] - reference["VAL"]

    # POC Location
    poc_pos = (current["POC"] - current["VAL"]) / va_width_today if va_width_today else 0.5
    if poc_pos > 0.66:
        notes.append("POC near VAH → buyers dominant")
    elif poc_pos < 0.33:
        notes.append("POC near VAL → sellers dominant")
    else:
        notes.append("POC near center → balanced day")

    # POC Migration
    if current["POC"] > reference["POC"]:
        notes.append("POC rising → bullish migration")
    elif current["POC"] < reference["POC"]:
        notes.append("POC falling → bearish migration")

    # Value Area Width
    if va_width_today > va_width_yesterday * 1.3:
        notes.append("VA expanding → increasing volatility")
    elif va_width_today < va_width_yesterday * 0.7:
        notes.append("VA compressing → potential breakout setup")

    # VWAP relation to POC
    if "VWAP" in current and abs(current["VWAP"] - current["POC"]) < 3:
        notes.append("VWAP near POC → consensus")
    elif "VWAP" in current:
        notes.append("VWAP far from POC → divergence")

    # Failed Auction Detection
    if current["High"] > current["VAH"] and current["Close"] < current["VAH"]:
        notes.append("Failed breakout (high rejected)")
    if current["Low"] < current["VAL"] and current["Close"] > current["VAL"]:
        notes.append("Failed breakdown (low rejected)")

    # Volume-Based Confidence
    if current["Close"] > current["POC"] and current["Volume"] > reference["Volume"]:
        notes.append("Close above POC + higher volume → bullish confidence")
    elif current["Close"] < current["POC"] and current["Volume"] > reference["Volume"]:
        notes.append("Close below POC + higher volume → bearish confidence")

    return notes

def display_bias_analysis(df, label="Daily"):
    if len(df) >= 2:
        date_options = df["Date"].dt.date.astype(str).tolist()
        selected = st.multiselect(f"Select two dates for comparison ({label})", date_options, default=date_options[-2:])

        if len(selected) == 2:
            selection = df[df["Date"].dt.date.astype(str).isin(selected)].sort_values("Date")
            if len(selection) == 2:
                today, prev = selection.iloc[1], selection.iloc[0]
                notes = interpret_bias(today, prev)
                st.markdown(f"### 🧭 {label} Bias Notes:")
                for note in notes:
                    st.markdown(f"- {note}")
                st.dataframe(selection[["Date", "Open", "Close", "VAL", "VAH", "POC", "VWAP", "Volume"]])
        else:
            st.info("Please select exactly 2 dates.")

if daily_file:
    st.subheader("📅 Daily Bias Analysis")
    daily_df = clean_df(pd.read_csv(daily_file))
    display_bias_analysis(daily_df, "Daily")

if h4_file:
    st.subheader("🕓 4H Bias Analysis")
    h4_df = clean_df(pd.read_csv(h4_file))
    if len(h4_df) >= 3:
        date_options = h4_df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
        selected = st.multiselect("Select two 4H candles to compare", options=date_options, default=date_options[-2:])
        if len(selected) == 2:
            selection = h4_df[h4_df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S").isin(selected)].sort_values("Date")
            if len(selection) == 2:
                today, prev = selection.iloc[1], selection.iloc[0]
                notes = interpret_bias(today, prev)
                st.markdown("### 🧭 4H Bias Notes:")
                for note in notes:
                    st.markdown(f"- {note}")
                st.dataframe(selection[["Date", "Open", "Close", "VAL", "VAH", "POC", "VWAP", "Volume"]])

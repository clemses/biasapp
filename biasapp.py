import streamlit as st
import pandas as pd

st.title("📊 Bias & Trade App – With Sierra Chart TXT Support")

st.sidebar.header("📁 Upload Files")
daily_file = st.sidebar.file_uploader("Upload Daily File", type=["csv", "txt"])
h4_file = st.sidebar.file_uploader("Upload 4H File", type=["csv", "txt"])

def load_file(file):
    try:
        df = pd.read_csv(file)
    except:
        file.seek(0)
        df = pd.read_csv(file, delimiter='\t')  # Try tab-delimited
    return df

def clean_df(df):
    df.columns = df.columns.str.strip().str.replace('"', '')
    df.rename(columns={
        "Open": "Open", "Last": "Close", "Point of Control": "POC",
        "Value Area High Value": "VAH", "Value Area Low Value": "VAL",
        "Date": "Date", "Volume Weighted Average Price": "VWAP"
    }, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date", "Open", "Close", "POC", "VAH", "VAL"], inplace=True)
    df.sort_values("Date", inplace=True)
    return df

def interpret_bias(current, reference):
    notes = []
    va_width_today = current["VAH"] - current["VAL"]
    va_width_yesterday = reference["VAH"] - reference["VAL"]

    poc_pos = (current["POC"] - current["VAL"]) / va_width_today if va_width_today else 0.5
    if poc_pos > 0.66:
        notes.append("POC near VAH → buyers dominant")
    elif poc_pos < 0.33:
        notes.append("POC near VAL → sellers dominant")
    else:
        notes.append("POC near center → balanced")

    if current["POC"] > reference["POC"]:
        notes.append("POC rising → bullish migration")
    elif current["POC"] < reference["POC"]:
        notes.append("POC falling → bearish migration")

    if va_width_today > va_width_yesterday * 1.3:
        notes.append("VA expanding → volatility increasing")
    elif va_width_today < va_width_yesterday * 0.7:
        notes.append("VA compressing → breakout potential")

    if "VWAP" in current and abs(current["VWAP"] - current["POC"]) < 3:
        notes.append("VWAP ≈ POC → fair value consensus")
    elif "VWAP" in current:
        notes.append("VWAP far from POC → divergence")

    if current["High"] > current["VAH"] and current["Close"] < current["VAH"]:
        notes.append("Failed breakout (above VAH rejected)")
    if current["Low"] < current["VAL"] and current["Close"] > current["VAL"]:
        notes.append("Failed breakdown (below VAL rejected)")

    if current["Close"] > current["POC"] and current["Volume"] > reference["Volume"]:
        notes.append("Close above POC + rising volume → bullish conviction")
    elif current["Close"] < current["POC"] and current["Volume"] > reference["Volume"]:
        notes.append("Close below POC + rising volume → bearish conviction")

    return notes

def generate_trade_recommendations(current, reference):
    recs = []
    thin_zone = current["VAH"] - current["VAL"] < (reference["VAH"] - reference["VAL"]) * 0.6

    if current["Close"] > current["POC"] and current["POC"] > reference["POC"]:
        recs.append("🟢 Long bias: price closing above rising POC.")

    if current["Close"] < current["POC"] and current["POC"] < reference["POC"]:
        recs.append("🔴 Short bias: price closing below falling POC.")

    if current["High"] > current["VAH"] and current["Close"] < current["VAH"]:
        recs.append("🔴 Fade breakout: high rejected above VAH.")

    if current["Low"] < current["VAL"] and current["Close"] > current["VAL"]:
        recs.append("🟢 Reversal: VAL tested and rejected, watch for bounce.")

    if thin_zone:
        recs.append("⚠️ Thin volume area → whippy zone, wait for confirmation.")

    if abs(current["POC"] - current["VWAP"]) < 2:
        recs.append("⚖️ POC ≈ VWAP → balanced zone, fade extremes.")

    return recs

def display_analysis(df, label="Daily"):
    if len(df) >= 2:
        date_options = df["Date"].dt.date.astype(str).tolist()
        selected = st.multiselect(f"Select two {label} dates", date_options, default=date_options[-2:])
        if len(selected) == 2:
            sel = df[df["Date"].dt.date.astype(str).isin(selected)].sort_values("Date")
            today, prev = sel.iloc[1], sel.iloc[0]
            bias_notes = interpret_bias(today, prev)
            trade_recs = generate_trade_recommendations(today, prev)

            st.markdown(f"### 🧭 {label} Bias Interpretation")
            for n in bias_notes:
                st.markdown(f"- {n}")

            st.markdown(f"### 📌 {label} Trade Recommendations")
            for r in trade_recs:
                st.markdown(f"- {r}")

            st.dataframe(sel[["Date", "Open", "Close", "POC", "VAL", "VAH", "VWAP", "Volume"]])
        else:
            st.info("Please select exactly 2 dates.")

if daily_file:
    st.subheader("📅 Daily Bias & Trades")
    daily_df = clean_df(load_file(daily_file))
    display_analysis(daily_df, "Daily")

if h4_file:
    st.subheader("🕓 4H Bias & Trades")
    h4_df = clean_df(load_file(h4_file))
    display_analysis(h4_df, "4H")

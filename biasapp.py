
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bias Dashboard", layout="wide")
st.title("📊 Bias Dashboard – Structure + Volume & Time (Optional) + Export")

# === UPLOAD FILES ===
st.sidebar.header("📂 Upload CSVs")
daily_file = st.sidebar.file_uploader("Upload Daily CSV", type=["csv", "txt"])
fourh_file = st.sidebar.file_uploader("Upload 4H CSV", type=["csv", "txt"])

# === CLEAN DATA ===
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
    required = ['Date', 'Open', 'Close', 'POC', 'VAL', 'VAH', 'VWAP', 'Volume']
    df['Trades'] = df['Trades'] if 'Trades' in df.columns else None
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        return pd.DataFrame()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    for col in required[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'Trades' in df.columns:
        df['Trades'] = pd.to_numeric(df['Trades'], errors='coerce')
    return df.dropna(subset=['Date']).sort_values("Date").reset_index(drop=True)

# === SCORING + LOGIC ===
def interpret_bias(curr, window):
    va_range = curr["VAH"] - curr["VAL"]
    center = curr["VAL"] + va_range / 2
    summary = []
    reco = []
    score = 0

    if abs(curr["POC"] - center) < va_range * 0.1:
        summary.append("POC near center → balanced"); score += 1
    if curr["POC"] < window["POC"].mean():
        summary.append("POC falling → bearish migration"); score += 1
    if abs(curr["VWAP"] - curr["POC"]) < va_range * 0.1:
        summary.append("VWAP ≈ POC → fair value zone"); score += 1
        reco.append("📯 Fade extremes")

    if curr["Close"] < curr["VAL"] and curr["Close"] > curr["Open"]:
        summary.append("Failed breakdown (below VAL rejected)"); score += 1
    if curr["Close"] > curr["VAL"] and abs(curr["Close"] - curr["VAL"]) < va_range * 0.2:
        reco.append("🟢 Reversal: VAL tested and rejected"); score += 1

    avg_vol = window["Volume"].mean()
    if curr["Volume"] > 1.3 * avg_vol:
        summary.append("High volume → expansion or strong interest"); score += 1
        if abs(curr["Close"] - curr["Open"]) < va_range * 0.2:
            summary.append("Volume spike but small body → absorption")
            reco.append("Fade unless confirmed")

    if 'Trades' in curr and curr['Trades'] and window['Trades'].notna().sum() > 0:
        avg_trades = window["Trades"].mean()
        if curr["Trades"] < 0.8 * avg_trades and abs(curr["Close"] - curr["Open"]) > va_range * 0.5:
            summary.append("Large range but low trade count → inefficient move")
            reco.append("⚠️ Potential fade setup")

    return summary, reco, score

# === DISPLAY LOGIC ===
def analyze(df, tf_name):
    st.subheader(f"📈 {tf_name} Bias Interpretation")
    dates = df["Date"].dt.date.unique()
    selected = st.date_input(f"Select {tf_name} Candle", value=dates[-1], key=tf_name)
    lookback = st.slider(f"Lookback for {tf_name}", 3, 10, 5, key=f"{tf_name}_slider")

    if selected not in df["Date"].dt.date.values:
        st.warning("Date not in dataset."); return

    idx = df[df["Date"].dt.date == selected].index[0]
    if idx < lookback:
        st.warning("Not enough candles for lookback."); return

    window = df.iloc[idx - lookback:idx]
    curr = df.iloc[idx]
    summary, reco, score = interpret_bias(curr, window)

    st.markdown("### 🧠 Interpretation")
    for s in summary: st.write("- " + s)
    st.markdown("### 🎯 Trade Recommendation")
    for r in reco: st.write("- " + r)

    st.markdown("### 📌 Key Levels")
    st.code(f"VAL: {curr['VAL']:.2f} | POC: {curr['POC']:.2f} | VAH: {curr['VAH']:.2f} | VWAP: {curr['VWAP']:.2f} | Close: {curr['Close']:.2f} | Volume: {curr['Volume']:.0f}")

    st.markdown("### 🧾 Journal Export")
    export = pd.DataFrame([{
        "Date": curr["Date"].date(),
        "Timeframe": tf_name,
        "Score": score,
        "Close": curr["Close"],
        "POC": curr["POC"],
        "VAL": curr["VAL"],
        "VAH": curr["VAH"],
        "VWAP": curr["VWAP"],
        "Volume": curr["Volume"],
        "Summary": "; ".join(summary),
        "Recommendation": "; ".join(reco)
    }])
    st.dataframe(export)
    st.download_button("📥 Download Summary", export.to_csv(index=False).encode('utf-8'), file_name=f"{tf_name}_bias_summary.csv")

# === MAIN EXECUTION ===
if daily_file:
    df_daily = clean_df(pd.read_csv(daily_file))
    if not df_daily.empty:
        analyze(df_daily, "Daily")

if fourh_file:
    df_4h = clean_df(pd.read_csv(fourh_file))
    if not df_4h.empty:
        analyze(df_4h, "4H")

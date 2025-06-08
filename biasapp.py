
from datetime import datetime
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Bias Dashboard – Interpretive Mode", layout="wide")
st.title("📊 Bias Dashboard – Bias Force, Visualization, Key Levels & Interpretation")

# === FILE UPLOAD ===
st.sidebar.header("📂 Upload CSV Files")
daily_file = st.sidebar.file_uploader("Upload Daily CSV", type=["csv", "txt"])

# === CLEAN FUNCTION ===
def clean_df(df):
    df.columns = df.columns.str.strip()
    col_map = {
        'Last': 'Close',
        'Point of Control': 'POC',
        'Value Area Low Value': 'VAL',
        'Value Area High Value': 'VAH',
        'Volume Weighted Average Price': 'VWAP'
    }
    df = df.rename(columns=col_map)
    required = ['Date', 'Open', 'Close', 'POC', 'VAL', 'VAH', 'VWAP']
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        return pd.DataFrame()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    for col in required[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna().sort_values("Date").reset_index(drop=True)

# === BIAS SCORING ===
def score_bias(row):
    range_va = row["VAH"] - row["VAL"]
    vwap_dist = abs(row["VWAP"] - row["POC"])
    center_dist = abs(row["POC"] - (row["VAL"] + range_va / 2))
    score = 0
    if center_dist < range_va * 0.15:
        score += 1
    if vwap_dist < range_va * 0.1:
        score += 1
    if abs(row["Close"] - row["VAL"]) < range_va * 0.15:
        score += 1
    if abs(row["Close"] - row["VAH"]) < range_va * 0.15:
        score += 1
    if row["Close"] < row["VAL"]:
        score += 1
    if row["Close"] > row["VAH"]:
        score += 1
    return score

# === VISUALIZATION ===
def show_plot(data):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data["Date"], data["POC"], label="POC", linewidth=2)
    ax.plot(data["Date"], data["VAL"], label="VAL", linestyle="--")
    ax.plot(data["Date"], data["VAH"], label="VAH", linestyle="--")
    ax.plot(data["Date"], data["Close"], label="Close", color="black")
    ax.plot(data["Date"], data["VWAP"], label="VWAP", linestyle="dotted")
    colors = ['green' if s >= 4 else 'orange' if s == 3 else 'red' for s in data["BiasStrength"]]
    for i, row in data.iterrows():
        ax.axvline(x=row["Date"], color=colors[i], alpha=0.3, linewidth=5)
    ax.legend()
    ax.set_title("Bias Zone Visualization with Strength")
    ax.set_ylabel("Price")
    ax.grid(True)
    st.pyplot(fig)

# === INTERPRETATION PANEL ===
def interpret_force(score):
    if score >= 4:
        return "🟢 Strong directional bias. Watch for commitment or breakout follow-through."
    elif score == 3:
        return "🟠 Moderate setup. Potential but requires confirmation."
    else:
        return "🔴 Weak/neutral. Wait for clearer structure or reaction."

# === MAIN LOGIC ===
if daily_file:
    df = clean_df(pd.read_csv(daily_file))
    if not df.empty:
        df["BiasStrength"] = df.apply(score_bias, axis=1)
        recent = df.tail(10).reset_index(drop=True)
        st.subheader("🔍 Recent Daily Bias Strength Summary")
        st.dataframe(recent[["Date", "Close", "POC", "VAL", "VAH", "VWAP", "BiasStrength"]])
        show_plot(recent)

        st.subheader("🧠 Market Interpretation and Guidance")
        latest = recent.iloc[-1]
        force = interpret_force(latest["BiasStrength"])
        st.markdown(f"**Bias Score:** `{latest['BiasStrength']}` → {force}")
        st.markdown("### 📌 Key Price Levels")
        st.code(f"VAL: {latest['VAL']:.2f} | POC: {latest['POC']:.2f} | VAH: {latest['VAH']:.2f} | VWAP: {latest['VWAP']:.2f} | Close: {latest['Close']:.2f}")

        st.markdown("### 🔭 What to Watch For")
        st.markdown("""
- **Volume spikes** at VAL/VAH → strong rejection or breakout.
- **Fast push through levels** → directional conviction or stop runs.
- **Long dwell time** at VAL/VAH → market in balance, indecision.
- **Fade extremes** when POC ≈ VWAP with no expansion.
- **Bias force >= 4** → trade with momentum.
""")

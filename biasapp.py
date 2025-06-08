
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 Full Multi-Timeframe Bias Dashboard – Daily, 4H, 30min")

st.markdown("""
This dashboard provides:
- 3-day Daily bias tracking
- Recent 4H momentum shifts
- 30min live structure and volume shifts
- Combined session bias output
- Visual timeline of price/POC/VWAP across timeframes
""")

daily_file = st.file_uploader("📅 Upload Daily CSV", type=["csv"])
h4_file = st.file_uploader("🕓 Upload 4H CSV", type=["csv"])
min30_file = st.file_uploader("🕧 Upload 30min CSV", type=["csv"])

def clean(upload_file, suffix):
    df = pd.read_csv(upload_file)
    df.columns = [c.strip() for c in df.columns]
    df['Date'] = df['Date'].astype(str)
    df['Time'] = df['Time'].astype(str) if 'Time' in df.columns else '00:00:00'
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
    df = df.sort_values("Datetime").drop_duplicates(subset="Datetime")
    keep = ['Datetime', 'Last', 'Volume', 'Point of Control', 'Value Area High Value', 'Value Area Low Value', 'Volume Weighted Average Price']
    df = df[[c for c in keep if c in df.columns]]
    df.rename(columns={c: f"{c}_{suffix}" for c in df.columns if c != 'Datetime'}, inplace=True)
    df = df.loc[:, ~df.columns.duplicated()]
    return df

def plot_bias_timeline(df, label):
    st.markdown(f"### 📈 {label} Timeline – Last, POC, VWAP")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['Datetime'], df[f'Last_{label}'], label='Price', linewidth=1.5)
    ax.plot(df['Datetime'], df[f'Point of Control_{label}'], label='POC', linestyle='--')
    ax.plot(df['Datetime'], df[f'Volume Weighted Average Price_{label}'], label='VWAP', linestyle=':')
    ax.legend()
    ax.set_title(f"{label} Price Structure")
    ax.set_xlabel("Datetime")
    ax.set_ylabel("Price")
    st.pyplot(fig)

def final_bias_summary(daily_bias, h4_bias, min30_trend):
    st.markdown("## 🧠 Final Bias Map for Session")
    summary = (
        f"- 📅 Daily Bias: {daily_bias}\n"
        f"- 🕓 4H Bias: {h4_bias}\n"
        f"- 🕧 30min Context: {min30_trend}"
    )
    st.code(summary)

    if daily_bias == "STRONG BULLISH" and h4_bias == "4H Bullish Bias":
        st.success("✅ Combined Session Bias: HIGH CONFIDENCE LONG")
    elif daily_bias == "STRONG BEARISH" and h4_bias == "4H Bearish Bias":
        st.error("🚨 Combined Session Bias: HIGH CONFIDENCE SHORT")
    else:
        st.warning("🟡 Combined Bias: MIXED or ROTATION ZONE")

if daily_file and h4_file and min30_file:
    try:
        df_d = clean(daily_file, "D")
        df_h = clean(h4_file, "H")
        df_m = clean(min30_file, "M")

        df_d['DateOnly'] = df_d['Datetime'].dt.date
        latest_d = df_d.groupby('DateOnly').tail(1).sort_values('DateOnly').tail(3).reset_index(drop=True)
        poc_trend = latest_d['Point of Control_D'].is_monotonic_increasing
        vwaps = (latest_d['Volume Weighted Average Price_D'] > latest_d['Point of Control_D']).sum()
        closes_above_vah = (latest_d['Last_D'] > latest_d['Value Area High Value_D']).sum()
        closes_below_val = (latest_d['Last_D'] < latest_d['Value Area Low Value_D']).sum()
        if poc_trend and vwaps >= 2 and closes_above_vah >= 2:
            daily_bias = "STRONG BULLISH"
        elif closes_below_val >= 2 and not poc_trend:
            daily_bias = "STRONG BEARISH"
        else:
            daily_bias = "NEUTRAL"

        df_h['RoundedTime'] = df_h['Datetime'].dt.floor('4H')
        recent_h = df_h.groupby('RoundedTime').tail(1).sort_values('RoundedTime').tail(6)
        h_vwap_poc = (recent_h['Volume Weighted Average Price_H'] > recent_h['Point of Control_H']).sum()
        h_above_vah = (recent_h['Last_H'] > recent_h['Value Area High Value_H']).sum()
        h_below_val = (recent_h['Last_H'] < recent_h['Value Area Low Value_H']).sum()
        if h_vwap_poc >= 4 and h_above_vah >= 2:
            h4_bias = "4H Bullish Bias"
        elif h_below_val >= 2:
            h4_bias = "4H Bearish Bias"
        else:
            h4_bias = "4H Neutral"

        df_m_recent = df_m.sort_values('Datetime').tail(5)
        delta_last = df_m_recent['Last_M'].iloc[-1] - df_m_recent['Last_M'].iloc[0]
        delta_vwap = df_m_recent['Volume Weighted Average Price_M'].iloc[-1] - df_m_recent['Volume Weighted Average Price_M'].iloc[0]
        if delta_last > 5 and delta_vwap > 3:
            min30_trend = "Short-term Upswing"
        elif delta_last < -5 and delta_vwap < -3:
            min30_trend = "Short-term Downswing"
        else:
            min30_trend = "Flat / Choppy"

        plot_bias_timeline(df_d.tail(30), "D")
        plot_bias_timeline(df_h.tail(30), "H")
        plot_bias_timeline(df_m.tail(50), "M")

        final_bias_summary(daily_bias, h4_bias, min30_trend)

    except Exception as e:
        st.error(f"Processing error: {e}")
else:
    st.info("Please upload all three files (Daily, 4H, 30min) to begin.")

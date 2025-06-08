
import streamlit as st
import pandas as pd

st.set_page_config(layout="centered")
st.title("📋 Multi-Timeframe Bias Scanner – Configurable & Text-Only")

st.markdown("Upload your Sierra Chart exports for Daily, 4H, and 30min. Configure bias thresholds below.")

# === Threshold controls ===
st.sidebar.header("🔧 Bias Threshold Settings")

poc_up_days = st.sidebar.slider("POC up days (Daily)", 1, 3, 2)
vwaps_above_poc = st.sidebar.slider("VWAP > POC days (Daily)", 0, 3, 2)
closes_above_vah = st.sidebar.slider("Closes above VAH (Daily)", 0, 3, 2)
closes_below_val = st.sidebar.slider("Closes below VAL (Daily)", 0, 3, 2)

h4_winning_vwaps = st.sidebar.slider("4H VWAP > POC bars", 0, 6, 4)
h4_above_vah = st.sidebar.slider("4H closes above VAH", 0, 6, 2)
h4_below_val = st.sidebar.slider("4H closes below VAL", 0, 6, 2)

min_last_threshold = st.sidebar.slider("30min ΔPrice Threshold", -20, 20, 5)
min_vwap_threshold = st.sidebar.slider("30min ΔVWAP Threshold", -10, 10, 3)

# === Upload files ===
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

if daily_file and h4_file and min30_file:
    try:
        df_d = clean(daily_file, "D")
        df_h = clean(h4_file, "H")
        df_m = clean(min30_file, "M")

        # === Interactive date filter
        all_dates = df_d['Datetime'].dt.date.unique()
        if len(all_dates) >= 3:
    start_date = st.date_input("Start date", value=all_dates[-3], min_value=min(all_dates), max_value=max(all_dates))
    session_day = pd.to_datetime(start_date).date()
    lookback_date = session_day - pd.Timedelta(days=5)
    df_d = df_d[df_d['Datetime'].dt.date.between(lookback_date, session_day)]
    df_h = df_h[df_h['Datetime'].dt.date.between(lookback_date, session_day)]
    df_m = df_m[df_m['Datetime'].dt.date == session_day]
            start_date = st.date_input("Start date", value=all_dates[-3], min_value=min(all_dates), max_value=max(all_dates))
            df_d = df_d[df_d['Datetime'].dt.date >= start_date]
            df_h = df_h[df_h['Datetime'].dt.date >= start_date]
            df_m = df_m[df_m['Datetime'].dt.date >= start_date]

        # === Daily Bias
        df_d['DateOnly'] = df_d['Datetime'].dt.date
        latest_d = df_d.groupby('DateOnly').tail(1).sort_values('DateOnly').tail(3).reset_index(drop=True)
        poc_trend = latest_d['Point of Control_D'].is_monotonic_increasing
        vwaps = (latest_d['Volume Weighted Average Price_D'] > latest_d['Point of Control_D']).sum()
        above_vah = (latest_d['Last_D'] > latest_d['Value Area High Value_D']).sum()
        below_val = (latest_d['Last_D'] < latest_d['Value Area Low Value_D']).sum()
        if poc_trend and vwaps >= vwaps_above_poc and above_vah >= closes_above_vah:
            daily_bias = "STRONG BULLISH"
        elif below_val >= closes_below_val and not poc_trend:
            daily_bias = "STRONG BEARISH"
        else:
            daily_bias = "NEUTRAL"

        # === 4H Bias
        df_h['RoundedTime'] = df_h['Datetime'].dt.floor('4H')
        recent_h = df_h.groupby('RoundedTime').tail(1).sort_values('RoundedTime').tail(6)
        h_vwap_poc = (recent_h['Volume Weighted Average Price_H'] > recent_h['Point of Control_H']).sum()
        h_above_vah = (recent_h['Last_H'] > recent_h['Value Area High Value_H']).sum()
        h_below_val = (recent_h['Last_H'] < recent_h['Value Area Low Value_H']).sum()
        if h_vwap_poc >= h4_winning_vwaps and h_above_vah >= h4_above_vah:
            h4_bias = "4H Bullish Bias"
        elif h_below_val >= h4_below_val:
            h4_bias = "4H Bearish Bias"
        else:
            h4_bias = "4H Neutral"

        # === 30min Trend
        df_m_recent = df_m.sort_values('Datetime').tail(5)
        delta_last = df_m_recent['Last_M'].iloc[-1] - df_m_recent['Last_M'].iloc[0]
        delta_vwap = df_m_recent['Volume Weighted Average Price_M'].iloc[-1] - df_m_recent['Volume Weighted Average Price_M'].iloc[0]
        if delta_last > min_last_threshold and delta_vwap > min_vwap_threshold:
            min30_trend = "Short-term Upswing"
        elif delta_last < -min_last_threshold and delta_vwap < -min_vwap_threshold:
            min30_trend = "Short-term Downswing"
        else:
            min30_trend = "Flat / Choppy"

        # === Summary
        st.subheader("🧠 Final Session Bias")
        st.markdown(f"""
        **Daily Bias:** `{daily_bias}`  
        **4H Bias:** `{h4_bias}`  
        **30min Trend:** `{min30_trend}`
        """)

        if daily_bias == "STRONG BULLISH" and h4_bias == "4H Bullish Bias":
            st.success("✅ Session Bias: HIGH CONFIDENCE LONG")
        elif daily_bias == "STRONG BEARISH" and h4_bias == "4H Bearish Bias":
            st.error("🚨 Session Bias: HIGH CONFIDENCE SHORT")
        else:
            st.warning("🟡 Session Bias: MIXED or ROTATION")

    except Exception as e:
        st.error(f"Processing error: {e}")
else:
    st.info("Please upload Daily, 4H, and 30min files.")

import streamlit as st
import pandas as pd

st.set_page_config(layout="centered")
st.title("📋 Multi-Timeframe Bias Scanner – Text + Config + Backtest")

st.markdown("Upload your Sierra Chart exports for Daily, 4H, and 30min. Adjust thresholds and backtest recent bias performance.")

# === Sidebar Threshold Controls ===
st.sidebar.header("🔧 Threshold Settings")
poc_up_days = st.sidebar.slider("POC up days (Daily)", 1, 3, 2)
vwaps_above_poc = st.sidebar.slider("VWAP > POC days (Daily)", 0, 3, 2)
closes_above_vah = st.sidebar.slider("Closes above VAH (Daily)", 0, 3, 2)
closes_below_val = st.sidebar.slider("Closes below VAL (Daily)", 0, 3, 2)

h4_winning_vwaps = st.sidebar.slider("4H VWAP > POC bars", 0, 6, 4)
h4_above_vah = st.sidebar.slider("4H closes above VAH", 0, 6, 2)
h4_below_val = st.sidebar.slider("4H closes below VAL", 0, 6, 2)

min_last_threshold = st.sidebar.slider("30min ΔPrice Threshold", -20, 20, 5)
min_vwap_threshold = st.sidebar.slider("30min ΔVWAP Threshold", -10, 10, 3)

st.sidebar.header("📊 Backtest")
backtest_length = st.sidebar.slider("Backtest past N sessions", 3, 30, 10)

# === Upload Files ===
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

# === Bias Rule Functions ===
def get_daily_bias(d):
    poc_trend = d['Point of Control_D'].is_monotonic_increasing
    vwaps = (d['Volume Weighted Average Price_D'] > d['Point of Control_D']).sum()
    above_vah = (d['Last_D'] > d['Value Area High Value_D']).sum()
    below_val = (d['Last_D'] < d['Value Area Low Value_D']).sum()
    if poc_trend and vwaps >= vwaps_above_poc and above_vah >= closes_above_vah:
        return "STRONG BULLISH"
    elif below_val >= closes_below_val and not poc_trend:
        return "STRONG BEARISH"
    else:
        return "NEUTRAL"

def get_h4_bias(h):
    h_vwap_poc = (h['Volume Weighted Average Price_H'] > h['Point of Control_H']).sum()
    h_above_vah = (h['Last_H'] > h['Value Area High Value_H']).sum()
    h_below_val = (h['Last_H'] < h['Value Area Low Value_H']).sum()
    if h_vwap_poc >= h4_winning_vwaps and h_above_vah >= h4_above_vah:
        return "4H Bullish Bias"
    elif h_below_val >= h4_below_val:
        return "4H Bearish Bias"
    else:
        return "4H Neutral"

def get_min30_trend(m):
    delta_last = m['Last_M'].iloc[-1] - m['Last_M'].iloc[0]
    delta_vwap = m['Volume Weighted Average Price_M'].iloc[-1] - m['Volume Weighted Average Price_M'].iloc[0]
    if delta_last > min_last_threshold and delta_vwap > min_vwap_threshold:
        return "Short-term Upswing"
    elif delta_last < -min_last_threshold and delta_vwap < -min_vwap_threshold:
        return "Short-term Downswing"
    else:
        return "Flat / Choppy"

if daily_file and h4_file and min30_file:
    try:
        with st.spinner("Calculating bias signals..."):
            df_d = clean(daily_file, "D")
            df_h = clean(h4_file, "H")
            df_m = clean(min30_file, "M")

            df_d['DateOnly'] = df_d['Datetime'].dt.date
            recent_dates = df_d['DateOnly'].sort_values().unique()[-backtest_length:]
            bias_results = []

            for dt in recent_dates:
                daily_slice = df_d[df_d['DateOnly'] <= dt].groupby('DateOnly').tail(1).sort_values('DateOnly').tail(3)
                h4_slice = df_h[df_h['Datetime'].dt.date == dt]
                m30_slice = df_m[df_m['Datetime'].dt.date == dt].sort_values("Datetime").tail(5)

                if len(daily_slice) >= 3 and not h4_slice.empty and len(m30_slice) >= 5:
                    d_bias = get_daily_bias(daily_slice)
                    h_bias = get_h4_bias(h4_slice)
                    m_bias = get_min30_trend(m30_slice)

                    if d_bias == "STRONG BULLISH" and h_bias == "4H Bullish Bias":
                        outcome = "LONG"
                    elif d_bias == "STRONG BEARISH" and h_bias == "4H Bearish Bias":
                        outcome = "SHORT"
                    else:
                        outcome = "NEUTRAL"

                    # Simulated PnL direction: was close > open that day?
                    close = daily_slice['Last_D'].iloc[-1]
                    open_ = df_d[df_d['DateOnly'] == dt]['Last_D'].iloc[0]
                    pnl = "UP" if close > open_ else "DOWN"
                    correct = (outcome == "LONG" and pnl == "UP") or (outcome == "SHORT" and pnl == "DOWN")

                    bias_results.append({
                        "Date": dt,
                        "Daily": d_bias,
                        "4H": h_bias,
                        "30min": m_bias,
                        "Signal": outcome,
                        "Close↑": pnl,
                        "Correct": correct
                    })

            result_df = pd.DataFrame(bias_results)
            st.subheader("📅 Latest Bias Signal")
            st.write(result_df.tail(1).drop(columns=["Correct"]))

            st.subheader("📈 Backtest Result")
            total = len(result_df[result_df['Signal'].isin(["LONG", "SHORT"])])
            hits = result_df['Correct'].sum()
            if total > 0:
                st.success(f"Accuracy: {hits}/{total} directional signals → **{(hits/total)*100:.1f}%**")
            else:
                st.info("No LONG/SHORT signals to evaluate in backtest window.")

    except Exception as e:
        st.error(f"Processing error: {e}")
else:
    st.info("Please upload all three files (Daily, 4H, 30min).")


import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Multi-Timeframe Bias Assistant – Daily & 4H Trend Scanner")

st.markdown("""
This tool compares the current day vs the past 2–3 days (and 4H candles) to detect directional memory and build a bias narrative.

It uses:
- POC trend
- VWAP vs POC
- Price vs VAH/VAL
- Volume momentum
- Combined bias scoring
""")

daily_file = st.file_uploader("📅 Upload Daily CSV", type=["csv"])
h4_file = st.file_uploader("🕓 Upload 4H CSV", type=["csv"])

def clean(upload_file, suffix):
    df = pd.read_csv(upload_file)  # ✅ FIX: read from UploadedFile object
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

def daily_bias_score(df):
    df = df.copy()
    df['DateOnly'] = df['Datetime'].dt.date
    latest_3 = df.groupby('DateOnly').tail(1).sort_values('DateOnly').tail(3).reset_index(drop=True)

    output = []
    for i, row in latest_3.iterrows():
        try:
            poc = row['Point of Control_D']
            vwap = row['Volume Weighted Average Price_D']
            vah = row['Value Area High Value_D']
            val = row['Value Area Low Value_D']
            close = row['Last_D']
            volume = row['Volume_D']

            entry = {
                "Date": row['DateOnly'],
                "POC": poc,
                "VWAP": vwap,
                "Close": close,
                "Volume": volume,
                "VWAP > POC": vwap > poc,
                "Close > VAH": close > vah,
                "Close < VAL": close < val
            }
            output.append(entry)
        except:
            continue

    score_df = pd.DataFrame(output)
    st.subheader("📆 3-Day Daily Bias Comparison")
    st.dataframe(score_df)

    rising_poc = score_df['POC'].is_monotonic_increasing
    bullish_vwap = score_df['VWAP > POC'].sum()
    closes_above_vah = score_df['Close > VAH'].sum()
    closes_below_val = score_df['Close < VAL'].sum()

    st.markdown("### 📊 Bias Interpretation Summary")
    st.markdown(f"- POC trend: {'⬆️ Rising' if rising_poc else '↕️ Mixed or falling'}")
    st.markdown(f"- VWAP > POC Days: `{bullish_vwap}` of 3")
    st.markdown(f"- Closes above VAH: `{closes_above_vah}` | below VAL: `{closes_below_val}`")

    if rising_poc and bullish_vwap >= 2 and closes_above_vah >= 2:
        st.success("📈 Overall Sentiment: **STRONG BULLISH**")
    elif closes_below_val >= 2 and not rising_poc:
        st.error("📉 Overall Sentiment: **STRONG BEARISH**")
    else:
        st.warning("🟡 Overall Sentiment: **NEUTRAL or MIXED**")

def h4_trend_score(df):
    df = df.copy()
    df['RoundedTime'] = df['Datetime'].dt.floor('4H')
    recent = df.groupby('RoundedTime').tail(1).sort_values('RoundedTime').tail(6)

    st.subheader("🕓 Recent 4H Bias Snapshots (Last 6 x 4H)")
    trend_rows = []
    for i, row in recent.iterrows():
        try:
            vwap = row['Volume Weighted Average Price_H']
            poc = row['Point of Control_H']
            price = row['Last_H']
            val = row['Value Area Low Value_H']
            vah = row['Value Area High Value_H']

            label = "Inside Value"
            if price > vah:
                label = "Above VAH"
            elif price < val:
                label = "Below VAL"

            trend_rows.append({
                "Time": row['RoundedTime'],
                "POC": poc,
                "VWAP": vwap,
                "Close": price,
                "VWAP > POC": vwap > poc,
                "Location": label
            })
        except:
            continue

    trend_df = pd.DataFrame(trend_rows)
    st.dataframe(trend_df)

    if trend_df['VWAP > POC'].sum() >= 4 and (trend_df['Location'] == "Above VAH").sum() >= 2:
        st.success("📈 Intraday Momentum: **4H Bullish Bias**")
    elif (trend_df['Location'] == "Below VAL").sum() >= 2:
        st.error("📉 Intraday Momentum: **4H Bearish Bias**")
    else:
        st.info("🟡 Intraday Momentum: **4H Mixed or Range**")

if daily_file and h4_file:
    try:
        df_d = clean(daily_file, "D")
        df_h4 = clean(h4_file, "H")
        daily_bias_score(df_d)
        h4_trend_score(df_h4)
    except Exception as e:
        st.error(f"Processing error: {e}")
else:
    st.info("Please upload both Daily and 4H CSV files to begin.")

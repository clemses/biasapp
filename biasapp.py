
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Multi-Timeframe Bias Assistant – Sierra Chart (.txt) Files")

st.markdown("""
This app analyzes Sierra Chart data from Daily, 4H, and 30min charts (.csv or .txt), and gives written interpretations and directional bias across timeframes.
""")

# --- File Uploads ---
daily_file = st.file_uploader("📅 Upload Daily File", type=["csv", "txt"])
h4_file = st.file_uploader("🕓 Upload 4H File", type=["csv", "txt"])
tpo_file = st.file_uploader("🕧 Upload 30min File", type=["csv", "txt"])

if daily_file and h4_file and tpo_file:
    try:
        def read_and_prepare(file, label):
            df = pd.read_csv(file)
            if 'Time' not in df.columns:
                df['Time'] = '00:00:00'
            df.columns = [c.strip() for c in df.columns]
            rename_map = {
                'Close': 'Last', 'Last Price': 'Last', 'Last': 'Last',
                'Point of Control': 'POC', 'POC': 'POC',
                'Value Area High Value': 'VAH', 'Value Area High': 'VAH', 'VAH': 'VAH',
                'Value Area Low Value': 'VAL', 'Value Area Low': 'VAL', 'VAL': 'VAL',
                'Volume Weighted Average Price': 'VWAP', 'VWAP': 'VWAP'
            }
            for src, dst in rename_map.items():
                if src in df.columns:
                    df.rename(columns={src: dst}, inplace=True)
            df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            df = df.sort_values('Datetime').drop_duplicates(subset='Datetime', keep='last')
            st.write(f"✅ Loaded {label}:", len(df), "rows after dropping duplicates")
            return df

        daily = read_and_prepare(daily_file, "Daily")
        h4 = read_and_prepare(h4_file, "4H")
        tpo = read_and_prepare(tpo_file, "30min")

        # Avoid column collisions before merge
        tpo_cols = set(tpo.columns)
        h4 = h4[[col for col in h4.columns if col not in tpo_cols or col == 'Datetime']]
        merged = pd.merge_asof(tpo, h4, on='Datetime', direction='backward', suffixes=('', '_4H'))

        merged_cols = set(merged.columns)
        daily = daily[[col for col in daily.columns if col not in merged_cols or col == 'Datetime']]
        merged = pd.merge_asof(merged, daily, on='Datetime', direction='backward', suffixes=('', '_Daily'))

        st.subheader("🧠 Daily Bias Interpretation")
        most_recent = merged.iloc[-1]

        interpretations = []

        if most_recent['POC_Daily'] > most_recent['VAL_Daily'] and most_recent['POC_Daily'] < most_recent['VAH_Daily']:
            interpretations.append("🔹 POC in center of VA → Balanced")
        elif most_recent['POC_Daily'] >= most_recent['VAH_Daily']:
            interpretations.append("🔺 POC near VAH → Bullish tilt")
        elif most_recent['POC_Daily'] <= most_recent['VAL_Daily']:
            interpretations.append("🔻 POC near VAL → Bearish tilt")

        if most_recent['VWAP_Daily'] > most_recent['POC_Daily']:
            interpretations.append("✅ VWAP > POC → Fair value consensus above auction")
        elif most_recent['VWAP_Daily'] < most_recent['POC_Daily']:
            interpretations.append("⚠️ VWAP < POC → Value perceived lower")

        if most_recent['Last_Daily'] > most_recent['VAH_Daily']:
            interpretations.append("📈 Close above VAH → Initiative Buy Bias")
        elif most_recent['Last_Daily'] < most_recent['VAL_Daily']:
            interpretations.append("📉 Close below VAL → Initiative Sell Bias")
        else:
            interpretations.append("⏸️ Close inside VA → Responsive or Balanced Bias")

        st.write("**Combined Daily Analysis:**")
        for item in interpretations:
            st.markdown("- " + item)

        st.subheader("📍 Combined Timeframe Bias")
        def classify_bias(row):
            above_vah = row['Last'] > row['VAH']
            below_val = row['Last'] < row['VAL']
            in_value = row['VAL'] <= row['Last'] <= row['VAH']
            rising_vol = row['Volume'] > 1000 and row.get('Volume_4H', 0) > 5000 and row.get('Volume_Daily', 0) > 5000

            if above_vah and rising_vol:
                return "Initiative Buy"
            elif below_val and rising_vol:
                return "Initiative Sell"
            elif in_value and not rising_vol:
                return "Responsive/Wait"
            elif above_vah and not rising_vol:
                return "Exhaustion Buy"
            elif below_val and not rising_vol:
                return "Exhaustion Sell"
            else:
                return "Unclear"

        merged['Bias'] = merged.apply(classify_bias, axis=1)
        st.dataframe(merged[['Datetime', 'Last', 'Bias']].tail(20))

        st.download_button("📥 Download Bias Summary CSV", data=merged.to_csv(index=False), file_name="bias_summary.csv")

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Upload all 3 files (Daily, 4H, 30min) to begin.")

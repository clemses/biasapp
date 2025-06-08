
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Bias Assistant with Rule-Based Interpretation")

st.markdown("""
This app combines Sierra Chart Daily, 4H, and 30min data and applies rule-based logic for:
- VWAP vs POC positioning
- Price inside vs outside Value Area (VAH/VAL)
- Volume surge detection
- Final bias classification with explanation
""")

# Upload section
daily_file = st.file_uploader("📅 Upload Daily CSV", type=["csv"])
h4_file = st.file_uploader("🕓 Upload 4H CSV", type=["csv"])
tpo_file = st.file_uploader("🕧 Upload 30min CSV", type=["csv"])

def prepare_df(upload, suffix):
    df = pd.read_csv(upload)
    df.columns = [c.strip() for c in df.columns]

    df['Date'] = df['Date'].astype(str)
    df['Time'] = df['Time'].astype(str) if 'Time' in df.columns else '00:00:00'
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')

    df = df.sort_values("Datetime").drop_duplicates(subset="Datetime")

    keep = ['Datetime', 'Last', 'Volume', 'Point of Control', 'Value Area High Value', 'Value Area Low Value', 'Volume Weighted Average Price']
    df = df[[col for col in keep if col in df.columns]]
    df.rename(columns={col: f"{col}_{suffix}" for col in df.columns if col != 'Datetime'}, inplace=True)
    df = df.loc[:, ~df.columns.duplicated()]
    return df

def classify_bias(row):
    try:
        price = row['Last_M']
        val = row['Value Area Low Value_M']
        vah = row['Value Area High Value_M']
        poc = row['Point of Control_M']
        vwap = row['Volume Weighted Average Price_M']
        volume = row['Volume_M']

        # Volume context
        vol_surge = volume > 10000

        # Value area location
        if price > vah:
            loc = 'Above VAH'
        elif price < val:
            loc = 'Below VAL'
        else:
            loc = 'Inside VA'

        # VWAP vs POC
        if vwap > poc:
            consensus = 'bullish'
        elif vwap < poc:
            consensus = 'bearish'
        else:
            consensus = 'neutral'

        # Combine logic
        if loc == 'Above VAH' and consensus == 'bullish' and vol_surge:
            return '📈 Initiative Long Bias'
        elif loc == 'Below VAL' and consensus == 'bearish' and vol_surge:
            return '📉 Initiative Short Bias'
        elif loc == 'Inside VA' and vol_surge:
            return '🔄 Responsive Trading Zone'
        elif not vol_surge:
            return '⏳ Low Volume – Wait'
        else:
            return '❓ Unclear'
    except:
        return '⚠️ Incomplete Data'

if daily_file and h4_file and tpo_file:
    try:
        daily = prepare_df(daily_file, "D")
        h4 = prepare_df(h4_file, "H")
        tpo = prepare_df(tpo_file, "M")

        merged = pd.merge_asof(tpo, h4, on="Datetime", direction="backward")
        merged = pd.merge_asof(merged, daily, on="Datetime", direction="backward")
        merged = merged.loc[:, ~merged.columns.duplicated()]

        merged['Bias Signal'] = merged.apply(classify_bias, axis=1)

        st.success("✅ Rule-based classification applied.")
        st.dataframe(merged[['Datetime', 'Last_M', 'Bias Signal']].tail(50))

    except Exception as e:
        st.error(f"❌ Merge or classification failed: {e}")
else:
    st.info("Upload all 3 CSV files to run the bias engine.")

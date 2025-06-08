
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🧠 Multi-Timeframe Bias Assistant – Clean Foundation")

st.markdown("Upload your Sierra Chart `.txt` or `.csv` data for **Daily**, **4H**, and **30min** timeframes to begin bias interpretation.")

# --- Upload Section ---
daily_file = st.file_uploader("📅 Upload Daily File", type=["csv", "txt"])
h4_file = st.file_uploader("🕓 Upload 4H File", type=["csv", "txt"])
tpo_file = st.file_uploader("🕧 Upload 30min File", type=["csv", "txt"])

def standardize_df(df, label):
    # Fix missing time
    if 'Time' not in df.columns:
        df['Time'] = '00:00:00'
    df.columns = [c.strip() for c in df.columns]

    # Rename relevant columns
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
    # Timestamp
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values('Datetime').drop_duplicates(subset='Datetime', keep='last')
    st.success(f"✅ {label} file loaded: {len(df)} rows after cleaning.")
    return df

if daily_file and h4_file and tpo_file:
    try:
        daily = standardize_df(pd.read_csv(daily_file), "Daily")
        h4 = standardize_df(pd.read_csv(h4_file), "4H")
        tpo = standardize_df(pd.read_csv(tpo_file), "30min")

        # --- Safe Merge ---
        base = tpo.copy()
        h4 = h4[[col for col in h4.columns if col not in base.columns or col == 'Datetime']]
        merged = pd.merge_asof(base, h4, on='Datetime', direction='backward', suffixes=('', '_4H'))

        daily = daily[[col for col in daily.columns if col not in merged.columns or col == 'Datetime']]
        merged = pd.merge_asof(merged, daily, on='Datetime', direction='backward', suffixes=('', '_Daily'))

        st.subheader("🧪 Clean Merged Data (preview)")
        st.dataframe(merged.tail(25))

        st.info("✅ Data ready — bias rules and interpretation logic will be added next.")

    except Exception as e:
        st.error(f"🚫 Error during processing: {e}")

else:
    st.info("Please upload all 3 files to begin.")

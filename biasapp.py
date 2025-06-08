
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🧠 Multi-Timeframe Bias Assistant – Clean & Stable Merge")

st.markdown("Upload Sierra Chart `.txt` or `.csv` data for **Daily**, **4H**, and **30min**. This version safely renames columns and avoids all axis reindex errors.")

# --- Upload Section ---
daily_file = st.file_uploader("📅 Upload Daily File", type=["csv", "txt"])
h4_file = st.file_uploader("🕓 Upload 4H File", type=["csv", "txt"])
tpo_file = st.file_uploader("🕧 Upload 30min File", type=["csv", "txt"])

def standardize_df(df, label, suffix):
    if 'Time' not in df.columns:
        df['Time'] = '00:00:00'
    df.columns = [c.strip() for c in df.columns]

    rename_map = {
        'Close': 'Last', 'Last Price': 'Last', 'Last': 'Last',
        'Point of Control': 'POC', 'POC': 'POC',
        'Value Area High Value': 'VAH', 'Value Area High': 'VAH', 'VAH': 'VAH',
        'Value Area Low Value': 'VAL', 'Value Area Low': 'VAL', 'VAL': 'VAL',
        'Volume Weighted Average Price': 'VWAP', 'VWAP': 'VWAP',
        'Volume': 'Volume'
    }

    for src, dst in rename_map.items():
        if src in df.columns:
            df.rename(columns={src: dst}, inplace=True)

    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values('Datetime').drop_duplicates(subset='Datetime', keep='last')

    # Add suffix to all non-time columns
    cols_to_rename = {col: f"{col}_{suffix}" for col in df.columns if col not in ['Datetime', 'Date', 'Time']}
    df.rename(columns=cols_to_rename, inplace=True)

    st.success(f"✅ {label} loaded: {len(df)} rows after cleaning. Columns: {list(df.columns)}")
    return df

if daily_file and h4_file and tpo_file:
    try:
        daily = standardize_df(pd.read_csv(daily_file), "Daily", "Daily")
        h4 = standardize_df(pd.read_csv(h4_file), "4H", "4H")
        tpo = standardize_df(pd.read_csv(tpo_file), "30min", "30min")

        # Merge
        merged = pd.merge_asof(tpo, h4, on='Datetime', direction='backward')
        merged = pd.merge_asof(merged, daily, on='Datetime', direction='backward')

        st.subheader("🧪 Merged Clean Data")
        st.dataframe(merged.tail(20))

        st.info("✅ Merge successful! Ready for rule logic implementation.")

    except Exception as e:
        st.error(f"🚫 Processing failed: {e}")
else:
    st.info("Please upload all 3 files to begin.")

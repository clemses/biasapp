
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🧠 Multi-Timeframe Bias Assistant – Deep-Cleaned")

st.markdown("This version fixes all `duplicate labels` issues by renaming, deduplicating columns and dropping raw time fields before merge.")

# Upload
daily_file = st.file_uploader("📅 Upload Daily File", type=["csv", "txt"])
h4_file = st.file_uploader("🕓 Upload 4H File", type=["csv", "txt"])
tpo_file = st.file_uploader("🕧 Upload 30min File", type=["csv", "txt"])

def clean_and_prepare(file, label, suffix):
    df = pd.read_csv(file)
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
    df.drop(columns=[col for col in ['Date', 'Time'] if col in df.columns], inplace=True)

    # Suffix all columns except timestamp
    df = df.rename(columns={col: f"{col}_{suffix}" for col in df.columns if col != 'Datetime'})

    # Drop duplicated column names if any
    df = df.loc[:, ~df.columns.duplicated()]
    st.write(f"📁 {label} columns:", list(df.columns))
    return df

if daily_file and h4_file and tpo_file:
    try:
        daily = clean_and_prepare(daily_file, "Daily", "D")
        h4 = clean_and_prepare(h4_file, "4H", "H")
        tpo = clean_and_prepare(tpo_file, "30min", "M")

        merged = pd.merge_asof(tpo, h4, on="Datetime", direction="backward")
        merged = pd.merge_asof(merged, daily, on="Datetime", direction="backward")

        # Ensure no duplicated columns post merge
        merged = merged.loc[:, ~merged.columns.duplicated()]

        st.success("✅ Merging complete. Columns are unique and clean.")
        st.dataframe(merged.tail(20))

    except Exception as e:
        st.error(f"🚫 Merge failed: {e}")
else:
    st.info("Upload all 3 timeframe files to proceed.")

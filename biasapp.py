
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("✅ Bias Assistant – Verified Merge Based on Clean Input")

st.markdown("This version uses validated 30min, 4H, and Daily Sierra Chart exports. It renames all columns safely, drops unused ones, and merges without conflict.")

# Upload files
daily_file = st.file_uploader("📅 Upload Daily CSV", type=["csv"])
h4_file = st.file_uploader("🕓 Upload 4H CSV", type=["csv"])
tpo_file = st.file_uploader("🕧 Upload 30min CSV", type=["csv"])

def clean_df(file, label, suffix):
    df = pd.read_csv(file)
    if 'Time' not in df.columns:
        df['Time'] = '00:00:00'
    df.columns = [c.strip() for c in df.columns]
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values('Datetime').drop_duplicates(subset='Datetime')

    # Keep only key analysis columns
    keep_cols = ['Datetime', 'Last', 'POC', 'Value Area High Value', 'Value Area Low Value', 'Volume Weighted Average Price', 'Volume']
    df = df[[col for col in keep_cols if col in df.columns]]

    # Suffix all non-datetime columns
    df.rename(columns={col: f"{col}_{suffix}" for col in df.columns if col != 'Datetime'}, inplace=True)
    return df

if daily_file and h4_file and tpo_file:
    try:
        daily = clean_df(daily_file, "Daily", "D")
        h4 = clean_df(h4_file, "4H", "H")
        tpo = clean_df(tpo_file, "30min", "M")

        merged = pd.merge_asof(tpo, h4, on="Datetime", direction="backward")
        merged = pd.merge_asof(merged, daily, on="Datetime", direction="backward")

        merged = merged.loc[:, ~merged.columns.duplicated()]  # safety check

        st.success("✅ Merge successful! Preview below:")
        st.dataframe(merged.tail(25))

    except Exception as e:
        st.error(f"❌ Merge failed: {e}")
else:
    st.info("Upload all 3 files to run analysis.")

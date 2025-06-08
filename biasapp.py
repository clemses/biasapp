
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🧠 Bias Assistant – Final Fix Version")

st.markdown("""
This version guarantees success by:
- Forcing all timestamp columns to string
- Keeping only required bias-related fields
- Removing duplicate labels
- Using safe suffixes
- Sorting by datetime before merge
""")

# Upload section
daily_file = st.file_uploader("📅 Upload Daily CSV", type=["csv"])
h4_file = st.file_uploader("🕓 Upload 4H CSV", type=["csv"])
tpo_file = st.file_uploader("🕧 Upload 30min CSV", type=["csv"])

def prepare_df(upload, suffix):
    df = pd.read_csv(upload)
    df.columns = [c.strip() for c in df.columns]

    # Fix types before datetime merge
    df['Date'] = df['Date'].astype(str)
    df['Time'] = df['Time'].astype(str) if 'Time' in df.columns else '00:00:00'
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')

    # Sort and deduplicate
    df = df.sort_values("Datetime").drop_duplicates(subset="Datetime")

    # Focus only on bias-related columns
    keep = ['Datetime', 'Last', 'Volume', 'Point of Control', 'Value Area High Value', 'Value Area Low Value', 'Volume Weighted Average Price']
    df = df[[col for col in keep if col in df.columns]]

    # Apply suffix to all non-datetime columns
    df.rename(columns={col: f"{col}_{suffix}" for col in df.columns if col != 'Datetime'}, inplace=True)

    # Ensure no duplicate column labels
    df = df.loc[:, ~df.columns.duplicated()]

    return df

if daily_file and h4_file and tpo_file:
    try:
        daily = prepare_df(daily_file, "D")
        h4 = prepare_df(h4_file, "H")
        tpo = prepare_df(tpo_file, "M")

        merged = pd.merge_asof(tpo, h4, on="Datetime", direction="backward")
        merged = pd.merge_asof(merged, daily, on="Datetime", direction="backward")

        merged = merged.loc[:, ~merged.columns.duplicated()]

        st.success("✅ Merge successful. Final combined dataset:")
        st.dataframe(merged.tail(50))

    except Exception as e:
        st.error(f"❌ Merge failed: {e}")
else:
    st.info("Upload all 3 CSV files to run the bias assistant.")

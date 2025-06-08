
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🧠 Bias Assistant – Full Debug Mode")

st.markdown("Upload 3 Sierra Chart `.txt` or `.csv` files. This version prints all column names and datetime uniqueness to debug merge crashes.")

debug = True  # show diagnostic info

# Upload files
daily_file = st.file_uploader("📅 Daily File", type=["csv", "txt"])
h4_file = st.file_uploader("🕓 4H File", type=["csv", "txt"])
tpo_file = st.file_uploader("🕧 30min File", type=["csv", "txt"])

def debug_df(df, label):
    st.write(f"📋 **{label} Columns:**", list(df.columns))
    dup_dt = df['Datetime'].duplicated().sum()
    st.write(f"🕐 **{label} Duplicate Timestamps:**", dup_dt)
    return df

def prepare_df(file, label, suffix):
    df = pd.read_csv(file)
    if 'Time' not in df.columns:
        df['Time'] = '00:00:00'
    df.columns = [c.strip() for c in df.columns]
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values("Datetime").drop_duplicates(subset="Datetime", keep="last")
    df.drop(columns=[col for col in ['Date', 'Time'] if col in df.columns], inplace=True)

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

    df.rename(columns={col: f"{col}_{suffix}" for col in df.columns if col != 'Datetime'}, inplace=True)
    df = df.loc[:, ~df.columns.duplicated()]
    return debug_df(df, label)

if daily_file and h4_file and tpo_file:
    try:
        daily = prepare_df(daily_file, "Daily", "D")
        h4 = prepare_df(h4_file, "4H", "H")
        tpo = prepare_df(tpo_file, "30min", "M")

        # First merge: TPO + 4H
        st.markdown("🔀 Merging 30min with 4H…")
        merged = pd.merge_asof(tpo, h4, on="Datetime", direction="backward")
        merged = merged.loc[:, ~merged.columns.duplicated()]
        st.write("✅ After 4H merge:", merged.columns)

        # Second merge: + Daily
        st.markdown("🔀 Merging result with Daily…")
        merged = pd.merge_asof(merged, daily, on="Datetime", direction="backward")
        merged = merged.loc[:, ~merged.columns.duplicated()]
        st.write("✅ Final columns after all merges:", merged.columns)

        # Final output
        st.success("✅ Merge complete with unique columns and datetimes.")
        st.dataframe(merged.tail(25))

    except Exception as e:
        st.error(f"🚫 Merge failed: {e}")

else:
    st.info("Upload all 3 files to run merge.")

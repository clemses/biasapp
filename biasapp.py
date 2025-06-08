
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(layout="wide")
st.title("Bias Mode Rule Engine + Session Planner")

st.markdown("""
This tool classifies market bias mode (Initiative vs Responsive) based on 30min TPO data, 4H and Daily chart structure, and generates a full session planner with visual signals and export functionality.
""")

# --- Upload section ---
tpo_file = st.file_uploader("Upload 30min TPO file (CSV or TXT from Sierra Chart)", type=["csv", "txt"])
h4_file = st.file_uploader("Upload 4H Bias CSV file", type=["csv"])
daily_file = st.file_uploader("Upload Daily Bias CSV file", type=["csv"])

if tpo_file and h4_file and daily_file:
    try:
        def read_sierra_file(uploaded_file):
            # Try to parse it as a CSV with comma delimiter
            return pd.read_csv(uploaded_file)

        tpo_df = read_sierra_file(tpo_file)
        h4_df = pd.read_csv(h4_file)
        daily_df = pd.read_csv(daily_file)

        # Format datetime columns
        tpo_df['Datetime'] = pd.to_datetime(tpo_df['Date'] + ' ' + tpo_df['Time'])
        h4_df['Datetime'] = pd.to_datetime(h4_df['Date'] + ' ' + h4_df['Time'])
        daily_df['Datetime'] = pd.to_datetime(daily_df['Date'])

        # Sort for merge_asof
        tpo_df = tpo_df.sort_values('Datetime')
        h4_df = h4_df.sort_values('Datetime')
        daily_df = daily_df.sort_values('Datetime')

        # Merge
        merged = pd.merge_asof(tpo_df, h4_df, on='Datetime', direction='backward', suffixes=('', '_4H'))
        merged = pd.merge_asof(merged, daily_df, on='Datetime', direction='backward', suffixes=('', '_Daily'))

        # --- Rule Logic Functions ---
        def get_bias_mode(row):
            outside_high = row['Last'] > row['Value Area High Value']
            outside_low = row['Last'] < row['Value Area Low Value']
            inside_value = not outside_high and not outside_low

            tpo_volume = row.get('Volume', 0)
            h4_volume = row.get('Volume_4H', 0)
            daily_volume = row.get('Volume_Daily', 0)
            rising_volume = tpo_volume > 1000 and h4_volume > 5000 and daily_volume > 5000

            bias_strong_up = row.get('Last_Daily', 0) > row.get('Value Area High Value_Daily', 0)
            bias_strong_down = row.get('Last_Daily', 0) < row.get('Value Area Low Value_Daily', 0)

            if (outside_high or outside_low) and rising_volume and (bias_strong_up or bias_strong_down):
                return "Initiative Bias"
            elif inside_value and not rising_volume:
                return "Responsive Bias"
            elif inside_value and rising_volume:
                return "Neutral - Watch for Breakout"
            elif (outside_high or outside_low) and not rising_volume:
                return "Fakeout - Wait"
            else:
                return "Unclear"

        def get_session_bias(row):
            if row.get('Last_Daily', 0) > row.get('Value Area High Value_Daily', 0):
                return "Daily Bullish Bias"
            elif row.get('Last_Daily', 0) < row.get('Value Area Low Value_Daily', 0):
                return "Daily Bearish Bias"
            else:
                return "Daily Neutral"

        # Apply rules
        merged['Bias Mode'] = merged.apply(get_bias_mode, axis=1)
        merged['Session Bias'] = merged.apply(get_session_bias, axis=1)

        # --- Session Planner Table ---
        st.subheader("Session Planner Summary")
        session_summary = merged[['Datetime', 'Last', 'Session Bias', 'Bias Mode']].copy()
        st.dataframe(session_summary.tail(100))

        # --- Visualization ---
        st.subheader("Bias Mode Over Time")
        fig, ax = plt.subplots(figsize=(12, 5))
        color_map = {
            'Initiative Bias': 'green',
            'Responsive Bias': 'blue',
            'Neutral - Watch for Breakout': 'orange',
            'Fakeout - Wait': 'red',
            'Unclear': 'gray'
        }
        colors = merged['Bias Mode'].map(color_map)
        ax.scatter(merged['Datetime'], merged['Last'], c=colors, label='Bias Mode', alpha=0.7)
        ax.set_title("Price vs. Bias Mode")
        ax.set_ylabel("Last Price")
        ax.set_xlabel("Datetime")
        ax.grid(True)
        st.pyplot(fig)

        # --- Export Section ---
        st.subheader("Export Filtered Trade Signals")
        selected_bias = st.multiselect("Select Bias Modes to Export", merged['Bias Mode'].unique())
        filtered_df = merged[merged['Bias Mode'].isin(selected_bias)]
        st.dataframe(filtered_df[['Datetime', 'Last', 'Bias Mode', 'Session Bias']])

        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Filtered Signals as CSV", data=csv, file_name="filtered_signals.csv")

    except Exception as e:
        st.error(f"An error occurred: {e}")

else:
    st.info("Please upload all three data files to begin.")

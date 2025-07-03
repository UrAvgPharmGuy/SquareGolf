import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Page config
st.set_page_config(page_title="Golf Launch Monitor Dashboard", layout="wide")

# --- Load and clean data ---
def load_and_clean_csv(filepath):
    try:
        df = pd.read_csv(filepath, skiprows=2)  # Skip metadata, load actual header row
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

    df.columns = df.columns.str.strip().str.replace('(yd)', '', regex=False).str.replace('(mph)', '', regex=False).str.replace(' ', '')

    if "Club" not in df.columns:
        st.error("Missing 'Club' column. Please check your CSV.")
        return pd.DataFrame()

    df = df[df["Club"].notnull() & ~df["Index"].astype(str).str.contains("Average|Deviation", na=False)]

    # Rename core metrics for easier use
    rename_map = {
        "Carry": "Carry",
        "Offline": "Offline",
        "Total": "Total Distance",
        "BallSpeed": "Ball Speed",
        "LaunchAngle": "Launch Angle",
        "SpinRate": "Spin Rate"
    }
    for original, new in rename_map.items():
        if original in df.columns:
            df[new] = pd.to_numeric(df[original], errors="coerce")

    return df

# --- Load file ---
df = load_and_clean_csv("golfdata.csv")
if df.empty:
    st.stop()

# --- Sidebar filters ---
club_list = sorted(df["Club"].unique())
selected_clubs = st.sidebar.multiselect("Select Club(s)", club_list, default=club_list)

filtered_df = df[df["Club"].isin(selected_clubs)]

# --- Standardize directional values ---
def convert_lr_to_float(value):
    if isinstance(value, str):
        value = value.strip()
        match = re.match(r'^([LR])(\d+(\.\d+)?)$', value)
        if match:
            return -float(match[2]) if match[1] == 'L' else float(match[2])
        try:
            return float(value)
        except:
            return value
    return value

# Columns likely to contain L/R strings
directional_cols = [
    "LaunchDirection", "SpinAxis", "SideSpin", "Offline",
    "ClubPath", "FaceAngle"
]

for col in directional_cols:
    if col in filtered_df.columns:
        filtered_df[col] = filtered_df[col].apply(convert_lr_to_float)

# --- Dispersion Chart ---
st.subheader("Dispersion Chart: Carry vs Offline")
if "Carry" in filtered_df.columns and "Offline" in filtered_df.columns:
    fig_dispersion = px.scatter(
        filtered_df,
        x="Offline",
        y="Carry",
        color="Club",
        hover_data=["Ball Speed", "Spin Rate"],
        title="Shot Dispersion by Club",
        height=500
    )
    st.plotly_chart(fig_dispersion, use_container_width=True)
else:
    st.warning("Missing Carry or Offline data.")

# --- Gapping Chart ---
st.subheader("Gapping Chart: Avg Carry and Total Distance per Club")
if "Carry" in filtered_df.columns and "Total Distance" in filtered_df.columns:
    gapping_df = (
        filtered_df.groupby("Club")[["Carry", "Total Distance"]]
        .mean()
        .reset_index()
        .sort_values("Carry", ascending=False)
    )

    gapping_df_melted = gapping_df.melt(id_vars="Club", value_vars=["Carry", "Total Distance"], 
                                        var_name="Metric", value_name="Distance")

    gapping_df_melted["Distance"] = gapping_df_melted["Distance"].round(0)

    fig_gapping = px.bar(
        gapping_df_melted,
        x="Distance",
        y="Club",
        color="Metric",
        orientation="h",
        barmode="group",
        text="Distance",
        title="Average Carry and Total Distance by Club",
        height=500
    )
    fig_gapping.update_traces(textposition='outside')
    st.plotly_chart(fig_gapping, use_container_width=True)
else:
    st.warning("Missing Carry or Total Distance data.")

# --- Raw Table ---
st.subheader("Shot Data Table")
st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

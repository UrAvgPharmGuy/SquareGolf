import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Page config
st.set_page_config(page_title="Golf Launch Monitor Dashboard", layout="wide")

# --- Load and clean data ---
def load_and_clean_csv(filepath):
    try:
        df = pd.read_csv(filepath)
        if "Club" not in df.columns:
            df = pd.read_csv(filepath, header=2)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

    df.columns = df.columns.str.strip()

    if "Club" not in df.columns:
        st.error("Missing 'Club' column. Please check your CSV.")
        return pd.DataFrame()

    df = df[df["Club"].notnull() & (df["Club"] != "Average")]

    # Rename columns to consistent names
    rename_map = {
        "Carry(yd)": "Carry",
        "Offline(yd)": "Offline",
        "Total(yd)": "Total Distance",
        "Ball Speed(mph)": "Ball Speed",
        "Launch Angle": "Launch Angle",
        "Spin Rate": "Spin Rate"
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
        if value.startswith('L'):
            return -float(value[1:])
        elif value.startswith('R'):
            return float(value[1:])
        try:
            return float(value)
        except:
            return value
    return value

directional_cols = [
    "Launch Direction", "Spin Axis", "Side Spin", "Offline",
    "Club Path", "Face Angle"
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
st.subheader("Gapping Chart: Avg Carry per Club")
if "Carry" in filtered_df.columns:
    gapping_df = (
        filtered_df.groupby("Club")["Carry"]
        .mean()
        .reset_index()
        .sort_values("Carry", ascending=False)
    )

    fig_gapping = px.bar(
        gapping_df,
        x="Carry",
        y="Club",
        orientation="h",
        title="Average Carry Distance by Club",
        height=500
    )
    st.plotly_chart(fig_gapping, use_container_width=True)

# --- Raw Table ---
st.subheader("Shot Data Table")
st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

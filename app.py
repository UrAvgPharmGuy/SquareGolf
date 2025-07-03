import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config
st.set_page_config(page_title="Golf Launch Monitor Dashboard", layout="wide")

# Load data
data_file = "golfdata.csv"
df = pd.read_csv(data_file)

# Clean column names
df.columns = df.columns.str.strip()

# Remove averages or blank entries if present
df = df[df["Club"].notnull() & (df["Club"] != "Average")]

# Convert necessary columns to numeric
numeric_cols = ["Carry(yd)", "Offline(yd)", "Total(yd)", "Ball Speed(mph)", "Launch Angle", "Spin Rate"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Sidebar filters
st.sidebar.header("Filters")
club_selection = st.sidebar.multiselect("Select Club(s)", options=df["Club"].unique(), default=df["Club"].unique())

# Filtered dataframe
df_filtered = df[df["Club"].isin(club_selection)]

# Main title
st.title("🏌️ Golf Launch Monitor Dashboard")

# Dispersion plot
st.subheader("Shot Dispersion (Carry vs. Offline)")
fig_dispersion = px.scatter(
    df_filtered,
    x="Offline(yd)",
    y="Carry(yd)",
    color="Club",
    hover_data=["Total(yd)", "Ball Speed(mph)", "Launch Angle"],
    labels={"Offline(yd)": "Offline (yards)", "Carry(yd)": "Carry (yards)"},
    height=500
)
st.plotly_chart(fig_dispersion, use_container_width=True)

# Gapping chart
st.subheader("Average Carry Distance by Club")
avg_carry = df_filtered.groupby("Club")["Carry(yd)"].mean().reset_index().sort_values("Carry(yd)")
fig_gapping = px.bar(
    avg_carry,
    x="Carry(yd)",
    y="Club",
    orientation="h",
    labels={"Carry(yd)": "Average Carry (yards)", "Club": "Club"},
    height=500
)
st.plotly_chart(fig_gapping, use_container_width=True)

# Shot table
st.subheader("Shot Data Table")
st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

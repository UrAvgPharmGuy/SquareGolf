import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

    # Rename core metrics for easier use (delay coercion to later step)
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
            df[new] = df[original]  # just copy without coercing yet

    return df

# --- Outlier Filter Toggle ---
remove_outliers = st.sidebar.checkbox("Remove outliers", value=True)

# --- Load and merge all session files ---
import glob
import os

session_files = glob.glob("Sessions/session_*.csv")
all_sessions = []

for f in session_files:
    df_temp = load_and_clean_csv(f)
    session_date = os.path.basename(f).replace("session_", "").replace(".csv", "")
    df_temp["Session"] = session_date  # add a session identifier
    all_sessions.append(df_temp)

df = pd.concat(all_sessions, ignore_index=True) if all_sessions else pd.DataFrame()
if df.empty:
    st.error("No session data found.")
    st.stop()

# --- Sidebar filters ---
with st.sidebar:
    st.subheader("Filters")
    with st.expander("Club & Session Filters", expanded=True):
        all_clubs = sorted(df["Club"].unique())
        select_all = st.checkbox("Select all clubs", value=True)
        if select_all:
            selected_clubs = st.multiselect("Select Club(s)", all_clubs, default=all_clubs)
        else:
            selected_clubs = st.multiselect("Select Club(s)", all_clubs)

        if "Session" in df.columns:
            unique_sessions = sorted(df["Session"].unique())
            selected_session = st.selectbox("Select Session", unique_sessions)
            df = df[df["Session"] == selected_session]

filtered_df = df[df["Club"].isin(selected_clubs)]
if filtered_df.empty:
    st.warning("Please select at least one club with valid data.")
    st.stop()
if filtered_df.empty:
    st.warning("Please select at least one club with valid data.")
    st.stop()


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

# Coerce numeric values after directional fix
numeric_cols = ["Carry", "Total Distance", "Ball Speed", "Launch Angle", "Spin Rate"]
for col in numeric_cols:
    if col in filtered_df.columns:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce")

# --- Club Recommendation ---
st.subheader("Club Recommendation by Target Distance")
target_distance = st.number_input("Enter your target distance (yds):", min_value=0, max_value=400, step=1)

if target_distance > 0 and "Total Distance" in filtered_df.columns:
    avg_distances = (
        filtered_df.groupby("Club")["Total Distance"]
        .mean()
        .reset_index()
        .rename(columns={"Total Distance": "Avg Distance"})
    )
    avg_distances["Delta"] = abs(avg_distances["Avg Distance"] - target_distance)
    best_match = avg_distances.sort_values("Delta").iloc[0]

    st.success(f"💡 Best match: **{best_match['Club']}** (Avg: {round(best_match['Avg Distance'])} yds)")

# --- Summary Table: Min/Avg/Max Total Distance ---
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Total Distance Summary by Club")
    if "Total Distance" in filtered_df.columns:
        club_order = {
    "56-Degree": 0,
    "S-Wedge": 1,
    "G-Wedge": 2,
    "P-Wedge": 3,
    "9 Iron": 4,
    "8 Iron": 5,
    "7 Iron": 6,
    "5 Iron": 7,
    "5 Hybrid": 8,
    "3 Hybrid": 9,
    "3 Wood": 10
}
distance_summary = (
    filtered_df.groupby("Club")["Total Distance"]
    .agg(["min", "mean", "max"])
    .round(0)
    .astype(int)
    .reset_index()
)
distance_summary["SortOrder"] = distance_summary["Club"].map(club_order)
distance_summary = distance_summary.sort_values("SortOrder").drop(columns=["SortOrder"])
st.dataframe(distance_summary.rename(columns={"min": "Min", "mean": "Average", "max": "Max"}).style.set_properties(**{'font-size': '12px'}), use_container_width=True)

# --- Dispersion Chart with Filled Ellipses ---
with st.expander("Shot Dispersion Chart", expanded=True):
    if "Carry" in filtered_df.columns and "Offline" in filtered_df.columns:
        import numpy as np

        color_palette = px.colors.qualitative.Set2
        club_colors = {club: color_palette[i % len(color_palette)] for i, club in enumerate(filtered_df["Club"].unique())}

        fig_dispersion = px.scatter(
            filtered_df,
            x="Offline",
            y="Carry",
            color="Club",
            hover_data=["Ball Speed", "Spin Rate"],
            title="Shot Dispersion by Club",
            height=400,
            color_discrete_map=club_colors
        )

        # Add ellipse as a scatter trace so it toggles with legend
        for club in filtered_df["Club"].unique():
            club_data = filtered_df[filtered_df["Club"] == club]
            if len(club_data) > 2:
                x_mean = club_data["Offline"].mean()
                y_mean = club_data["Carry"].mean()
                x_std = club_data["Offline"].std() * 2
                y_std = club_data["Carry"].std() * 2

                theta = np.linspace(0, 2 * np.pi, 100)
                x_ellipse = x_mean + x_std * np.cos(theta)
                y_ellipse = y_mean + y_std * np.sin(theta)

                fig_dispersion.add_trace(go.Scatter(
                    x=x_ellipse,
                    y=y_ellipse,
                    mode="lines",
                    line=dict(color=club_colors[club], width=2, dash="dot"),
                    fill='toself',
                    fillcolor=club_colors[club].replace('rgb', 'rgba').replace(')', ', 0.1)'),
                    name=f"{club} Ellipse",
                    legendgroup=club,
                    showlegend=False,
                    hoverinfo='skip'
                ))

        st.plotly_chart(fig_dispersion, use_container_width=True)
    else:
        st.warning("Missing Carry or Offline data.")

# --- Gapping Chart ---
with st.expander("Gapping Chart: Avg Carry and Total Distance per Club", expanded=False):
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
            height=400
        )
        fig_gapping.update_traces(textposition='outside')
        st.plotly_chart(fig_gapping, use_container_width=True)
    else:
        st.warning("Missing Carry or Total Distance data.")

# --- Apply Outlier Filtering (IQR-based and custom rules) ---
if remove_outliers:
    for col in ["Carry", "Total Distance"]:
        if col in filtered_df.columns:
            Q1 = filtered_df[col].quantile(0.25)
            Q3 = filtered_df[col].quantile(0.75)
            IQR = Q3 - Q1
            filtered_df = filtered_df[(filtered_df[col] >= Q1 - 1.5 * IQR) & (filtered_df[col] <= Q3 + 1.5 * IQR)]

    # Custom cleanup rules
    if "Ball Speed" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Ball Speed"] >= 40]
    if "Carry" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Carry"] >= 30]
    if "Offline" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Offline"].apply(lambda x: isinstance(x, (int, float)) and abs(x) <= 50)]

# --- Raw Table ---
with st.expander("Shot Data Table", expanded=False):
    st.dataframe(filtered_df.reset_index(drop=True).style.set_properties(**{'font-size': '12px'}), use_container_width=True)

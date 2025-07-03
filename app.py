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

# --- Load file ---
df = load_and_clean_csv("golfdata.csv")
if df.empty:
    st.stop()

# --- Sidebar filters ---
club_list = sorted(df["Club"].unique())
with st.sidebar:
    st.subheader("Filters")
    selected_clubs = st.multiselect("Select Club(s)", club_list, default=club_list)

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

# Coerce numeric values after directional fix
numeric_cols = ["Carry", "Total Distance", "Ball Speed", "Launch Angle", "Spin Rate"]
for col in numeric_cols:
    if col in filtered_df.columns:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce")

# --- Summary Table: Min/Avg/Max Total Distance ---
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Total Distance Summary by Club")
    if "Total Distance" in filtered_df.columns:
        distance_summary = filtered_df.groupby("Club")["Total Distance"].agg(["min", "mean", "max"]).round(1).reset_index()
        st.dataframe(distance_summary.rename(columns={"min": "Min", "mean": "Average", "max": "Max"}).style.set_properties(**{'font-size': '12px'}), use_container_width=True)

# --- Dispersion Chart with Filled Ellipses ---
with st.expander("Shot Dispersion Chart", expanded=True):
    if "Carry" in filtered_df.columns and "Offline" in filtered_df.columns:
        fig_dispersion = px.scatter(
            filtered_df,
            x="Offline",
            y="Carry",
            color="Club",
            hover_data=["Ball Speed", "Spin Rate"],
            title="Shot Dispersion by Club",
            height=400
        )

        color_palette = px.colors.qualitative.Set2
        club_colors = {club: color_palette[i % len(color_palette)] for i, club in enumerate(filtered_df["Club"].unique())}

        for club in filtered_df["Club"].unique():
            club_data = filtered_df[filtered_df["Club"] == club]
            if len(club_data) > 2:
                x_mean = club_data["Offline"].mean()
                y_mean = club_data["Carry"].mean()
                x_std = club_data["Offline"].std()
                y_std = club_data["Carry"].std()

                # Convert RGB to RGBA with transparency
                base_color = club_colors[club]
                if base_color.startswith('rgb'):
                    rgba = base_color.replace('rgb', 'rgba').replace(')', ', 0.2)')
                else:
                    rgba = base_color

                fig_dispersion.add_shape(
                    type="circle",
                    xref="x",
                    yref="y",
                    x0=x_mean - x_std,
                    x1=x_mean + x_std,
                    y0=y_mean - y_std,
                    y1=y_mean + y_std,
                    line=dict(color=base_color, width=1),
                    fillcolor=rgba,
                    opacity=0.5,
                    layer="below"
                )

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

# --- Raw Table ---
with st.expander("Shot Data Table", expanded=False):
    st.dataframe(filtered_df.reset_index(drop=True).style.set_properties(**{'font-size': '12px'}), use_container_width=True)

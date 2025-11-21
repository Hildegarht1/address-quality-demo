# Streamlit app: app.py
# Usage:
# streamlit run app.py
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from pathlib import Path

st.set_page_config(layout="wide", page_title="Address Quality Dashboard")

OUTPUT_PARQUET = Path("outputs/addresses_clean.parquet")

st.title("Address Quality & Geocoding Dashboard")

if not OUTPUT_PARQUET.exists():
    st.error("No cleaned dataset found. Run notebooks/01_geocode.py first to produce outputs/addresses_clean.parquet.")
    st.stop()

df = pd.read_parquet(OUTPUT_PARQUET)

# KPI cards
total = len(df)
success_count = int(df["geocode_success"].sum())
success_rate = success_count / total * 100 if total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total addresses", total)
col2.metric("Geocode success", success_count)
col3.metric("Success rate", f"{success_rate:.1f}%")

# Filters
with st.sidebar:
    st.header("Filters")
    min_score = st.slider("Min match score", 0.0, 1.0, 0.0, 0.1)
    show_failed_only = st.checkbox("Show failed addresses only", value=False)
    city_list = sorted(df["city"].dropna().unique().tolist()) if "city" in df.columns else []
    selected_city = st.selectbox("City", ["All"] + city_list)

filtered = df.copy()
filtered = filtered[filtered["match_score"] >= min_score]
if show_failed_only:
    filtered = filtered[filtered["geocode_success"] == False]
if selected_city != "All":
    filtered = filtered[filtered["city"] == selected_city]

st.subheader("Map")
# Create folium map
if filtered[["lat", "lon"]].dropna().empty:
    st.info("No geocoded points to show on the map.")
else:
    center = [filtered["lat"].mean(), filtered["lon"].mean()]
    m = folium.Map(location=center, zoom_start=6)
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in filtered.dropna(subset=["lat", "lon"]).iterrows():
        tooltip = f"{row.get('original_address','')[:80]}<br>Score: {row.get('match_score',0)}"
        folium.Marker(location=[row["lat"], row["lon"]], tooltip=tooltip).add_to(marker_cluster)
    # Render map
    st_data = st_folium(m, width=900, height=500)

st.subheader("Failed / Low Quality Addresses")
fail_df = df[df["geocode_success"] == False].copy()
st.dataframe(fail_df[["original_address", "normalized_address"]].head(50))

st.subheader("Sample data (filtered)")
st.dataframe(filtered.head(100))
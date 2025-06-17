import streamlit as st
import geopandas as gpd
import pandas as pd

# FILE PATHS—these files must sit alongside app.py
SCHOOLS_GPKG     = "Schools.gpkg"
ADDRESSPTS_GPKG  = "AddressPoints.gpkg"

# LAYER NAMES (match exactly the names in your .gpkg files)
SCHOOL_LAYER     = "schools"
ADDRESS_LAYER    = "address"

# COORDINATE SYSTEMS
PROJECT_CRS = 3310  # California Albers (meters)
WEB_CRS     = 4326  # WGS84 lat/lon

@st.cache_data
def load_data():
    schools   = gpd.read_file(SCHOOLS_GPKG, layer=SCHOOL_LAYER).to_crs(PROJECT_CRS)
    addresses = gpd.read_file(ADDRESSPTS_GPKG, layer=ADDRESS_LAYER).to_crs(PROJECT_CRS)
    return schools, addresses

with st.spinner("Loading data…"):
    schools, addresses = load_data()

st.title("📫 LAUSD School Mailer: Buffer & Export")

# 1) select a school
school_list     = schools["labels"].sort_values().unique()
selected_school = st.selectbox("Select a School", school_list)

# 2) choose buffer radius
radius_miles = st.select_slider(
    "Buffer radius (miles)",
    options=[0.25, 0.5, 1.0, 2.0],
    value=0.5
)
radius_m = radius_miles * 1609.34  # miles → meters

# 3) buffer & filter
geom        = schools.loc[schools["labels"] == selected_school, "geometry"].iloc[0]
buffer_geom = geom.buffer(radius_m)
selected_addrs = addresses[addresses.within(buffer_geom)]

# 4) display & export
st.markdown(f"**Found {len(selected_addrs)} addresses** within **{radius_miles} miles** of **{selected_school}**")
if not selected_addrs.empty:
    st.map(selected_addrs.to_crs(WEB_CRS))
    df = pd.DataFrame({
        "address": selected_addrs["FullAddress_EnerGov"],
        "x":        selected_addrs.geometry.x,
        "y":        selected_addrs.geometry.y
    })
    csv = df.to_csv(index=False)
    st.download_button("⬇️ Download CSV", data=csv, file_name=f"{selected_school}_{radius_miles}mi.csv", mime="text/csv")
else:
    st.info("No addresses found for that selection.")

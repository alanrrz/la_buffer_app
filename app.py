import os, requests
import streamlit as st
import geopandas as gpd
import pandas as pd

# ─── DATA DOWNLOAD ─────────────────────────────────────────────────────
DATA_SOURCES = {
    "Schools.gpkg":        "https://my-bucket.s3.amazonaws.com/Schools.gpkg",
    "AddressPoints.gpkg":  "https://my-bucket.s3.amazonaws.com/AddressPoints.gpkg"
}
for fname, url in DATA_SOURCES.items():
    if not os.path.exists(fname):
        with st.spinner(f"Downloading {fname}…"):
            r = requests.get(url)
            r.raise_for_status()
            with open(fname, "wb") as f:
                f.write(r.content)

# ─── CONFIG ─────────────────────────────────────────────────────────────
SCHOOLS_GPKG    = "Schools.gpkg"
ADDRESSPTS_GPKG = "AddressPoints.gpkg"
SCHOOL_LAYER    = "schools"
ADDRESS_LAYER   = "address"
PROJECT_CRS     = 3310
WEB_CRS         = 4326

@st.cache_data
def load_data():
    schools   = gpd.read_file(SCHOOLS_GPKG, layer=SCHOOL_LAYER).to_crs(PROJECT_CRS)
    addrs     = gpd.read_file(ADDRESSPTS_GPKG, layer=ADDRESS_LAYER).to_crs(PROJECT_CRS)
    return schools, addrs

with st.spinner("Loading spatial data…"):
    schools, addresses = load_data()

# ─── APP UI ─────────────────────────────────────────────────────────────
st.title("📫 LAUSD School Mailer: Buffer & Export")
school_list     = schools["labels"].sort_values().unique()
selected_school = st.selectbox("Select a School", school_list)
radius_miles    = st.select_slider("Buffer (miles)", [0.25,0.5,1.0,2.0], value=0.5)
radius_m        = radius_miles * 1609.34

geom        = schools.loc[schools["labels"]==selected_school, "geometry"].iloc[0]
buffer_geom = geom.buffer(radius_m)
selected_addrs = addresses[addresses.within(buffer_geom)]

st.markdown(f"**Found {len(selected_addrs)} addresses** within **{radius_miles} mi** of **{selected_school}**")
if not selected_addrs.empty:
    st.map(selected_addrs.to_crs(WEB_CRS))
    df = pd.DataFrame({
        "address": selected_addrs["FullAddress_EnerGov"],
        "x":        selected_addrs.geometry.x,
        "y":        selected_addrs.geometry.y
    })
    csv = df.to_csv(index=False)
    st.download_button("⬇️ Download CSV", data=csv, file_name=f"{selected_school}.csv", mime="text/csv")
else:
    st.info("No addresses found.")

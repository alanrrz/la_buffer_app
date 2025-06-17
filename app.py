import os
import requests
import streamlit as st

# ─── GOOGLE DRIVE FILE DOWNLOAD ─────────────────────────────────────────
def download_file_from_google_drive(file_id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    # 1. Initial request
    response = session.get(URL, params={'id': file_id}, stream=True)
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value

    # 2. Confirm token if present
    if token:
        response = session.get(URL, params={'id': file_id, 'confirm': token}, stream=True)

    # 3. Save to disk in chunks
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                f.write(chunk)

# Map file names to their Drive IDs
DATA_SOURCES = {
    "Schools.gpkg":       "1XcGZvFmHdv4zmJBNb9MYHeIIjuPwMjGv",
    "AddressPoints.gpkg": "1_3_FEgj4V7uHigDN13KDueDhULGP6yWc"
}

for fname, file_id in DATA_SOURCES.items():
    if not os.path.exists(fname):
        with st.spinner(f"Downloading {fname}…"):
            download_file_from_google_drive(file_id, fname)

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

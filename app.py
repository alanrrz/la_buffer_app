import math
import pandas as pd
import streamlit as st

# ─── LOAD DATA ──────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    schools   = pd.read_csv("schools.csv")     # has 'label','lon','lat'
    addresses = pd.read_csv("addresses.csv")  # has 'address','lon','lat'
    return schools, addresses

schools, addresses = load_data()

# ─── APP HEADER ─────────────────────────────────────────────────────────
st.title("📫 LAUSD Mailer (CSV Edition)")
st.markdown("Pick a school and radius to get all addresses within that distance.")

# ─── USER CONTROLS ──────────────────────────────────────────────────────
selected = st.selectbox("Select a School", schools["label"].sort_values().unique())
radius_mi = st.slider("Buffer radius (miles)", min_value=0.25, max_value=2.0, value=0.5, step=0.25)

# Get chosen school coordinates
school = schools[schools["label"] == selected].iloc[0]
slon, slat = school.lon, school.lat

# ─── DISTANCE FUNCTION ──────────────────────────────────────────────────
def haversine(lon1, lat1, lon2, lat2):
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# Compute distances & filter
addresses["distance"] = addresses.apply(
    lambda r: haversine(slon, slat, r.lon, r.lat), axis=1
)
within = addresses[addresses["distance"] <= radius_mi]

# ─── RESULTS ───────────────────────────────────────────────────────────
st.markdown(f"**Found {len(within)} addresses** within **{radius_mi} mi** of **{selected}**")

if not within.empty:
    # Map preview (expects 'latitude','longitude' columns)
    map_df = within.rename(columns={"lat":"latitude", "lon":"longitude"})
    st.map(map_df[["latitude","longitude"]])

    # Downloadable CSV
    out = within[["address","lon","lat","distance"]].rename(
        columns={"lon":"longitude","lat":"latitude"}
    )
    csv = out.to_csv(index=False)
    st.download_button(
        "⬇️ Download Mailing List",
        data=csv,
        file_name=f"{selected.replace(' ','_')}_{radius_mi}mi.csv",
        mime="text/csv"
    )
else:
    st.info("No addresses found in that buffer.")

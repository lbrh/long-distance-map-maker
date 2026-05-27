import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import math
import os

MARKS_FILE = "map.csv"
LINES_FILE = "saved_lines.csv"


def haversine_nm(lat1, lon1, lat2, lon2):
    R_km = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return (R_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))) / 1.852


# Load only POINT marks (skip LINESTRING rows)
_raw = pd.read_csv(MARKS_FILE)
marks_df = _raw[_raw["WKT"].str.startswith("POINT")].dropna(subset=["Lat", "Long"]).copy()

marks_data = [
    {"name": str(r["Mark Name"]), "lat": float(r["Lat"]), "lng": float(r["Long"])}
    for _, r in marks_df.iterrows()
]

if "last_save_ts" not in st.session_state:
    st.session_state.last_save_ts = None

# ----------------------------
# Page
# ----------------------------
st.title("🏁 Port Phillip Race Mapper")

race_map = components.declare_component("race_map", path="map_component")
result = race_map(marks=marks_data, default=None)

# ----------------------------
# Handle save (only fires when user clicks Save inside the map component)
# ----------------------------
if result and result.get("action") == "save":
    ts = result.get("ts")
    if ts != st.session_state.last_save_ts:
        st.session_state.last_save_ts = ts

        route = result.get("route", [])
        name  = result.get("name", "Race 1")
        lookup = {m["name"]: m for m in marks_data}

        rows = []
        for i in range(len(route) - 1):
            a = lookup.get(route[i])
            b = lookup.get(route[i + 1])
            if a and b:
                rows.append({
                    "Route": name,
                    "From":  route[i],
                    "To":    route[i + 1],
                    "NM":    round(haversine_nm(a["lat"], a["lng"], b["lat"], b["lng"]), 2),
                })

        if rows:
            write_header = not os.path.exists(LINES_FILE)
            pd.DataFrame(rows).to_csv(LINES_FILE, mode="a", index=False, header=write_header)
            st.success(f"✅ Saved **{name}** — {len(rows)} leg{'s' if len(rows) != 1 else ''}")
        else:
            st.warning("Nothing to save — build a route with at least 2 marks first.")

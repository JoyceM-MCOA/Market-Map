import pandas as pd
import folium
from geopy.distance import geodesic

# -----------------------------
# SETTINGS
# -----------------------------
EXCEL_FILE = "Lakeway_market_map.xlsx"
OUTPUT_HTML = "Lakeway_market_map.html"

HUB_NAME = "THE SUMMIT AT LAKEWAY HEALTHCARE CTR"

RINGS = [
    (7,  "≈15 min"),
    (15, "≈30 min"),
    (25, "≈45 min"),
]

SHOW_LABELS_FOR = "ACH_ONLY"  # ALL | ACH_ONLY | NONE

MAP_TITLE = "Lakeway Post-Acute Market — Hub & Hospital"

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_excel(EXCEL_FILE)

for col in ["Beds", "Latitude", "Longitude"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Latitude", "Longitude"])

hub = df[df["Facility Name"].str.strip() == HUB_NAME].iloc[0]
hub_loc = (hub["Latitude"], hub["Longitude"])

# -----------------------------
# CREATE MAP (Google-like)
# -----------------------------
m = folium.Map(
    location=hub_loc,
    zoom_start=11,
    tiles="CartoDB positron",
    control_scale=True
)

# Tile toggles
folium.TileLayer("CartoDB positron", name="Light (Google-like)").add_to(m)
folium.TileLayer("CartoDB voyager", name="Detailed").add_to(m)
folium.TileLayer("OpenStreetMap", name="Standard").add_to(m)
folium.TileLayer("Esri.WorldImagery", name="Satellite").add_to(m)

# -----------------------------
# TITLE PANEL
# -----------------------------
title_html = f"""
<div style="
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    background: white;
    padding: 10px 18px;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    font-size: 16px;
    font-weight: bold;
">
    {MAP_TITLE}
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

# -----------------------------
# LEGEND
# -----------------------------
legend_html = """
<div style="
    position: fixed;
    bottom: 40px;
    left: 40px;
    z-index: 9999;
    background: white;
    padding: 10px 14px;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    font-size: 12px;
">
<b>Legend</b><br>
<span style="color:blue;">●</span> Hub SNF<br>
<span style="color:green;">●</span> Other SNFs<br>
<span style="color:red;">●</span> Acute Hospitals<br>
<span style="color:gray;">—</span> Hub → Hospital Distance<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# -----------------------------
# HUB MARKER
# -----------------------------
folium.Marker(
    hub_loc,
    tooltip=f"HUB: {hub['Facility Name']}",
    icon=folium.Icon(color="blue", icon="star")
).add_to(m)

# -----------------------------
# DRIVE-TIME RINGS (proxy)
# -----------------------------
for miles, label in RINGS:
    folium.Circle(
        hub_loc,
        radius=miles * 1609.34,
        color="blue",
        weight=2,
        fill=False,
        tooltip=f"{label} radius (~{miles} mi)"
    ).add_to(m)

# -----------------------------
# FACILITIES + LINES
# -----------------------------
for _, row in df.iterrows():
    loc = (row["Latitude"], row["Longitude"])
    dist_mi = geodesic(hub_loc, loc).miles

    ftype = row["FacilityType"].strip().upper()

    if row["Facility Name"].strip() == HUB_NAME:
        color = "blue"
    elif ftype == "SNF":
        color = "green"
    else:
        color = "red"

    beds = row["Beds"] if pd.notna(row["Beds"]) else 0
    radius = max(5, beds / 12)

    popup = (
        f"<b>{row['Facility Name']}</b><br>"
        f"Type: {row['FacilityType']}<br>"
        f"Beds: {beds}<br>"
        f"Provider ID: {row['Provider ID']}<br>"
        f"Distance from hub: {dist_mi:.1f} miles"
    )

    folium.CircleMarker(
        location=loc,
        radius=radius,
        color=color,
        fill=True,
        fill_opacity=0.75,
        popup=popup,
    ).add_to(m)

    # Distance lines to hospitals
    if ftype == "ACH" and row["Facility Name"].strip() != HUB_NAME:
        folium.PolyLine(
            locations=[hub_loc, loc],
            color="gray",
            weight=1,
            opacity=0.6
        ).add_to(m)

    # Labels
    if SHOW_LABELS_FOR == "ALL" or (SHOW_LABELS_FOR == "ACH_ONLY" and ftype == "ACH"):
        folium.Marker(
            loc,
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-size:10px;
                    background:white;
                    padding:2px 4px;
                    border-radius:3px;
                    border:1px solid #ccc;
                    max-width:220px;
                ">
                    {row['Facility Name']}
                </div>
                """
            )
        ).add_to(m)

# Layer control
folium.LayerControl(collapsed=False).add_to(m)

# -----------------------------
# SAVE
# -----------------------------
m.save(OUTPUT_HTML)
print(f"Created: {OUTPUT_HTML}")

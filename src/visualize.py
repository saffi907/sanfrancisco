"""
visualize.py
transit score bar chart and interactive folium map
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import folium
from folium.plugins import MarkerCluster

OUTPUT_DIR = "output"

TIER_COLORS = {
    "excellent": "#4CAF50",
    "good": "#8BC34A",
    "moderate": "#FFC107",
    "poor": "#F44336"
}


def plot_transit_scores(features):
    # bar chart of neighborhoods ranked by transit score
    df = features.sort_values("transit_score", ascending=True)
    colors = [TIER_COLORS.get(t, "#999") for t in df["tier"]]

    fig, ax = plt.subplots(figsize=(10, 12))
    ax.barh(df.index, df["transit_score"], color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("transit score")
    ax.set_title("sf neighborhoods ranked by transit access")
    ax.tick_params(axis="y", labelsize=8)

    legend_items = [Patch(facecolor=c, label=t) for t, c in TIER_COLORS.items()]
    ax.legend(handles=legend_items, loc="lower right", title="tier")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "transit_scores.png"), dpi=150)
    plt.close()


def create_map(features, neighborhoods, stops_with_nhood):
    # interactive folium map color-coded by cluster tier
    m = folium.Map(location=[37.76, -122.44], zoom_start=12, tiles="cartodbpositron")

    # color each neighborhood polygon
    for _, row in neighborhoods.iterrows():
        nhood_name = row["nhood"]
        if nhood_name not in features.index:
            continue
        info = features.loc[nhood_name]
        color = TIER_COLORS.get(info["tier"], "#999")

        # Add warning text if it's an anomaly
        anomaly_text = f"ANOMALY: {info['anomaly']}" if info["anomaly"] != "normal" else ""

        folium.GeoJson(
            row["geometry"].__geo_interface__,
            style_function=lambda x, c=color: {
                "fillColor": c,
                "color": "#333",
                "weight": 1,
                "fillOpacity": 0.5
            },
            tooltip=f"{nhood_name}: {info['tier']} ({info['stop_count']:.0f} stops, {info['route_diversity']:.0f} routes){anomaly_text}"
        ).add_to(m)

    # stop markers with clustering to avoid clutter
    marker_cluster = MarkerCluster(name="transit stops").add_to(m)
    for _, stop in stops_with_nhood.iterrows():
        folium.CircleMarker(
            location=[stop["LATITUDE"], stop["LONGITUDE"]],
            radius=2,
            color="#1565C0",
            fill=True,
            fill_opacity=0.6,
            popup=stop["STOPNAME"]
        ).add_to(marker_cluster)

    folium.LayerControl().add_to(m)
    map_path = os.path.join(OUTPUT_DIR, "transit_map.html")
    m.save(map_path)
"""
analysis.py
feature engineering, clustering, and anomaly detection
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTPUT_DIR = "output"


def compute_features(stops_with_nhood, route_nhood_map, neighborhoods):
    # build transit access features for each neighborhood

    # project to meters so area calculation is meaningful
    nhood_proj = neighborhoods.to_crs(epsg=3857)
    areas = nhood_proj.set_index("nhood").geometry.area / 1e6  # sq km

    stop_counts = stops_with_nhood.groupby("nhood")["STOPID"].count().rename("stop_count")
    route_diversity = route_nhood_map.groupby("nhood")["route"].nunique().rename("route_diversity")

    features = pd.DataFrame(index=neighborhoods["nhood"])
    features = features.join(stop_counts).join(route_diversity)
    features["area_km2"] = areas
    features = features.fillna(0)

    # derived features
    features["stop_density"] = features["stop_count"] / features["area_km2"]
    features["routes_per_km2"] = features["route_diversity"] / features["area_km2"]

    return features


def find_optimal_k(X_scaled, max_k=8):
    # elbow method to help pick k
    inertias = []
    k_range = range(2, max_k + 1)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)
    return list(k_range), inertias


def cluster_neighborhoods(features, k=4):
    # run k-means on the normalized features, assign tiers
    feature_cols = ["stop_count", "stop_density", "route_diversity", "routes_per_km2"]
    X = features[feature_cols].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # save elbow plot
    k_range, inertias = find_optimal_k(X_scaled)
    plt.figure(figsize=(6, 4))
    plt.plot(k_range, inertias, "o-", color="#2196F3")
    plt.xlabel("number of clusters (k)")
    plt.ylabel("inertia")
    plt.title("elbow method for optimal k")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "elbow_plot.png"), dpi=150)
    plt.close()

    # fit with chosen k
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    features["cluster"] = km.fit_predict(X_scaled)

    # composite score (weighted combination of features)
    features["transit_score"] = (
        features["stop_density"] * 0.4
        + features["routes_per_km2"] * 0.3
        + features["stop_count"] * 0.2
        + features["route_diversity"] * 0.1
    )

    # rank clusters so 0 = best access
    cluster_means = features.groupby("cluster")["transit_score"].mean().sort_values(ascending=False)
    rank_map = {c: i for i, c in enumerate(cluster_means.index)}
    features["cluster_rank"] = features["cluster"].map(rank_map)

    tier_names = {0: "excellent", 1: "good", 2: "moderate", 3: "poor"}
    features["tier"] = features["cluster_rank"].map(tier_names)

    return features


def detect_anomalies(features):
    # flag neighborhoods with unusually high or low transit scores using iqr
    q1 = features["transit_score"].quantile(0.25)
    q3 = features["transit_score"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    features["anomaly"] = "normal"
    features.loc[features["transit_score"] > upper, "anomaly"] = "unusually high"
    features.loc[features["transit_score"] < lower, "anomaly"] = "unusually low"

    anomalies = features[features["anomaly"] != "normal"]
    if not anomalies.empty:
        print(f"      -> flagged {len(anomalies)} anomaly/anomalies:")
        for nhood, row in anomalies.iterrows():
            print(f"         - {nhood}: {row['anomaly']} (score: {row['transit_score']:.1f})")

    return features
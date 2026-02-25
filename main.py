"""
sf transit access analysis
identifies which san francisco neighborhoods have the best public transit
access using clustering and anomaly detection on muni stop/route data.

data sources (data.sfgov.org):
  - muni stops: all transit stops in the sfmta system
  - analysis neighborhoods: official sf neighborhood boundaries
  - muni simple routes: route patterns and service categories
"""

import os
import warnings
from src.preprocess import load_stops, load_neighborhoods, load_routes
from src.preprocess import assign_stops_to_neighborhoods, assign_routes_to_neighborhoods
from src.analysis import compute_features, cluster_neighborhoods, detect_anomalies
from src.visualize import plot_transit_scores, create_map

warnings.filterwarnings("ignore")
os.makedirs("output", exist_ok=True)


def main():
    print("loading data...")
    stops = load_stops()
    neighborhoods = load_neighborhoods()
    routes = load_routes()

    print("preprocessing...")
    stops_with_nhood = assign_stops_to_neighborhoods(stops, neighborhoods)
    route_nhood_map = assign_routes_to_neighborhoods(routes, neighborhoods)

    print("running analysis...")
    features = compute_features(stops_with_nhood, route_nhood_map, neighborhoods)
    features = cluster_neighborhoods(features, k=4)
    features = detect_anomalies(features)

    print("generating output...")
    plot_transit_scores(features)
    create_map(features, neighborhoods, stops_with_nhood)

    print("done! check the output/ folder for results.")


if __name__ == "__main__":
    main()
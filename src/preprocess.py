"""
preprocess.py
handles loading the csv data and spatial joins
"""

import os
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point

DATA_DIR = "data"

# update these if your csv names differ
STOPS_FILE = "Muni_Stops_20260223.csv"
NEIGHBORHOODS_FILE = "Analysis_Neighborhoods_20260223.csv"
ROUTES_FILE = "Muni_Simple_Routes_20260223.csv"


def load_stops():
    # load muni stop data, keep what we need
    df = pd.read_csv(os.path.join(DATA_DIR, STOPS_FILE))
    df = df[["STOPID", "STOPNAME", "LATITUDE", "LONGITUDE"]].dropna()
    df["geometry"] = df.apply(lambda r: Point(r["LONGITUDE"], r["LATITUDE"]), axis=1)
    return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")


def load_neighborhoods():
    # load neighborhood boundaries from the wkt geometry column
    df = pd.read_csv(os.path.join(DATA_DIR, NEIGHBORHOODS_FILE))
    df["geometry"] = df["the_geom"].apply(wkt.loads)
    return gpd.GeoDataFrame(df[["nhood", "geometry"]], geometry="geometry", crs="EPSG:4326")


def load_routes():
    # load route patterns, extract route name and geometry
    df = pd.read_csv(os.path.join(DATA_DIR, ROUTES_FILE))
    df = df[["ROUTE_NAME", "DIRECTION", "SERVICE_CA", "shape"]].dropna(subset=["shape"])
    df["geometry"] = df["shape"].apply(wkt.loads)
    return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")


def assign_stops_to_neighborhoods(stops, neighborhoods):
    # point-in-polygon: figure out which neighborhood each stop belongs to
    joined = gpd.sjoin(stops, neighborhoods, how="left", predicate="within")
    joined = joined.dropna(subset=["nhood"])
    return joined


def assign_routes_to_neighborhoods(routes, neighborhoods):
    # find which routes pass through each neighborhood using intersection
    records = []
    for _, route in routes.iterrows():
        for _, nhood in neighborhoods.iterrows():
            if route.geometry.intersects(nhood.geometry):
                records.append({
                    "nhood": nhood["nhood"],
                    "route": route["ROUTE_NAME"],
                    "service": route["SERVICE_CA"]
                })
    return pd.DataFrame(records)
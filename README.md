# San Francisco Transit Access Analysis

## Aim

im visiting san francisco after spring break and will be relying on public transit to get around since i dont like driving in crowded cities. so i wanted to figure out which neighborhoods actually have the best transit access. the idea is that someone new to the city (like me) could use this to decide where to stay based on how well-connected the area is by muni.

the approach uses clustering to group neighborhoods into transit access tiers and anomaly detection to flag any outliers.

## Data Sources

all data is from https://data.sfgov.org/:

- Muni Stops (https://data.sfgov.org/Transportation/Muni-Stops/i28k-bkz6)
- Analysis Neighborhoods (https://data.sfgov.org/Geographic-Locations-and-Boundaries/Analysis-Neighborhoods/p5b7-5n3h)
- Muni Simple Routes (https://data.sfgov.org/Transportation/Muni-Simple-Routes/d5wm-7beg)

csv files are in `data/` folder.

## Setup

requires python 3.10+ and a few pip packages:

```
pip install pandas numpy scikit-learn matplotlib geopandas shapely folium
```

then just run:

```
python main.py
```

outputs go to the `output/` folder.

## Project Structure

```
main.py            entry point, runs the whole pipeline
src/
  preprocess.py    loads csv data, maps stops and routes to neighborhoods
  analysis.py      computes features, runs k-means clustering, detects anomalies
  visualize.py     generates the bar chart and interactive map
data/              the three csv datasets
output/            generated plots and map
```

## How It Works

### preprocessing
loads the three csv files using pandas. parses the neighborhood polygon boundaries from wkt format with shapely, then uses a point-in-polygon spatial join to figure out which neighborhood each muni stop belongs to. it also checks which routes pass through each neighborhood by intersecting route geometries with the neighborhood polygons.

### feature engineering
for each neighborhood we compute four features: stop count (total stops), stop density (stops per sq km), route diversity (number of unique routes), and routes per sq km.

### clustering
normalizes the features with standard scaling and runs k-means with k=4 to group neighborhoods into four tiers: excellent, good, moderate, and poor. we validated k=4 using the elbow method (see `output/elbow_plot.png`).

### anomaly detection
computes a weighted transit score from the features and uses the iqr method to flag outlier neighborhoods. anything beyond 1.5x the interquartile range from q1 or q3 gets flagged. im taking stats as well this semester so it was good to actually apply this to something real.

### visualization
generates three outputs:
- `transit_scores.png` - bar chart of all 41 neighborhoods ranked by score, color coded by tier
- `elbow_plot.png` - inertia vs k chart to validate the cluster count
- `transit_map.html` - interactive map with neighborhoods colored by tier and clickable stop markers

## Findings

the top neighborhoods for transit access were bayview hunters point, west of twin peaks, sunset/parkside, and mission. these all had high stop counts and good route diversity.

the worst were lincoln park, treasure island, seacliff, and the presidio. makes sense since those are mostly parks or low density areas.

bayview hunters point got flagged as an anomaly because it has way more stops (259) than any other neighborhood, which makes its score unusually high compared to the rest.

basically if youre visiting or moving to sf and want to get around without a car, stick to the excellent or good tier neighborhoods. avoid the outskirts and parks unless you have a ride.

## Acknowledgments

used the copilot autocomplete tool for help with code completion during development.
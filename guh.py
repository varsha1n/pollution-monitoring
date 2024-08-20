import ee
import geemap
import plotly.graph_objects as go
import matplotlib.colors as mcolors
import plotly.graph_objects as go
import numpy as np
import calendar

# Initialize the Earth Engine API
ee.Authenticate()
ee.Initialize(project="ee-narravarsha1")

# Define the city
city = "Agartala"

# Define the coordinates for city, India
city_lat = 23.831457
city_lon = 91.286778

# Define a buffer around the point to cover an area around city (50 kilometers)
buffer_radius = 50000  # 50 kilometers in meters
buffered_city_geometry = ee.Geometry.Point(city_lon, city_lat).buffer(buffer_radius)

# Set the specific month and year
year = 2019
month = 1
# Create the start and end dates for the specific month
start_date = f"{year}-{month:02d}-01"
end_date = f"{year}-12-31"

# Load the CO and H2O image collection (using OFFL dataset)
collection = (
    ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CO")
    .filterBounds(buffered_city_geometry)
    .filterDate(start_date, end_date)
    .select(["CO_column_number_density", "H2O_column_number_density"])
)

# Load the surface pressure image collection (using ECMWF ERA5 dataset)
surface_pressure_collection = (
    ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    .filterBounds(buffered_city_geometry)
    .filterDate(start_date, end_date)
    .select("surface_pressure")
)

# Calculate the mean over the collection for CO, H2O, and surface pressure
CO_mean = (
    collection.select("CO_column_number_density").mean().clip(buffered_city_geometry)
)
H2O_mean = (
    collection.select("H2O_column_number_density").mean().clip(buffered_city_geometry)
)
surface_pressure_mean = surface_pressure_collection.mean().clip(buffered_city_geometry)

# Constants
g = 9.82  # m/s^2
m_H2O = 0.01801528  # kg/mol
m_dry_air = 0.0289644  # kg/mol

# Calculate TC_dry_air
TC_dry_air = surface_pressure_mean.divide(g * m_dry_air).subtract(
    H2O_mean.multiply(m_H2O / m_dry_air)
)

# Calculate XCO
XCO = CO_mean.divide(TC_dry_air).rename("XCO")

# Convert XCO to ppb
XCO_ppb = XCO.multiply(1e9).rename("XCO_ppb")

# Calculate the minimum and maximum CO values
min_max = XCO_ppb.reduceRegion(
    reducer=ee.Reducer.minMax(),
    geometry=buffered_city_geometry,
    scale=1113.2,
    maxPixels=1e9,
)

# Get min and max values and round them to three decimal places
CO_min = round(min_max.get("XCO_ppb_min").getInfo(), 3)
CO_max = round(min_max.get("XCO_ppb_max").getInfo(), 3)

# Print the minimum and maximum CO values
print("Minimum CO value:", CO_min)
print("Maximum CO value:", CO_max)

# Create a map centered around city
m = geemap.Map(center=[city_lat, city_lon], zoom=10)

# Define visualization parameters
vis_params = {
    "min": 0,
    "max": 500,
    "palette": [
        "#5e4fa2",
        "#378dba",
        "#73c7a4",
        "#bee5a0",
        "#f0f9a8",
        "#feeda1",
        "#fdbe6e",
        "#f57948",
        "#d8424d",
        "#9e0142",
    ],  # Spectral color palette
}

# Apply a 98% stretch
stretch = XCO_ppb.reduceRegion(
    reducer=ee.Reducer.percentile([2, 98]),
    geometry=buffered_city_geometry,
    scale=1113.2,
    maxPixels=1e9,
)
min_val = stretch.get("XCO_ppb_p2").getInfo()
max_val = stretch.get("XCO_ppb_p98").getInfo()
vis_params["min"] = min_val
vis_params["max"] = max_val

# Add XCO concentration layer to the map
m.addLayer(XCO_ppb, vis_params, "XCO_ppb Concentration")


# Define the color palette and value range for Plotly color bar
color_palette = [
    "#5e4fa2",
    "#378dba",
    "#73c7a4",
    "#bee5a0",
    "#f0f9a8",
    "#feeda1",
    "#fdbe6e",
    "#f57948",
    "#d8424d",
    "#9e0142",
]

# Create a figure with only a horizontal colorbar
fig = go.Figure()

# Add a colorbar trace with no data
fig.add_trace(
    go.Heatmap(
        z=[np.linspace(min_val, max_val, 100)],
        colorscale=color_palette,
        colorbar=dict(
            title="XCO Concentration (ppb)",
            titleside="top",
            tickvals=[min_val, max_val],
            ticktext=[f"{min_val:.3f}", f"{max_val:.3f}"],
            orientation="h",  # Horizontal colorbar
        ),
        showscale=True,
    )
)

# Update layout to remove axes and labels
fig.update_layout(
    xaxis=dict(showticklabels=False),
    yaxis=dict(showticklabels=False),
    coloraxis_colorbar=dict(
        title="XCO Concentration (ppb)",
        titleside="top",
        tickvals=[min_val, max_val],
        ticktext=[f"{min_val}", f"{max_val}"],
        orientation="h",  # Horizontal colorbar
    ),
    height=200,  # Adjust height for better visualization
)

# Save the colorbar figure as an image
fig.write_image("horizontal_colorbar_legend.png")

# Optionally, display the figure
fig.show(renderer="browser")  # Opens the plot in your default web browser


# Save the map to an HTML file and then open it in a browser
m.to_html("city_map.html")

# Optionally display the saved HTML in the default web browser
import webbrowser

webbrowser.open("city_map.html")

import ee
import geemap
import numpy as np
import folium
from folium import plugins
import math
import calendar

# Initialize the Earth Engine API
ee.Authenticate()
ee.Initialize(project="ee-sandhyarajagiri930")

# Define the coordinates for city, India
city_lat = 17.385044
city_lon = 78.486671
city_coords = [city_lat, city_lon]

# Define a buffer around the point to cover an area around city (50 kilometers)
buffer_radius = 50000  # 50 kilometers in meters


# Function to calculate the bounding box
def get_bounding_box(center_lat, center_lon, radius_m):
    # Constants
    km_per_degree_lat = 111  # Approximate value

    # Calculate latitude degrees for the radius
    lat_degree_diff = radius_m / 1000 / km_per_degree_lat

    # Calculate longitude degrees for the radius (considering latitude)
    lon_degree_diff = (
        radius_m / 1000 / (km_per_degree_lat * np.cos(np.radians(center_lat)))
    )

    # Bounding box coordinates
    min_lat = center_lat - lat_degree_diff
    max_lat = center_lat + lat_degree_diff
    min_lon = center_lon - lon_degree_diff
    max_lon = center_lon + lon_degree_diff

    return [min_lon, min_lat, max_lon, max_lat]


# Calculate bounding box for the buffer radius
bounding_box = get_bounding_box(city_lat, city_lon, buffer_radius)

# Define the bounding box geometry
region = ee.Geometry.Rectangle(bounding_box)

# Set the specific month and year
year = 2019
month = 1
# Create the start and end dates for the specific month
start_date = f"{year}-{month:02d}-01"
end_date = f"{year}-12-31"


# Function to calculate wind speed and direction
def compute_wind_speed_and_direction(image):
    u = image.select("u_component_of_wind_10m")
    v = image.select("v_component_of_wind_10m")

    # Compute wind direction in radians
    wind_dir_radians = u.atan2(v).rename("wind_direction_radians")

    # Convert radians to degrees
    wind_dir_degrees = (
        wind_dir_radians.multiply(180).divide(math.pi).rename("wind_direction_degrees")
    )

    # Compute wind speed
    wind_speed = (u.pow(2).add(v.pow(2))).sqrt().rename("wind_speed_m_s")

    return image.addBands([wind_speed, wind_dir_degrees])


# Filter the ECMWF ERA5 image collection for Hyderabad and the specified date range
era5_collection = (
    ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    .filterBounds(region)
    .filterDate(start_date, end_date)
    .select(["u_component_of_wind_10m", "v_component_of_wind_10m"])
)

# Compute wind speed and direction
era5_with_wind = era5_collection.map(compute_wind_speed_and_direction)

# Compute the mean wind direction over the specified date range
mean_wind_direction = era5_with_wind.select("wind_direction_degrees").mean()

# Print the mean wind direction
print("Mean wind direction:", mean_wind_direction.getInfo())

# Create a map centered around Hyderabad
map_city = folium.Map(location=city_coords, zoom_start=8)

# Add a marker for Hyderabad
folium.Marker(location=city_coords, popup="Hyderabad").add_to(map_city)

# Add wind direction arrows
wind_dir_layer = plugins.FeatureGroupSubGroup(map_city, "Wind Direction")
map_city.add_child(wind_dir_layer)

# Create sampling points and add arrows
for lat in np.linspace(bounding_box[1], bounding_box[3], 10):
    for lon in np.linspace(bounding_box[0], bounding_box[2], 10):
        point = ee.Geometry.Point(lon, lat)
        direction = mean_wind_direction.reduceRegion(ee.Reducer.first(), point).get(
            "wind_direction_degrees"
        )
        if direction.getInfo() is not None:
            wind_dir = direction.getInfo()
            folium.Marker(
                [lat, lon],
                icon=folium.DivIcon(
                    html=f"<div style='transform: rotate({wind_dir}deg); color: black; font-size: 24px;'>&#8593;</div>"
                ),
            ).add_to(wind_dir_layer)

# Add layer control and display the map
folium.LayerControl().add_to(map_city)
map_city

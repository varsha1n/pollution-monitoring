import sys
import ee
import requests
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as ticker
import os

# Initialize the Earth Engine API
ee.Authenticate()
ee.Initialize(project="ee-narravarsha1")


def CO_Time_Series(city, date, plot_file_path):

    start_date, end_date = date[:10], date[13:]
    # Define city coordinates
    city_coords = {
        "Hyderabad": (17.3850, 78.4867),
        "Mumbai": (19.0760, 72.8777),
        "Banglore": (12.9716, 77.5946),
        "Kolkata": (22.5726, 88.3639),
        "Pune": (18.5204, 73.8567),
    }

    lat, long = city_coords.get(
        city, (13.0827, 80.2707)
    )  # Default to Chennai if city not found

    # Define a buffer around the point to cover an area around Bangalore (25 kilometers)
    buffer_radius = 25000  # 25 kilometers in meters
    buffered_bangalore_geometry = ee.Geometry.Point(long, lat).buffer(buffer_radius)

    # Load the CO image collection
    co_collection = (
        ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CO")
        .filterBounds(buffered_bangalore_geometry)
        .filterDate(start_date, end_date)
        .select("CO_column_number_density")
    )

    # Load the surface pressure image collection (using ECMWF ERA5 dataset)
    surface_pressure_collection = (
        ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
        .filterBounds(buffered_bangalore_geometry)
        .filterDate(start_date, end_date)
        .select("surface_pressure")
    )

    # Calculate the mean over the collection for CO and surface pressure
    CO_mean = co_collection.mean().clip(buffered_bangalore_geometry)
    surface_pressure_mean = surface_pressure_collection.mean().clip(
        buffered_bangalore_geometry
    )

    # Constants
    g = 9.82  # m/s^2
    m_CO = 0.02801  # kg/mol (CO molar mass)
    m_dry_air = 0.0289644  # kg/mol

    # Calculate TC_dry_air
    TC_dry_air = surface_pressure_mean.divide(g * m_dry_air)

    # Calculate XCO
    XCO = CO_mean.divide(TC_dry_air).rename("XCO")

    # Convert XCO to ppb
    XCO_ppb = XCO.multiply(1e9).rename("XCO_ppb")

    # Calculate the minimum and maximum CO values
    min_max = XCO_ppb.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=buffered_bangalore_geometry,
        scale=1113.2,
        maxPixels=1e9,
    )

    # Get min and max values and round them to two decimal places
    CO_min = round(min_max.get("XCO_ppb_min").getInfo(), 3)
    CO_max = round(min_max.get("XCO_ppb_max").getInfo(), 3)

    # Print the minimum and maximum CO values
    print("Minimum CO value:", CO_min)
    print("Maximum CO value:", CO_max)

    # Define a color palette based on CO concentration levels
    palette = [
        "#9e0142",
        "#d8424d",
        "#f57948",
        "#fdbe6e",
        "#feeda1",
        "#f0f9a8",
        "#bee5a0",
        "#73c7a4",
        "#378dba",
        "#5e4fa2",
    ]

    # Get a URL to a thumbnail image of the CO concentration data
    thumbnail_url = XCO_ppb.getThumbURL(
        {
            "min": CO_min,
            "max": CO_max,
            "region": buffered_bangalore_geometry.bounds().getInfo()["coordinates"],
            "dimensions": 512,
            "palette": palette,
        }
    )

    # Download the image and convert it to a NumPy array
    response = requests.get(thumbnail_url)
    img = Image.open(BytesIO(response.content))
    img_array = np.array(img)

    # Get the geographic extent
    coords = buffered_bangalore_geometry.bounds().getInfo()["coordinates"][0]
    extent = [coords[0][0], coords[2][0], coords[0][1], coords[2][1]]

    # Create a custom colormap
    custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", palette)

    # Plot the image using Matplotlib with the custom colormap
    fig, ax = plt.subplots()  # Create a figure and axes
    cax = ax.imshow(
        img_array, extent=extent, origin="upper", cmap=custom_cmap
    )  # Specify the custom colormap
    ax.set_title("CO Concentration around {city} ({start_date} to {end_date})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Define the number of ticks
    num_ticks = 5

    # Calculate the interval between ticks
    interval = (CO_max - CO_min) / (num_ticks - 1)

    # Calculate the tick positions
    tick_positions = [CO_min + i * interval for i in range(num_ticks)]

    # Create a dummy ScalarMappable to use with the colorbar
    norm = plt.Normalize(vmin=CO_min, vmax=CO_max)
    sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
    sm.set_array([])

    # Create the colorbar
    cbar = plt.colorbar(sm, ax=ax, orientation="vertical")
    cbar.set_label("CO Concentration (ppb)")

    # Set ticker to manually specify tick positions
    tick_locator = ticker.FixedLocator(tick_positions)
    cbar.locator = tick_locator
    cbar.update_ticks()

    # Set custom tick labels
    tick_labels = ["{:.3f}".format(value) for value in tick_positions]
    cbar.ax.set_yticklabels(tick_labels, ha="left")

    # Save plot to the file (overwrites the existing file)
    plt.savefig(plot_file_path, bbox_inches="tight", dpi=300)
    plt.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python CO.py <city> <date>")
        sys.exit(1)

    city = sys.argv[1]
    date = sys.argv[2]
    plot_file_path = "plots/latest_plot.png"  # Static filename
    CO_Time_Series(city, date, plot_file_path)

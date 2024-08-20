import ee
import requests
from PIL import Image
import numpy as np
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from io import BytesIO
from datetime import datetime, timedelta
import sys
from datetime import datetime, timedelta

# Initialize the Earth Engine API
ee.Authenticate()
ee.Initialize(project="ee-narravarsha1")


def CO_Map(city, start_date, end_date, plot_file_path):

    # Define city coordinates
    city_coords = {
        "Mumbai": (19.076090, 72.877426),
        "Delhi": (28.704060, 77.102493),
        "Chennai": (13.082680, 80.270718),
        "Kolkata": (22.572646, 88.363895),
        "Bangalore": (12.971599, 77.594566),
        "Pune": (18.520430, 73.856743),
        "Ahmedabad": (23.022505, 72.571365),
        "Surat": (21.170240, 72.831062),
        "Agra": (27.176670, 78.008072),
        "Chandigarh": (30.733315, 76.779419),
        "Asansol": (23.683333, 86.983333),
        "Moradabad": (28.838686, 78.773331),
        "Muzaffarpur": (26.120886, 85.364720),
        "Patna": (25.594095, 85.137566),
        "Agartala": (23.831457, 91.286778),
        "Bhopal": (23.259933, 77.412613),
        "Rourkela": (22.260423, 84.853584),
        "Jodhpur": (26.238947, 73.024309),
        "Indore": (22.719568, 75.857727),
        "Hyderabad": (17.3850, 78.4867),
    }

    city = "Chennai"  # Replace with the city you are looking for
    lat, long = city_coords.get(
        city, (13.0827, 80.2707)
    )  # Default to Chennai if city not found
    # Define the coordinates for city, India
    lat = 17.385044
    long = 78.486671

    # Define a buffer around the point to cover an area around city (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_city_geometry = ee.Geometry.Point(long, lat).buffer(buffer_radius)

    # Load the NO2 and H2O image collection (using OFFL dataset)
    collection = (
        ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2")
        .filterBounds(buffered_city_geometry)
        .filterDate(start_date, end_date)
        .select("NO2_column_number_density")
    )

    watervapor_collection = (
        ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CO")
        .filterBounds(buffered_city_geometry)
        .filterDate(start_date, end_date)
        .select("H2O_column_number_density")
    )

    # Load the surface pressure image collection (using ECMWF ERA5 dataset)
    surface_pressure_collection = (
        ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
        .filterBounds(buffered_city_geometry)
        .filterDate(start_date, end_date)
        .select("surface_pressure")
    )

    # Calculate the mean over the collection for CO, H2O, and surface pressure
    NO2_mean = (
        collection.select("NO2_column_number_density")
        .mean()
        .clip(buffered_city_geometry)
    )
    watervapor_mean = watervapor_collection.mean().clip(buffered_city_geometry)
    surface_pressure_mean = surface_pressure_collection.mean().clip(
        buffered_city_geometry
    )

    # Constants
    g = 9.82  # m/s^2
    m_H2O = 0.01801528  # kg/mol
    m_dry_air = 0.0289644  # kg/mol

    # Calculate TC_dry_air
    TC_dry_air = surface_pressure_mean.divide(g * m_dry_air).subtract(
        watervapor_mean.multiply(m_H2O / m_dry_air)
    )

    # Calculate XNO2
    XNO2 = NO2_mean.divide(TC_dry_air).rename("XNO2")

    # Convert XNO2 to ppb
    XNO2_ppb = XNO2.multiply(1e9).rename("XNO2_ppb")

    # Calculate the minimum and maximum NO2 values
    min_max = XNO2_ppb.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=buffered_city_geometry,
        scale=1113.2,
        maxPixels=1e9,
    )

    # Get min and max values and round them to two decimal places
    NO2_min = round(min_max.get("XNO2_ppb_min").getInfo(), 3)
    NO2_max = round(min_max.get("XNO2_ppb_max").getInfo(), 3)

    # Print the minimum and maximum NO2 values
    print("Minimum NO2 value:", NO2_min)
    print("Maximum NO2 value:", NO2_max)

    # Define a color palette based on NO2 concentration levels
    palette = [
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

    # Get a URL to a thumbnail image of the NO2 concentration data
    thumbnail_url = XNO2_ppb.getThumbURL(
        {
            "min": NO2_min,
            "max": NO2_max,
            "region": buffered_city_geometry.bounds().getInfo()["coordinates"],
            "dimensions": 512,
            "palette": palette,
        }
    )

    # Download the image and convert it to a NumPy array
    response = requests.get(thumbnail_url)
    img = Image.open(BytesIO(response.content))
    img_array = np.array(img)

    # Get the geographic extent
    coords = buffered_city_geometry.bounds().getInfo()["coordinates"][0]
    extent = [coords[0][0], coords[2][0], coords[0][1], coords[2][1]]

    # Create a custom colormap
    custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", palette)

    # Plot the image using Matplotlib with the custom colormap
    fig, ax = plt.subplots()  # Create a figure and axes
    cax = ax.imshow(
        img_array, extent=extent, origin="upper", cmap=custom_cmap
    )  # Specify the custom colormap

    # Assuming start_date and end_date are in the format 'YYYY-MM-DD'

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Add one day to start_date

    # Calculate the difference in days
    date_diff = (end_date - start_date).days

    # Check if the difference is less than 3 days
    if date_diff < 3:
        start_date += timedelta(days=1)
        ax.set_title(
            f"CO Concentration around {city} from {start_date.strftime('%Y-%m-%d')}"
        )
    else:
        ax.set_title(
            f"CO Concentration around {city} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
    ax.set_xlabel("Longitude (E°)")
    ax.set_ylabel("Latitude (N°)")

    # Define the number of ticks
    num_ticks = 5

    # Calculate the interval between ticks
    interval = (NO2_max - NO2_min) / (num_ticks - 1)

    # Calculate the tick positions
    tick_positions = [NO2_min + i * interval for i in range(num_ticks)]

    # Create a dummy ScalarMappable to use with the colorbar
    norm = plt.Normalize(vmin=NO2_min, vmax=NO2_max)
    sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
    sm.set_array([])

    # Create the colorbar
    cbar = plt.colorbar(sm, ax=ax, orientation="vertical")
    cbar.set_label("NO2 Concentration (ppb)")

    # Set ticker to manually specify tick positions
    tick_locator = ticker.FixedLocator(tick_positions)
    cbar.locator = tick_locator
    cbar.update_ticks()

    # Set custom tick labels
    tick_labels = ["{:.3f}".format(value) for value in tick_positions]
    cbar.ax.set_yticklabels(tick_labels, ha="left")

    plt.savefig(plot_file_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Plot saved successfully to {plot_file_path}.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python CO.py <city> <start_date> <end_date>")
        sys.exit(1)

    city = sys.argv[1]
    startDate = sys.argv[2]
    endDate = sys.argv[3]
    plot_file_path = "plots/latest_Map.png"  # Static filename
    CO_Map(city, startDate, endDate, plot_file_path)

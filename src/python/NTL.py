import ee
import requests
from PIL import Image
import numpy as np
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from io import BytesIO
import sys

# Initialize the Earth Engine API
ee.Authenticate()
ee.Initialize(project="ee-narravarsha1")


def NTL(city, start_date, end_date):
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

    lat, long = city_coords.get(
        city, (13.0827, 80.2707)
    )  # Default to Chennai if city not found

    # Define a buffer around the point to cover an area around the selected city (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_city_geometry = ee.Geometry.Point([long, lat]).buffer(buffer_radius)

    # Filter the NOAA VIIRS image collection for specified city and date range
    viirs_collection = (
        ee.ImageCollection("NOAA/VIIRS/001/VNP46A2")
        .filterBounds(buffered_city_geometry)
        .filterDate(start_date, end_date)
        .select("Gap_Filled_DNB_BRDF_Corrected_NTL")
        .mean()
        .clip(buffered_city_geometry)
    )

    # Define visualization parameters
    vis_params_NTL = {
        "min": 0,
        "max": 100,
        "palette": ["black", "purple", "cyan", "green", "yellow", "red", "white"],
    }

    # Calculate the minimum and maximum NTL values
    min_max = viirs_collection.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=buffered_city_geometry,
        scale=500,
        maxPixels=1e9,
    )

    # Get min and max values and round them to two decimal places
    NTL_min = round(min_max.get("Gap_Filled_DNB_BRDF_Corrected_NTL_min").getInfo(), 3)
    NTL_max = round(min_max.get("Gap_Filled_DNB_BRDF_Corrected_NTL_max").getInfo(), 3)

    # Print the minimum and maximum NTL values
    print("Minimum NTL value:", NTL_min)
    print("Maximum NTL value:", NTL_max)

    # Get a URL to a thumbnail image of the NTL data
    thumbnail_url = viirs_collection.getThumbURL(
        {
            "min": NTL_min,
            "max": NTL_max,
            "region": buffered_city_geometry.bounds().getInfo()["coordinates"],
            "dimensions": 512,
            "palette": vis_params_NTL["palette"],
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
    custom_cmap = LinearSegmentedColormap.from_list(
        "custom_cmap", vis_params_NTL["palette"]
    )

    # Plot the image using Matplotlib with the custom colormap
    fig, ax = plt.subplots()
    cax = ax.imshow(img_array, extent=extent, origin="upper", cmap=custom_cmap)
    ax.set_title(f"NTL around {city} in {year}")
    ax.set_xlabel("Longitude (E°)")
    ax.set_ylabel("Latitude (N°)")

    # Define the number of ticks
    num_ticks = 5

    # Calculate the interval between ticks
    interval = (NTL_max - NTL_min) / (num_ticks - 1)

    # Calculate the tick positions
    tick_positions = [NTL_min + i * interval for i in range(num_ticks)]

    # Create a dummy ScalarMappable to use with the colorbar
    norm = plt.Normalize(vmin=NTL_min, vmax=NTL_max)
    sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
    sm.set_array([])

    # Create the colorbar
    cbar = plt.colorbar(sm, ax=ax, orientation="vertical")
    cbar.set_label("NTL Value")

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
    year = sys.argv[2]
    half_year = sys.argv[3]
    if half_year == "jan-jun":
        # Create the start and end dates for the specific month
        start_date = f"{year}-01-01"
        end_date = f"{year}-06-30"
    elif half_year == "jan-dec":
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    else:
        start_date = f"{year}-07-01"
        end_date = f"{year}-12-30"

    plot_file_path = "plots/NTL.png"  # Static filename
    NTL(city, start_date, end_date)

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


def HCHO_Map(city, date, plot_file_path):

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

    # Define a buffer around the point to cover an area around the selected city (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_city_geometry = ee.Geometry.Point([long, lat]).buffer(buffer_radius)

    # Load the HCHO image collection (using OFFL dataset)
    collection_HCHO = (
        ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_HCHO")
        .filterBounds(buffered_city_geometry)
        .filterDate("2019-01-01", "2019-12-31")
        .select("tropospheric_HCHO_column_number_density")
    )  # Updated band name

    # Load the surface pressure image collection (using ECMWF ERA5 dataset)
    surface_pressure_collection = (
        ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
        .filterBounds(buffered_city_geometry)
        .filterDate("2019-01-01", "2019-12-31")
        .select("surface_pressure")
    )

    # Calculate the mean over the collection for HCHO and surface pressure
    HCHO_mean = collection_HCHO.mean().clip(buffered_city_geometry)
    surface_pressure_mean = surface_pressure_collection.mean().clip(
        buffered_city_geometry
    )

    # Constants
    g = 9.82  # m/s^2
    m_dry_air = 0.0289644  # kg/mol

    # Calculate TC_dry_air
    TC_dry_air = surface_pressure_mean.divide(g * m_dry_air)

    # Calculate XHCHO
    XHCHO = HCHO_mean.divide(TC_dry_air).rename("XHCHO")

    # Convert XHCHO to ppb
    XHCHO_ppb = XHCHO.multiply(1e9).rename("XHCHO_ppb")

    # Calculate the minimum and maximum HCHO values
    min_max_HCHO = XHCHO_ppb.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=buffered_city_geometry,
        scale=1113.2,
        maxPixels=1e9,
    )

    # Get min and max values and round them to two decimal places
    HCHO_min = round(min_max_HCHO.get("XHCHO_ppb_min").getInfo(), 3)
    HCHO_max = round(min_max_HCHO.get("XHCHO_ppb_max").getInfo(), 3)

    # Print the minimum and maximum HCHO values
    print("Minimum HCHO value:", HCHO_min)
    print("Maximum HCHO value:", HCHO_max)

    # Define a color palette based on HCHO concentration levels
    palette_HCHO = [
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

    # Get a URL to a thumbnail image of the HCHO concentration data
    thumbnail_url_HCHO = XHCHO_ppb.getThumbURL(
        {
            "min": HCHO_min,
            "max": HCHO_max,
            "region": buffered_city_geometry.bounds().getInfo()["coordinates"],
            "dimensions": 512,
            "palette": palette_HCHO,
        }
    )

    # Download the image and convert it to a NumPy array
    response_HCHO = requests.get(thumbnail_url_HCHO)
    img_HCHO = Image.open(BytesIO(response_HCHO.content))
    img_array_HCHO = np.array(img_HCHO)

    # Get the geographic extent
    coords = buffered_city_geometry.bounds().getInfo()["coordinates"][0]
    extent = [coords[0][0], coords[2][0], coords[0][1], coords[2][1]]

    # Filter the NOAA VIIRS image collection for the specified city and date range
    viirs_collection = (
        ee.ImageCollection("NOAA/VIIRS/001/VNP46A2")
        .filterBounds(buffered_city_geometry)
        .filterDate("2021-01-01", "2021-12-31")
        .select("Gap_Filled_DNB_BRDF_Corrected_NTL")
        .mean()
        .clip(buffered_city_geometry)
    )

    # Calculate the minimum and maximum NTL values
    min_max_NTL = viirs_collection.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=buffered_city_geometry,
        scale=500,
        maxPixels=1e9,
    )

    # Get min and max values and round them to two decimal places
    NTL_min = round(
        min_max_NTL.get("Gap_Filled_DNB_BRDF_Corrected_NTL_min").getInfo(), 3
    )
    NTL_max = round(
        min_max_NTL.get("Gap_Filled_DNB_BRDF_Corrected_NTL_max").getInfo(), 3
    )

    # Print the minimum and maximum NTL values
    print("Minimum NTL value:", NTL_min)
    print("Maximum NTL value:", NTL_max)

    # Apply threshold to NTL data
    NTL_threshold = 30
    viirs_thresholded = viirs_collection.gt(NTL_threshold).selfMask()

    # Define a white color palette for NTL values greater than threshold
    palette_NTL = ["white"]

    # Get a URL to a thumbnail image of the thresholded NTL data
    thumbnail_url_NTL = viirs_thresholded.getThumbURL(
        {
            "min": 1,  # As the mask will have values of 1 for true
            "max": 1,
            "region": buffered_city_geometry.bounds().getInfo()["coordinates"],
            "dimensions": 512,
            "palette": palette_NTL,
        }
    )

    # Download the image and convert it to a NumPy array
    response_NTL = requests.get(thumbnail_url_NTL)
    img_NTL = Image.open(BytesIO(response_NTL.content))
    img_array_NTL = np.array(img_NTL)

    # Create a custom colormap for HCHO
    custom_cmap_HCHO = LinearSegmentedColormap.from_list(
        "custom_cmap_HCHO", palette_HCHO
    )

    # Create a custom colormap for NTL
    custom_cmap_NTL = LinearSegmentedColormap.from_list("custom_cmap_NTL", palette_NTL)

    # Plot the images using Matplotlib with the custom colormaps
    fig, ax = plt.subplots()

    # Plot HCHO concentration image
    cax_HCHO = ax.imshow(
        img_array_HCHO, extent=extent, origin="upper", cmap=custom_cmap_HCHO
    )

    # Overlay NTL image with 40% opacity
    cax_NTL = ax.imshow(
        img_array_NTL, extent=extent, origin="upper", cmap=custom_cmap_NTL, alpha=1
    )

    # Set title and labels
    ax.set_title("HCHO Concentration and NTL around Hyderabad in 2019 (50km radius)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Define the number of ticks
    num_ticks = 5

    # Calculate the interval between ticks for HCHO
    interval_HCHO = (HCHO_max - HCHO_min) / (num_ticks - 1)

    # Calculate the tick positions for HCHO
    tick_positions_HCHO = [HCHO_min + i * interval_HCHO for i in range(num_ticks)]

    # Create a dummy ScalarMappable to use with the colorbar for HCHO
    norm_HCHO = plt.Normalize(vmin=HCHO_min, vmax=HCHO_max)
    sm_HCHO = plt.cm.ScalarMappable(cmap=custom_cmap_HCHO, norm=norm_HCHO)
    sm_HCHO.set_array([])

    # Create the colorbar for HCHO
    cbar_HCHO = plt.colorbar(sm_HCHO, ax=ax, orientation="vertical")
    cbar_HCHO.set_label("HCHO Concentration (ppb)")

    # Set ticker to manually specify tick positions for HCHO
    tick_locator_HCHO = ticker.FixedLocator(tick_positions_HCHO)
    cbar_HCHO.locator = tick_locator_HCHO
    cbar_HCHO.update_ticks()

    # Set custom tick labels for HCHO
    tick_labels_HCHO = ["{:.3f}".format(value) for value in tick_positions_HCHO]
    cbar_HCHO.ax.set_yticklabels(tick_labels_HCHO, ha="left")

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
    HCHO_Map(city, date, plot_file_path)

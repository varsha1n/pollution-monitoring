import ee
import sys
import requests
from PIL import Image
import numpy as np
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from io import BytesIO

# Initialize the Earth Engine API
ee.Authenticate()
ee.Initialize(project="ee-narravarsha1")


def SO2_Map(city, start_date, end_date, plot_file_path):

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
    # Define the coordinates for the selected city in Indi# Define the coordinates for the selected city in India
    lat = 17.385044
    long = 78.486671
    city_coords = [lat, long]

    # Define a buffer around the point to cover an area around the selected city (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_city_geometry = ee.Geometry.Point([long, lat]).buffer(buffer_radius)

    # Load the SO2 image collection (using OFFL dataset)
    collection_SO2 = (
        ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_SO2")
        .filterBounds(buffered_city_geometry)
        .filterDate(start_date, end_date)
        .select("SO2_column_number_density")
    )

    # Load the surface pressure image collection (using ECMWF ERA5 dataset)
    surface_pressure_collection = (
        ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
        .filterBounds(buffered_city_geometry)
        .filterDate(start_date, end_date)
        .select("surface_pressure")
    )

    # Calculate the mean over the collection for SO2 and surface pressure
    SO2_mean = collection_SO2.mean().clip(buffered_city_geometry)
    surface_pressure_mean = surface_pressure_collection.mean().clip(
        buffered_city_geometry
    )

    # Constants
    g = 9.82  # m/s^2
    m_dry_air = 0.0289644  # kg/mol

    # Calculate TC_dry_air
    TC_dry_air = surface_pressure_mean.divide(g * m_dry_air)

    # Calculate XSO2
    XSO2 = SO2_mean.divide(TC_dry_air).rename("XSO2")

    # Convert XSO2 to ppb
    XSO2_ppb = XSO2.multiply(1e9).rename("XSO2_ppb")

    # Calculate the minimum and maximum SO2 values
    min_max_SO2 = XSO2_ppb.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=buffered_city_geometry,
        scale=1113.2,
        maxPixels=1e9,
    )

    # Get min and max values and round them to two decimal places
    SO2_min = round(min_max_SO2.get("XSO2_ppb_min").getInfo(), 3)
    SO2_max = round(min_max_SO2.get("XSO2_ppb_max").getInfo(), 3)

    # Print the minimum and maximum SO2 values
    print("Minimum SO2 value:", SO2_min)
    print("Maximum SO2 value:", SO2_max)

    # Define a color palette based on SO2 concentration levels
    palette_SO2 = [
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

    # Get a URL to a thumbnail image of the SO2 concentration data
    thumbnail_url_SO2 = XSO2_ppb.getThumbURL(
        {
            "min": SO2_min,
            "max": SO2_max,
            "region": buffered_city_geometry.bounds().getInfo()["coordinates"],
            "dimensions": 512,
            "palette": palette_SO2,
        }
    )

    # Download the image and convert it to a NumPy array
    response_SO2 = requests.get(thumbnail_url_SO2)
    img_SO2 = Image.open(BytesIO(response_SO2.content))
    img_array_SO2 = np.array(img_SO2)

    # Get the geographic extent
    coords = buffered_city_geometry.bounds().getInfo()["coordinates"][0]
    extent = [coords[0][0], coords[2][0], coords[0][1], coords[2][1]]

    # Filter the NOAA VIIRS image collection for the specified city and date range
    viirs_collection = (
        ee.ImageCollection("NOAA/VIIRS/001/VNP46A2")
        .filterBounds(buffered_city_geometry)
        .filterDate(start_date, end_date)
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

    # Create a custom colormap for SO2
    custom_cmap_SO2 = LinearSegmentedColormap.from_list("custom_cmap_SO2", palette_SO2)

    # Create a custom colormap for NTL
    custom_cmap_NTL = LinearSegmentedColormap.from_list("custom_cmap_NTL", palette_NTL)

    # Plot the images using Matplotlib with the custom colormaps
    fig, ax = plt.subplots()

    # Plot SO2 concentration image
    cax_SO2 = ax.imshow(
        img_array_SO2, extent=extent, origin="upper", cmap=custom_cmap_SO2
    )

    # Overlay NTL image with 40% opacity
    cax_NTL = ax.imshow(
        img_array_NTL, extent=extent, origin="upper", cmap=custom_cmap_NTL, alpha=1
    )

    # Set title and labels
    ax.set_title("SO2 Concentration and NTL around Hyderabad in 2019 (50km radius)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Define the number of ticks
    num_ticks = 5

    # Calculate the interval between ticks for SO2
    interval_SO2 = (SO2_max - SO2_min) / (num_ticks - 1)

    # Calculate the tick positions for SO2
    tick_positions_SO2 = [SO2_min + i * interval_SO2 for i in range(num_ticks)]

    # Create a dummy ScalarMappable to use with the colorbar for SO2
    norm_SO2 = plt.Normalize(vmin=SO2_min, vmax=SO2_max)
    sm_SO2 = plt.cm.ScalarMappable(cmap=custom_cmap_SO2, norm=norm_SO2)
    sm_SO2.set_array([])

    # Create the colorbar for SO2
    cbar_SO2 = plt.colorbar(sm_SO2, ax=ax, orientation="vertical")
    cbar_SO2.set_label("SO2 Concentration (ppb)")

    # Set ticker to manually specify tick positions for SO2
    tick_locator_SO2 = ticker.FixedLocator(tick_positions_SO2)
    cbar_SO2.locator = tick_locator_SO2
    cbar_SO2.update_ticks()

    # Set custom tick labels for SO2
    tick_labels_SO2 = ["{:.3f}".format(value) for value in tick_positions_SO2]
    cbar_SO2.ax.set_yticklabels(tick_labels_SO2, ha="left")

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
    plot_file_path = "plots/latest_plot.png"  # Static filename
    SO2_Map(city, startDate, endDate, plot_file_path)

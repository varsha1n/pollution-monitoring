import ee
import requests
from PIL import Image
import numpy as np
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from io import BytesIO
import sys
import os

# Authenticate and initialize Earth Engine
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

    lat, long = city_coords.get(
        city, (13.0827, 80.2707)
    )  # Default to Chennai if city not found

    # Define a buffer around the point to cover an area around the selected city (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_city_geometry = ee.Geometry.Point([long, lat]).buffer(buffer_radius)

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
        collection.select("CO_column_number_density")
        .mean()
        .clip(buffered_city_geometry)
    )
    H2O_mean = (
        collection.select("H2O_column_number_density")
        .mean()
        .clip(buffered_city_geometry)
    )
    surface_pressure_mean = surface_pressure_collection.mean().clip(
        buffered_city_geometry
    )

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

    # Get min and max values and round them to two decimal places
    CO_min = round(min_max.get("XCO_ppb_min").getInfo(), 3)
    CO_max = round(min_max.get("XCO_ppb_max").getInfo(), 3)

    # Print the minimum and maximum CO values
    print("Minimum CO value:", CO_min)
    print("Maximum CO value:", CO_max)

    # Define a color palette based on CO concentration levels
    palette_CO = [
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
    thumbnail_url_CO = XCO_ppb.getThumbURL(
        {
            "min": CO_min,
            "max": CO_max,
            "region": buffered_city_geometry.bounds().getInfo()["coordinates"],
            "dimensions": 512,
            "palette": palette_CO,
        }
    )

    # Download the image and convert it to a NumPy array
    response_CO = requests.get(thumbnail_url_CO)
    img_CO = Image.open(BytesIO(response_CO.content))
    img_array_CO = np.array(img_CO)

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

    # Create a custom colormap for CO
    custom_cmap_CO = LinearSegmentedColormap.from_list("custom_cmap_CO", palette_CO)

    # Create a custom colormap for NTL
    custom_cmap_NTL = LinearSegmentedColormap.from_list("custom_cmap_NTL", palette_NTL)

    # Plot the images using Matplotlib with the custom colormaps
    fig, ax = plt.subplots()

    # Plot CO concentration image
    cax_CO = ax.imshow(img_array_CO, extent=extent, origin="upper", cmap=custom_cmap_CO)

    # Overlay NTL image with 40% opacity
    cax_NTL = ax.imshow(
        img_array_NTL, extent=extent, origin="upper", cmap=custom_cmap_NTL, alpha=1
    )

    # Set title and labels
    ax.set_title("CO Concentration and NTL around Hyderabad in 2019 (50km radius)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Define the number of ticks
    num_ticks = 5

    # Calculate the interval between ticks for CO
    interval_CO = (CO_max - CO_min) / (num_ticks - 1)

    # Calculate the tick positions for CO
    tick_positions_CO = [CO_min + i * interval_CO for i in range(num_ticks)]

    # Create a dummy ScalarMappable to use with the colorbar for CO
    norm_CO = plt.Normalize(vmin=CO_min, vmax=CO_max)
    sm_CO = plt.cm.ScalarMappable(cmap=custom_cmap_CO, norm=norm_CO)
    sm_CO.set_array([])

    # Create the colorbar for CO
    cbar_CO = plt.colorbar(sm_CO, ax=ax, orientation="vertical")
    cbar_CO.set_label("CO Concentration (ppb)")

    # Set ticker to manually specify tick positions for CO
    tick_locator_CO = ticker.FixedLocator(tick_positions_CO)
    cbar_CO.locator = tick_locator_CO
    cbar_CO.update_ticks()

    # Set custom tick labels for CO
    tick_labels_CO = ["{:.3f}".format(value) for value in tick_positions_CO]
    cbar_CO.ax.set_yticklabels(tick_labels_CO, ha="left")

    plt.savefig(plot_file_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Plot saved successfully to {plot_file_path}.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python CO.py <city> <start_date> <end_date>")
        sys.exit(1)

    city = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    plot_file_path = "plots/latest_plot.png"  # Static filename
    CO_Map(city, start_date, end_date, plot_file_path)

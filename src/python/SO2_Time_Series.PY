import ee
import plotly.graph_objs as go
import calendar
import plotly.io as pio
import sys

# Authorize ee
ee.Authenticate()

# Initialize the Earth Engine API
ee.Initialize(project="ee-narravarsha1")


def SO2_Time_Series(city, date, plot_file_path):

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

    # Define a buffer around the point to cover an area around Mumbai (25 kilometers)
    buffer_radius = 25000  # 25 kilometers in meters
    buffered_mumbai_geometry = ee.Geometry.Point(long, lat).buffer(buffer_radius)

    # Constants
    g = 9.82  # m/s^2
    m_H2O = 0.01801528  # kg/mol
    m_dry_air = 0.0289644  # kg/mol

    # Function to calculate mean SO2 concentration for a given month
    def extract_month_data(month):
        start_date = ee.Date.fromYMD(2019, month, 1)
        end_date = ee.Date.fromYMD(2019, month, calendar.monthrange(2019, month)[1])

        # Filter the collections for the given month
        filtered_collection = (
            ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_SO2")
            .filterBounds(buffered_mumbai_geometry)
            .filterDate(start_date, end_date)
            .select("SO2_column_number_density")
        )

        watervapor_collection = (
            ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CO")
            .filterBounds(buffered_mumbai_geometry)
            .filterDate(start_date, end_date)
            .select("H2O_column_number_density")
        )

        surface_pressure_collection = (
            ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
            .filterBounds(buffered_mumbai_geometry)
            .filterDate(start_date, end_date)
            .select("surface_pressure")
        )

        # Check if the collections are empty
        if (
            filtered_collection.size().getInfo() == 0
            or surface_pressure_collection.size().getInfo() == 0
        ):
            return None

        # Calculate the mean over the collection for SO2, H2O, and surface pressure
        SO2_mean_month = (
            filtered_collection.select("SO2_column_number_density")
            .mean()
            .clip(buffered_mumbai_geometry)
        )
        H2O_mean_month = watervapor_collection.mean().clip(buffered_mumbai_geometry)
        surface_pressure_mean_month = surface_pressure_collection.mean().clip(
            buffered_mumbai_geometry
        )

        # Calculate TC_dry_air for the month
        TC_dry_air_month = surface_pressure_mean_month.divide(g * m_dry_air).subtract(
            H2O_mean_month.multiply(m_H2O / m_dry_air)
        )

        # Calculate XSO2 for the month
        XSO2_month = SO2_mean_month.divide(TC_dry_air_month).rename("XSO2")

        # Convert XSO2 to ppb
        XSO2_ppb_month = XSO2_month.multiply(1e9).rename("XSO2_ppb")

        # Calculate the mean SO2 concentration for the month
        mean_value = XSO2_ppb_month.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=buffered_mumbai_geometry, scale=1000
        ).get("XSO2_ppb")
        return mean_value

    # Extract SO2 concentration values for each month
    so2_values = []
    for month in range(1, 13):
        value = extract_month_data(month)
        if value is not None:
            value = round(value.getInfo(), 3)  # Round to 3 decimals
            print(f"Month: {month}, Value: {value}")  # Debug statement
        else:
            value = None
            print(f"Month: {month}, Value: None")  # Debug statement
        so2_values.append(value)

    # Define month names for x-axis labels
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    # Replace None values with None in the plot (for consistency)
    so2_values = [v if v is not None else None for v in so2_values]

    # Create a Plotly trace for the SO2 concentration data
    trace = go.Scatter(
        x=month_names,
        y=so2_values,
        mode="lines+markers+text",  # Include text mode to display y values
        name="SO2 Concentration",
        hoverinfo="x+y",
        text=so2_values,  # Display y values as text
        textposition="top center",  # Position of the text relative to the markers
        line=dict(color="royalblue", width=2, dash="dash"),
        marker=dict(color="darkorange", size=8, symbol="circle"),
    )

    # Create layout for the plot
    layout = go.Layout(
        title={
            "text": "Monthly Mean SO2 Concentration for Mumbai in 2019 (25km radius)",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(
            title="Month",
            tickmode="array",
            tickvals=month_names,
            ticktext=month_names,
            showgrid=True,
            gridcolor="lightgrey",
        ),
        yaxis=dict(
            title="Mean SO2 Concentration (ppb)", showgrid=True, gridcolor="lightgrey"
        ),
        plot_bgcolor="whitesmoke",
        hovermode="closest",
        showlegend=True,
        legend=dict(
            x=0.1,
            y=1.1,
            bgcolor="rgba(255, 255, 255, 0)",
            bordercolor="rgba(255, 255, 255, 0)",
        ),
    )

    # Create figure
    fig = go.Figure(data=[trace], layout=layout)

    # Show interactive plot
    fig.show()

    # Save the Plotly figure as a PNG file
    pio.write_image(fig, plot_file_path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python CO.py <city> <date>")
        sys.exit(1)

    city = sys.argv[1]
    date = sys.argv[2]
    plot_file_path = "plots/latest_plot.png"
    SO2_Time_Series(city, date, plot_file_path)

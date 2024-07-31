import ee
import plotly.graph_objs as go
import calendar
import plotly.io as pio
import sys

# Initialize the Earth Engine API
ee.Authenticate()
ee.Initialize(project="ee-narravarsha1")


def CO_Time_Series(city, start_date, end_date, plot_file_path):

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

    # Define a buffer around the point to cover an area around the city (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_city_geometry = ee.Geometry.Point(long, lat).buffer(buffer_radius)

    # Constants
    g = 9.82  # m/s^2
    m_H2O = 0.01801528  # kg/mol
    m_dry_air = 0.0289644  # kg/mol

    # Function to calculate mean CO concentration for a given month
    def extract_month_data(month):
        start_date = ee.Date.fromYMD(2019, month, 1)
        end_date = ee.Date.fromYMD(2019, month, calendar.monthrange(2019, month)[1])

        # Filter the collections for the given month
        filtered_collection = (
            ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CO")
            .filterBounds(buffered_city_geometry)
            .filterDate(start_date, end_date)
            .select(["CO_column_number_density", "H2O_column_number_density"])
        )

        surface_pressure_collection = (
            ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
            .filterBounds(buffered_city_geometry)
            .filterDate(start_date, end_date)
            .select("surface_pressure")
        )

        # Check if the collections are empty
        if (
            filtered_collection.size().getInfo() == 0
            or surface_pressure_collection.size().getInfo() == 0
        ):
            return None

        # Calculate the mean over the collection for CO, H2O, and surface pressure
        CO_mean_month = (
            filtered_collection.select("CO_column_number_density")
            .mean()
            .clip(buffered_city_geometry)
        )
        H2O_mean_month = (
            filtered_collection.select("H2O_column_number_density")
            .mean()
            .clip(buffered_city_geometry)
        )
        surface_pressure_mean_month = surface_pressure_collection.mean().clip(
            buffered_city_geometry
        )

        # Calculate TC_dry_air for the month
        TC_dry_air_month = surface_pressure_mean_month.divide(g * m_dry_air).subtract(
            H2O_mean_month.multiply(m_H2O / m_dry_air)
        )

        # Calculate XCO for the month
        XCO_month = CO_mean_month.divide(TC_dry_air_month).rename("XCO")

        # Convert XCO to ppb
        XCO_ppb_month = XCO_month.multiply(1e9).rename("XCO_ppb")

        # Calculate the mean CO concentration for the month
        mean_value = XCO_ppb_month.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=buffered_city_geometry, scale=1000
        ).get("XCO_ppb")
        return mean_value

    # Extract CO concentration values for each month
    co_values = []
    for month in range(1, 13):
        value = extract_month_data(month)
        if value is not None:
            value = round(value.getInfo(), 3)  # Round to 3 decimals
            print(f"Month: {month}, Value: {value}")  # Debug statement
        else:
            value = None
            print(f"Month: {month}, Value: None")  # Debug statement
        co_values.append(value)

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
    co_values = [v if v is not None else None for v in co_values]

    # Create a Plotly trace for the CO concentration data
    trace = go.Scatter(
        x=month_names,
        y=co_values,
        mode="lines+markers+text",  # Include text mode to display y values
        name="CO Concentration",
        hoverinfo="x+y",
        text=co_values,  # Display y values as text
        textposition="top center",  # Position of the text relative to the markers
        line=dict(color="royalblue", width=2, dash="dash"),
        marker=dict(color="darkorange", size=8, symbol="circle"),
    )

    # Create layout for the plot
    layout = go.Layout(
        title={
            "text": f"Monthly Mean CO Concentration for {city} in 2019 (50km radius)",
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
            title="Mean CO Concentration (ppb)",
            showgrid=True,
            gridcolor="lightgrey",
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

    # Save plot to the file
    pio.write_image(fig, plot_file_path, width=1500, height=1000)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python CO.py <city> <start_date> <end_date>")
        sys.exit(1)

    city = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    plot_file_path = "plots/latest_plot.png"  # Static filename
    CO_Time_Series(city, start_date, end_date, plot_file_path)

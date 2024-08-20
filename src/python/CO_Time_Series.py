import ee
import plotly.graph_objs as go
import calendar
import plotly.io as pio
from datetime import datetime, timedelta
import sys
import os

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

    # Parse the start_date string into a datetime object
    start_date_year = datetime.strptime(start_date, "%Y-%m-%d")

    # Extract the year from the datetime object
    year = start_date_year.year

    # Define a buffer around the point to cover an area around the city (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_city_geometry = ee.Geometry.Point(long, lat).buffer(buffer_radius)

    # Calculate the duration between start_date and end_date
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
    duration = end_date_dt - start_date_dt

    # Determine if the duration is approximately 3 months
    seasonal = (
        abs(duration.days - 90) <= 5
    )  # Approximate 3 months with a tolerance of 5 days

    def get_data(start_date, end_date):
        collection = (
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

        if (
            collection.size().getInfo() == 0
            or surface_pressure_collection.size().getInfo() == 0
        ):
            return None

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

        g = 9.82  # m/s^2
        m_H2O = 0.01801528  # kg/mol
        m_dry_air = 0.0289644  # kg/mol

        TC_dry_air = surface_pressure_mean.divide(g * m_dry_air).subtract(
            H2O_mean.multiply(m_H2O / m_dry_air)
        )
        XCO = CO_mean.divide(TC_dry_air).rename("XCO")
        XCO_ppb = XCO.multiply(1e9).rename("XCO_ppb")

        mean_value = XCO_ppb.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=buffered_city_geometry, scale=1113.2
        ).get("XCO_ppb")

        return mean_value

    if seasonal:
        # Generate 15-day intervals within the specified season
        date_ranges = []
        while start_date_dt <= end_date_dt:
            end_interval_date = start_date_dt + timedelta(days=14)
            if end_interval_date > end_date_dt:
                end_interval_date = end_date_dt
            date_ranges.append(
                (
                    start_date_dt.strftime("%Y-%m-%d"),
                    end_interval_date.strftime("%Y-%m-%d"),
                )
            )
            start_date_dt = end_interval_date + timedelta(days=1)

        # Get CO concentration values for each 15-day interval
        co_values = []
        for start, end in date_ranges:
            value = get_data(start, end)
            if value is not None:
                value = round(value.getInfo(), 3)
                print(f"Period: {start} to {end}, Value: {value}")  # Debug statement
            else:
                value = None
                print(f"Period: {start} to {end}, Value: None")  # Debug statement
            co_values.append(value)

        # Define custom period names for x-axis labels
        period_names = [f"{start} - {end}" for start, end in date_ranges]

    else:
        # Define the start and end dates for each month of the year
        start_dates = [f"{year}-{month:02d}-01" for month in range(1, 13)]
        end_dates = [
            f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
            for month in range(1, 13)
        ]

        # Initialize list to store CO values
        co_values = []

        # Process each month
        for start_date, end_date in zip(start_dates, end_dates):
            value = get_data(start_date, end_date)
            if value is not None:
                value = round(value.getInfo(), 3)
                print(f"Month: {start_date[:7]}, Value: {value}")  # Debug statement
            else:
                value = None
                print(f"Month: {start_date[:7]}, Value: None")  # Debug statement
            co_values.append(value)

        # Define month names for x-axis labels
        period_names = [
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
        x=period_names,
        y=co_values,
        mode="lines+markers+text",  # Include text mode to display y values
        name="CO Concentration",
        hoverinfo="x+y",
        text=[
            f"{v:.3f}" if v is not None else None for v in co_values
        ],  # Format y values to 3 decimal places
        textposition="top center",  # Position of the text relative to the markers
        line=dict(color="royalblue", width=2, dash="dash"),
        marker=dict(color="darkorange", size=8, symbol="circle"),
    )

    # Create layout for the plot
    layout = go.Layout(
        title={
            "text": f'{"Seasonal" if seasonal else "Yearly"} Mean CO Concentration for {city} from {start_date} to {end_date}',
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(
            title="Period",
            tickmode="array",
            tickvals=period_names,
            ticktext=period_names,
            showgrid=True,
            gridcolor="lightgrey",
        ),
        yaxis=dict(
            title="Mean CO Concentration (ppb)", showgrid=True, gridcolor="lightgrey"
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

    # Ensure plots directory exists
    os.makedirs(os.path.dirname(plot_file_path), exist_ok=True)

    # Save plot to the file
    fig.write_html(plot_file_path)
    fig.show()
    print(f"Plot saved to {plot_file_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python CO.py <city> <start_date> <end_date>")
        sys.exit(1)

    city = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    plot_file_path = "plots/latest_Timeseries.html"  # Static filename
    CO_Time_Series(city, start_date, end_date, plot_file_path)

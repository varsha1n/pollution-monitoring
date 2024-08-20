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


def SO2_Time_Series(city, start_date, end_date, plot_file_path):

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

    # Parse the start_date and end_date strings into datetime objects
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
    duration = end_date_dt - start_date_dt

    # Determine if the duration is approximately 3 months
    seasonal = (
        abs(duration.days - 90) <= 5
    )  # Approximate 3 months with a tolerance of 5 days

    # Define a buffer around the point to cover an area around the city (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_city_geometry = ee.Geometry.Point(long, lat).buffer(buffer_radius)

    def extract_month_data(month):
        start_date = ee.Date.fromYMD(start_date_dt.year, month, 1)
        end_date = ee.Date.fromYMD(
            start_date_dt.year, month, calendar.monthrange(start_date_dt.year, month)[1]
        )

        # Filter the collections for the given month
        filtered_collection = (
            ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_HCHO")
            .filterBounds(buffered_city_geometry)
            .filterDate(start_date, end_date)
            .select(["tropospheric_HCHO_column_number_density"])
        )

        if filtered_collection.size().getInfo() == 0:
            return None

        HCHO_mean_month = filtered_collection.mean().clip(buffered_city_geometry)
        HCHO_ppb_month = HCHO_mean_month.multiply(1e9).rename("HCHO_ppb")

        mean_value = HCHO_ppb_month.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=buffered_city_geometry, scale=1000
        ).get("HCHO_ppb")
        return mean_value

    def get_monthly_data():
        hcho_values = []
        for month in range(1, 13):
            value = extract_month_data(month)
            if value is not None:
                value = round(value.getInfo(), 3)
            else:
                value = None
            hcho_values.append(value)
        return hcho_values, [
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

    def get_seasonal_data():
        date_ranges = []
        temp_start_date_dt = start_date_dt  # Use a temporary variable for iteration
        while temp_start_date_dt <= end_date_dt:
            end_interval_date = temp_start_date_dt + timedelta(days=14)
            if end_interval_date > end_date_dt:
                end_interval_date = end_date_dt
            date_ranges.append(
                (
                    temp_start_date_dt.strftime("%Y-%m-%d"),
                    end_interval_date.strftime("%Y-%m-%d"),
                )
            )
            temp_start_date_dt = end_interval_date + timedelta(days=1)

        hcho_values = []
        for start, end in date_ranges:
            # Extract month from the start date to get HCHO data
            month = datetime.strptime(start, "%Y-%m-%d").month
            value = extract_month_data(month)
            if value is not None:
                value = round(value.getInfo(), 3)
            else:
                value = None
            hcho_values.append(value)
        return hcho_values, [f"{start} - {end}" for start, end in date_ranges]

    # Get data based on whether it's seasonal or yearly
    if seasonal:
        hcho_values, period_names = get_seasonal_data()
    else:
        hcho_values, period_names = get_monthly_data()

    hcho_values = [v if v is not None else None for v in hcho_values]

    # Create a Plotly trace for the HCHO concentration data
    trace = go.Scatter(
        x=period_names,
        y=hcho_values,
        mode="lines+markers+text",  # Include text mode to display y values
        name="HCHO Concentration",
        hoverinfo="x+y",
        text=[f"{v:.3f}" if v is not None else None for v in hcho_values],
        textposition="top center",
        line=dict(color="royalblue", width=2, dash="dash"),
        marker=dict(color="darkorange", size=8, symbol="circle"),
    )

    # Create layout for the plot
    layout = go.Layout(
        title={
            "text": f'{"Seasonal" if seasonal else "Monthly"} Mean SO2 Concentration for {city} from {start_date} to {end_date}',
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

    # Ensure plots directory exists
    os.makedirs(os.path.dirname(plot_file_path), exist_ok=True)

    # Save plot to the file
    fig.write_html(plot_file_path)
    print(f"Plot saved to {plot_file_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <city> <start_date> <end_date>")
        sys.exit(1)

    city = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    plot_file_path = "plots/latest_Timeseries.html"  # Static filename
    SO2_Time_Series(city, start_date, end_date, plot_file_path)

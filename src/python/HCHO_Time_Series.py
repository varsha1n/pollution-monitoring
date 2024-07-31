import ee
import plotly.graph_objs as go
import calendar
import plotly.io as pio
import sys

# Initialize the Earth Engine API
ee.Authenticate()
ee.Initialize(project="ee-narravarsha1")


def HCHO_Time_Series(city, start_date, end_date, plot_file_path):

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

    # Define a buffer around the point to cover an area around Hyderabad (50 kilometers)
    buffer_radius = 50000  # 50 kilometers in meters
    buffered_hyderabad_geometry = ee.Geometry.Point(long, lat).buffer(buffer_radius)

    # Function to calculate mean HCHO concentration for a given month
    def extract_month_data(month):
        start_date = ee.Date.fromYMD(2019, month, 1)
        end_date = ee.Date.fromYMD(2019, month, calendar.monthrange(2019, month)[1])

        # Filter the collections for the given month
        filtered_collection = (
            ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_HCHO")
            .filterBounds(buffered_hyderabad_geometry)
            .filterDate(start_date, end_date)
            .select(["tropospheric_HCHO_column_number_density"])
        )

        # Check if the collections are empty
        if filtered_collection.size().getInfo() == 0:
            return None

        # Calculate the mean over the collection for HCHO
        HCHO_mean_month = filtered_collection.mean().clip(buffered_hyderabad_geometry)

        # Convert HCHO to ppb
        HCHO_ppb_month = HCHO_mean_month.multiply(1e9).rename("HCHO_ppb")

        # Calculate the mean HCHO concentration for the month
        mean_value = HCHO_ppb_month.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=buffered_hyderabad_geometry, scale=1000
        ).get("HCHO_ppb")
        return mean_value

    # Extract HCHO concentration values for each month
    hcho_values = []
    for month in range(1, 13):
        value = extract_month_data(month)
        if value is not None:
            value = round(value.getInfo(), 3)  # Round to 3 decimals
            print(f"Month: {month}, Value: {value}")  # Debug statement
        else:
            value = None
            print(f"Month: {month}, Value: None")  # Debug statement
        hcho_values.append(value)

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
    hcho_values = [v if v is not None else None for v in hcho_values]

    # Create a Plotly trace for the HCHO concentration data
    trace = go.Scatter(
        x=month_names,
        y=hcho_values,
        mode="lines+markers+text",  # Include text mode to display y values
        name="HCHO Concentration",
        hoverinfo="x+y",
        text=hcho_values,  # Display y values as text
        textposition="top center",  # Position of the text relative to the markers
        line=dict(color="royalblue", width=2, dash="dash"),
        marker=dict(color="darkorange", size=8, symbol="circle"),
    )

    # Create layout for the plot
    layout = go.Layout(
        title={
            "text": "Monthly Mean HCHO Concentration for Bangalore in 2019 (50km radius)",
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
            title="Mean HCHO Concentration (ppb)", showgrid=True, gridcolor="lightgrey"
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
        print("Usage: python HCHO_Time_series.py <city> <start_date> <end_date>")
        sys.exit(1)

    city = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    plot_file_path = "plots/latest_plot.png"  # Static filename
    HCHO_Time_Series(city, start_date, end_date, plot_file_path)

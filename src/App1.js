import React, { useState, useEffect } from "react";

import "./App.css";
import logo1 from "./logo1.png"; // Replace with your logo path
import logo2 from "./logo2.png"; // Replace with your logo path
import logo3 from "./logo3.png"; // Replace with your logo path
import logo4 from "./logo4.png"; // Replace with your logo path
import MapEmbed from "./MapEmbed";

const App = () => {
  const [city, setCity] = useState("");
  const [pollutant, setPollutant] = useState("");
  const [year, setYear] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [duration, setDuration] = useState("");
  const [timeframe, setTimeframe] = useState("");
  const [mapImageSrc, setMapImageSrc] = useState("");

  // Separate loading states
  const [loadingPollution, setLoadingPollution] = useState(false);
  const [loadingNTL, setLoadingNTL] = useState(false);
  const [loadingTimeSeries, setLoadingTimeSeries] = useState(false);

  const [errorMessage, setErrorMessage] = useState("");

  // NTL-specific states
  const [ntlCity, setNtlCity] = useState("");
  const [ntlYear, setNtlYear] = useState("");
  const [halfYear, setHalfYear] = useState("");
  const [ntlImageSrc, setNtlImageSrc] = useState("");

  // Separate Time Series form states
  const [timeSeriesCity, setTimeSeriesCity] = useState("");
  const [timeSeriesPollutant, setTimeSeriesPollutant] = useState("");
  const [timeSeriesYear, setTimeSeriesYear] = useState("");
  const [timeSeriesSeason, setTimeSeriesSeason] = useState("");
  const [timeSeriesImageSrc, setTimeSeriesImageSrc] = useState("");

  // Handlers for Pollution Data form
  const handleCityChange = (e) => setCity(e.target.value);
  const handlePollutantChange = (e) => setPollutant(e.target.value);
  const handleYearChange = (e) => setYear(e.target.value);
  const handleStartDateChange = (e) => setStartDate(e.target.value);
  const handleEndDateChange = (e) => setEndDate(e.target.value);
  const handleDurationChange = (e) => {
    setDuration(e.target.value);
    setTimeframe(""); // Reset timeframe when duration changes
  };
  const handleTimeframeChange = (e) => setTimeframe(e.target.value);

  // Handlers for NTL Data form
  const handleNtlCityChange = (e) => setNtlCity(e.target.value);
  const handleNtlYearChange = (e) => setNtlYear(e.target.value);
  const handleHalfYearChange = (e) => setHalfYear(e.target.value);

  // Handlers for Separate Time Series form
  const handleTimeSeriesCityChange = (e) => setTimeSeriesCity(e.target.value);
  const handleTimeSeriesPollutantChange = (e) =>
    setTimeSeriesPollutant(e.target.value);
  const handleTimeSeriesYearChange = (e) => setTimeSeriesYear(e.target.value);
  const handleTimeSeriesSeasonChange = (e) =>
    setTimeSeriesSeason(e.target.value);
  const [timeSeriesHtmlContent, setTimeSeriesHtmlContent] = useState("");
  const [MapHtmlContent, setMapHtmlContent] = useState("");

  const [weeklyOptions, setWeeklyOptions] = useState([]);
  const [isWindowsEnabled, setIsWindowsEnabled] = useState(false);

  useEffect(() => {
    generateWeeklyOptions();
  }, []);

  const generateWeeklyOptions = () => {
    const startDate = new Date("2018-05-01");
    const endDate = new Date();
    const weeks = [];

    let current = startDate;

    while (current <= endDate) {
      const nextWeek = new Date(current);
      nextWeek.setDate(nextWeek.getDate() + 6); // Adding 6 days to get a full week

      // Ensure the last week doesn't extend beyond today
      const formattedStartDate = current.toISOString().split("T")[0];
      const formattedEndDate = nextWeek.toISOString().split("T")[0];
      weeks.push({ start: formattedStartDate, end: formattedEndDate });

      // Move to the next week
      current.setDate(current.getDate() + 7);
    }

    setWeeklyOptions(weeks);
  };

  const isValidDateRange = (start, end) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const minDate = new Date("2018-04-30");
    const maxDate = new Date("2025-06-05");

    return startDate >= minDate && endDate <= maxDate;
  };

  const formatDate = (date) => {
    const [day, month, year] = date.split("-");
    return `${year}-${month}-${day}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoadingPollution(true);
    setErrorMessage("");

    let formattedStartDate = startDate;
    let formattedEndDate = endDate;

    const adjustEndDate = (startDate, endDate) => {
      const start = new Date(startDate);
      let end = new Date(endDate);

      if (
        end.getDate() >
        new Date(end.getFullYear(), end.getMonth() + 1, 0).getDate()
      ) {
        end = new Date(end.getFullYear(), end.getMonth() + 1, 0);
      }

      return {
        formattedStartDate: start.toISOString().split("T")[0],
        formattedEndDate: end.toISOString().split("T")[0],
      };
    };

    if (duration === "Date" && !isValidDateRange(startDate, endDate)) {
      setErrorMessage("Data is not available for the selected date range.");
      setLoadingPollution(false);
      return;
    } else if (duration === "Season") {
      const seasonMap = {
        "march-may": ["03-01", "05-31"],
        "june-august": ["06-01", "08-31"],
        "september-november": ["09-01", "11-30"],
        "december-february": ["12-01", "02-28"],
      };
      [formattedStartDate, formattedEndDate] = seasonMap[timeframe];
      formattedStartDate = `${year}-${formattedStartDate}`;
      formattedEndDate = `${year}-${formattedEndDate}`;
    } else if (duration === "Month") {
      if (!timeframe) {
        setErrorMessage("Please select a month.");
        setLoadingPollution(false);
        return;
      }

      const monthEndDates = {
        "01": "31", // January
        "02": "28", // February (non-leap year)
        "03": "31", // March
        "04": "30", // April
        "05": "31", // May
        "06": "30", // June
        "07": "31", // July
        "08": "31", // August
        "09": "30", // September
        10: "31", // October
        11: "30", // November
        12: "31", // December
      };

      formattedStartDate = `${year}-${timeframe}-01`;
      formattedEndDate = `${year}-${timeframe}-${monthEndDates[timeframe]}`;
    } else if (duration === "Week") {
      if (!timeframe) {
        setErrorMessage("Please select a week.");
        setLoadingPollution(false);
        return;
      }
      const [start, end] = timeframe.split("_");
      formattedStartDate = start;
      formattedEndDate = end;
    } else if (duration === "Year") {
      if (!year) {
        setErrorMessage("Please select a year.");
        setLoadingPollution(false);
        return;
      }
      formattedStartDate = `${year}-01-01`;
      formattedEndDate = `${year}-12-31`;
    }

    try {
      const response = await fetch("http://localhost:3001/pollution-data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          city,
          pollutant,
          startDate: formattedStartDate,
          endDate: formattedEndDate,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const blob = await response.blob(); // Get the response as a blob (binary large object)
      const imageUrl = URL.createObjectURL(blob); // Create a URL for the image blob

      setMapImageSrc(imageUrl); // This will hold the image URL
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoadingPollution(false);
    }
  };

  const handleNtlSubmit = async (e) => {
    e.preventDefault();
    setLoadingNTL(true);

    try {
      const response = await fetch("http://localhost:3001/ntl-data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ntlCity,
          ntlYear,
          halfYear,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      setNtlImageSrc(`data:image/png;base64,${data.ntlPlot}`);
    } catch (error) {
      console.error("Error fetching NTL data:", error);
    } finally {
      setLoadingNTL(false);
    }
  };
  const handleTimeSeriesSubmit = async (e) => {
    e.preventDefault();
    setLoadingTimeSeries(true);

    let formattedStartDate = startDate;
    let formattedEndDate = endDate;

    const seasonMap = {
      "march-may": ["03-01", "05-31"],
      "june-august": ["06-01", "08-31"],
      "september-november": ["09-01", "11-30"],
      "december-february": ["12-01", "02-28"],
    };

    [formattedStartDate, formattedEndDate] = seasonMap[timeSeriesSeason];
    formattedStartDate = `${timeSeriesYear}-${formattedStartDate}`;
    formattedEndDate = `${timeSeriesYear}-${formattedEndDate}`;

    try {
      const response = await fetch("http://localhost:3001/time-series-data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          timeSeriesCity,
          timeSeriesPollutant,
          timeSeriesStartDate: formattedStartDate,
          timeSeriesEndDate: formattedEndDate,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const htmlContent = await response.text(); // Fetch the HTML content as text
      setTimeSeriesHtmlContent(htmlContent); // Set the HTML content to state
    } catch (error) {
      console.error("Error fetching time series data:", error);
      console.error("Request Body:", {
        timeSeriesCity,
        timeSeriesPollutant,
        timeSeriesStartDate: formattedStartDate,
        timeSeriesEndDate: formattedEndDate,
      });
    } finally {
      setLoadingTimeSeries(false);
    }
  };

  const renderAdditionalOptions = (type) => {
    switch (type) {
      case "city":
        return (
          <>
            <option value="Mumbai">Mumbai</option>
            <option value="Delhi">Delhi</option>
            <option value="Chennai">Chennai</option>
            <option value="Kolkata">Kolkata</option>
            <option value="Bangalore">Bangalore</option>
            <option value="Pune">Pune</option>
            <option value="Ahmedabad">Ahmedabad</option>
            <option value="Surat">Surat</option>
            <option value="Agra">Agra</option>
            <option value="Chandigarh">Chandigarh</option>
            <option value="Asansol">Asansol</option>
            <option value="Moradabad">Moradabad</option>
            <option value="Muzaffarpur">Muzaffarpur</option>
            <option value="Patna">Patna</option>
            <option value="Agartala">Agartala</option>
            <option value="Bhopal">Bhopal</option>
            <option value="Rourkela">Rourkela</option>
            <option value="Jodhpur">Jodhpur</option>
            <option value="Indore">Indore</option>
            <option value="Hyderabad">Hyderabad</option>
          </>
        );
      case "month":
        return (
          <>
            <option value="01">January</option>
            <option value="02">February</option>
            <option value="03">March</option>
            <option value="04">April</option>
            <option value="05">May</option>
            <option value="06">June</option>
            <option value="07">July</option>
            <option value="08">August</option>
            <option value="09">September</option>
            <option value="10">October</option>
            <option value="11">November</option>
            <option value="12">December</option>
          </>
        );
      case "season":
        return (
          <>
            <option value="march-may">March-May</option>
            <option value="june-august">June-August</option>
            <option value="september-november">September-November</option>
            <option value="december-february">December-February</option>
          </>
        );
      case "year":
        return (
          <>
            <option value="2018">2018</option>
            <option value="2019">2019</option>
            <option value="2020">2020</option>
            <option value="2021">2021</option>
            <option value="2022">2022</option>
            <option value="2023">2023</option>
            <option value="2024">2024</option>
            <option value="2025">2025</option>
          </>
        );
      case "week":
        return (
          <>
            {weeklyOptions.map((week, index) => (
              <option
                key={index}
                value={`${week.start}_${week.end}`}
              >{`${week.start} to ${week.end}`}</option>
            ))}
          </>
        );
      default:
        return null;
    }
  };
  const handleWindowsToggle = () => {
    setIsWindowsEnabled((prev) => !prev);
  };

  return (
    <div className="body">
      <nav>
        <img className="logo1" src={logo1} alt="Logo 1" />
        <img className="logo2" src={logo2} alt="Logo 2" />
        <img className="logo3" src={logo3} alt="Logo 3" />
        <img className="logo4" src={logo4} alt="Logo 4" />
      </nav>
      <div className="static">
        <MapEmbed />
        <div className="scrollable-content">
          <p className="dummy-text">
            {/* Your scrollable dummy text goes here */}
            The map has been generated using the integration of Google Earth
            engine along with different python libraries, with sentinel 5p offl
            datasets provided by the Google Earth engine data providers.
            {/* Add more dummy text as needed */}
          </p>
        </div>
      </div>

      <div className="content">
        <div className="form-container">
          <h1 className="heading">Select Pollution Data</h1>
          <form onSubmit={handleSubmit}>
            <label htmlFor="city">City:</label>
            <select id="city" value={city} onChange={handleCityChange}>
              <option value="">Select a city</option>
              {renderAdditionalOptions("city")}
            </select>

            <label htmlFor="pollutant">Pollutant:</label>
            <select
              id="pollutant"
              value={pollutant}
              onChange={handlePollutantChange}
            >
              <option value="">Select a pollutant</option>
              <option value="CO">CO</option>
              <option value="HCHO">HCHO</option>
              <option value="NO2">NO2</option>
              <option value="SO2">SO2</option>
            </select>

            <label htmlFor="year">Year:</label>
            <select id="year" value={year} onChange={handleYearChange}>
              <option value="">Select a year</option>
              {renderAdditionalOptions("year")}
            </select>

            <label htmlFor="duration">Duration:</label>
            <select
              id="duration"
              value={duration}
              onChange={handleDurationChange}
            >
              <option value="">Select a duration</option>
              <option value="Month">Monthly</option>
              <option value="Season">Season</option>
              <option value="Date">Daily</option>
              <option value="Week">Weekly</option>
              <option value="Year">Yearly</option>
            </select>

            {duration === "Date" && (
              <>
                <label htmlFor="startDate">Start Date:</label>
                <input
                  type="date"
                  id="startDate"
                  value={startDate}
                  onChange={handleStartDateChange}
                />

                <label htmlFor="endDate">End Date:</label>
                <input
                  type="date"
                  id="endDate"
                  value={endDate}
                  onChange={handleEndDateChange}
                />
              </>
            )}

            {duration !== "Date" && duration !== "Year" && (
              <>
                <label htmlFor="timeframe">Select {duration}:</label>
                <select
                  id="timeframe"
                  value={timeframe}
                  onChange={handleTimeframeChange}
                >
                  <option value="">Select an option</option>
                  {renderAdditionalOptions(duration.toLowerCase())}
                </select>
              </>
            )}

            <div className="switch-container">
              <label htmlFor="windows-toggle">Winds:</label>
              <label className="switch">
                <input
                  type="checkbox"
                  id="windows-toggle"
                  checked={isWindowsEnabled}
                  onChange={handleWindowsToggle}
                />
                <span className="slider round"></span>
              </label>
            </div>

            <button type="submit" disabled={loadingPollution}>
              {loadingPollution ? "Loading..." : "Submit"}
            </button>
          </form>

          {errorMessage && <p className="error">{errorMessage}</p>}
        </div>

        <div className="plot-container">
          {loadingPollution && <p>Loading...</p>}
          {!loadingPollution && mapImageSrc && (
            <div className="image-section">
              <div className="image-container">
                <img src={mapImageSrc} alt="Pollution Map" className="image" />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="content">
        <div className="form-container">
          <h1 className="heading">Select NTL Data</h1>
          <form onSubmit={handleNtlSubmit}>
            <label htmlFor="ntlCity">City:</label>
            <select id="ntlCity" value={ntlCity} onChange={handleNtlCityChange}>
              <option value="">Select a city</option>
              {renderAdditionalOptions("city")}
            </select>

            <label htmlFor="ntlYear">Year:</label>
            <select id="ntlYear" value={ntlYear} onChange={handleNtlYearChange}>
              <option value="">Select a year</option>
              {renderAdditionalOptions("year")}
            </select>

            <label htmlFor="halfYear">Half Year:</label>
            <select
              id="halfYear"
              value={halfYear}
              onChange={handleHalfYearChange}
            >
              <option value="">Select half year</option>
              <option value="jan-jun">Jan-Jun</option>
              <option value="jul-dec">Jul-Dec</option>
            </select>

            <button type="submit" disabled={loadingNTL}>
              {loadingNTL ? "Loading..." : "Submit"}
            </button>
          </form>
        </div>

        <div className="plot-container">
          {ntlImageSrc && (
            <div className="image-section">
              <div className="image-container">
                <img src={ntlImageSrc} alt="NTL Plot" className="image" />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="content">
        <div className="form-container">
          <h1 className="heading">Time Series Data</h1>
          <form onSubmit={handleTimeSeriesSubmit}>
            <label htmlFor="timeSeriesCity">City:</label>
            <select
              id="timeSeriesCity"
              value={timeSeriesCity}
              onChange={handleTimeSeriesCityChange}
            >
              <option value="">Select a city</option>
              {renderAdditionalOptions("city")}
            </select>

            <label htmlFor="timeSeriesPollutant">Pollutant:</label>
            <select
              id="timeSeriesPollutant"
              value={timeSeriesPollutant}
              onChange={handleTimeSeriesPollutantChange}
            >
              <option value="">Select a pollutant</option>
              <option value="CO">CO</option>
              <option value="HCHO">HCHO</option>
              <option value="NO2">NO2</option>
              <option value="SO2">SO2</option>
            </select>

            <label htmlFor="timeSeriesYear">Year:</label>
            <select
              id="timeSeriesYear"
              value={timeSeriesYear}
              onChange={handleTimeSeriesYearChange}
            >
              <option value="">Select a year</option>
              {renderAdditionalOptions("year")}
            </select>

            <label htmlFor="timeSeriesSeason">Season:</label>
            <select
              id="timeSeriesSeason"
              value={timeSeriesSeason}
              onChange={handleTimeSeriesSeasonChange}
            >
              <option value="">Select a season</option>
              {renderAdditionalOptions("season")}
            </select>

            <button type="submit" enabled={loadingTimeSeries}>
              {loadingTimeSeries ? "Loading..." : "Submit"}
            </button>
          </form>
        </div>
        <div className="plot-container">
          {loadingTimeSeries && <p>Loading...</p>}
          {timeSeriesHtmlContent ? (
            <div className="html-section">
              <iframe
                srcDoc={timeSeriesHtmlContent}
                title="Time Series Plot"
                style={{ width: "100%", height: "600px", border: "none" }}
              />
            </div>
          ) : (
            <p>No HTML content available</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;

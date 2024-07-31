import React, { useState } from "react";
import "./App.css";
import logo1 from "./logo1.png"; // Replace with your logo path
import logo2 from "./logo2.png"; // Replace with your logo path
import logo3 from "./logo3.png"; // Replace with your logo path
import logo4 from "./logo4.png"; // Replace with your logo path

const App = () => {
  const [city, setCity] = useState("");
  const [pollutant, setPollutant] = useState("");
  const [startDate, setStartDate] = useState(""); // State for start date
  const [endDate, setEndDate] = useState(""); // State for end date
  const [plotType, setPlotType] = useState(""); // State for plot type
  const [duration, setDuration] = useState(""); // State for duration
  const [timeframe, setTimeframe] = useState(""); // State for additional timeframe options
  const [imageSrc, setImageSrc] = useState(""); // State to hold image URL
  const [loading, setLoading] = useState(false); // State to manage loading
  const [errorMessage, setErrorMessage] = useState(""); // State for error message

  const handleCityChange = (e) => setCity(e.target.value);
  const handlePollutantChange = (e) => setPollutant(e.target.value);
  const handleStartDateChange = (e) => setStartDate(e.target.value);
  const handleEndDateChange = (e) => setEndDate(e.target.value);
  const handlePlotTypeChange = (e) => setPlotType(e.target.value);
  const handleDurationChange = (e) => {
    setDuration(e.target.value);
    setTimeframe(""); // Reset timeframe when duration changes
  };
  const handleTimeframeChange = (e) => setTimeframe(e.target.value);

  const isValidDateRange = (start, end) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const minDate = new Date("2018-04-30");
    const maxDate = new Date("2025-06-05");

    return startDate >= minDate && endDate <= maxDate;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage("");

    if (duration === "Date" && !isValidDateRange(startDate, endDate)) {
      setErrorMessage("Data is not available for the selected date range.");
      setLoading(false);
      return;
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
          startDate,
          endDate,
          plotType,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);
      setImageSrc(imageUrl);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const renderAdditionalOptions = () => {
    switch (duration) {
      case "Year":
        return (
          <>
            <option value="2018">2018</option>
            <option value="2019">2019</option>
            <option value="2020">2020</option>
            <option value="2021">2021</option>
          </>
        );
      case "Season":
        return (
          <>
            <option value="march-may">March to May</option>
            <option value="june-august">June to August</option>
            <option value="september-november">September to November</option>
            <option value="december-february">December to February</option>
          </>
        );
      case "Month":
        return (
          <>
            <option value="January">January</option>
            <option value="February">February</option>
            <option value="March">March</option>
            <option value="April">April</option>
            <option value="May">May</option>
            <option value="June">June</option>
            <option value="July">July</option>
            <option value="August">August</option>
            <option value="September">September</option>
            <option value="October">October</option>
            <option value="November">November</option>
            <option value="December">December</option>
          </>
        );
      default:
        return <option value="">Select Duration First</option>;
    }
  };

  return (
    <div className="body">
      <nav>
        <img className="logo1" src={logo1} alt="Logo 1" />
        <img className="logo2" src={logo2} alt="Logo 2" />
        <img className="logo3" src={logo3} alt="Logo 3" />
        <img className="logo4" src={logo4} alt="Logo 4" />
      </nav>
      <div className="container">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>
              <select value={plotType} onChange={handlePlotTypeChange} required>
                <option value="">PLOT TYPE</option>
                <option value="Map">Map</option>
                <option value="Time_Series">Time Series</option>
              </select>
            </label>
            <label>
              <select value={city} onChange={handleCityChange} required>
                <option value="">CITY</option>
                <option value="Hyderabad">Hyderabad</option>
                <option value="Mumbai">Mumbai</option>
                <option value="Chennai">Chennai</option>
                <option value="Banglore">Banglore</option>
                <option value="Kolkata">Kolkata</option>
                <option value="Indore">Indore</option>
                <option value="Jodhpur">Jodhpur</option>
                <option value="Rourkela">Rourkela</option>
                <option value="Bhopal">Bhopal</option>
                <option value="Agartala">Agartala</option>
                <option value="Patna">Patna</option>
                <option value="Muzaffarpur">Muzaffarpur</option>
                <option value="Moradabad">Moradabad</option>
                <option value="Asansol">Asansol</option>
                <option value="Chandigarh">Chandigarh</option>
                <option value="Surat">Surat</option>
                <option value="Ahmedabad">Ahmedabad</option>
                <option value="Delhi">Delhi</option>
                <option value="Agra">Agra</option>
              </select>
            </label>
            <label>
              <select
                value={pollutant}
                onChange={handlePollutantChange}
                required
              >
                <option value="">POLLUTANT</option>
                <option value="CO">CO</option>
                <option value="HCHO">HCHO</option>
                <option value="NO2">NO2</option>
                <option value="SO2">SO2</option>
              </select>
            </label>
            <label>
              <select value={duration} onChange={handleDurationChange} required>
                <option value="">DURATION</option>
                <option value="Year">Yearly</option>
                <option value="Season">Seasonal</option>
                <option value="Month">Monthly</option>
                <option value="Date">Daily</option>
              </select>
            </label>
            {duration !== "Date" && (
              <label>
                <select
                  value={timeframe}
                  onChange={handleTimeframeChange}
                  required
                >
                  <option value="">Select {duration}</option>
                  {renderAdditionalOptions()}
                </select>
              </label>
            )}
            {duration === "Date" && (
              <>
                <label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={handleStartDateChange}
                    className="date"
                    required
                  />
                </label>
                <label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={handleEndDateChange}
                    className="date"
                    required
                  />
                </label>
              </>
            )}
            <button type="submit">SUBMIT</button>
          </div>
        </form>
        <div>
          {loading ? (
            <p>PROCESSING....</p>
          ) : errorMessage ? (
            <p>{errorMessage}</p>
          ) : (
            imageSrc && (
              <div className="plots">
                <img src={imageSrc} alt={`Pollution ${plotType}`} />
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};

export default App;

import React, { useState } from "react";
import "./App.css";
import logo1 from "./logo1.jpg"; // Replace with your logo path
import logo2 from "./logo2.jpg"; // Replace with your logo path

const App = () => {
  const [city, setCity] = useState("");
  const [pollutant, setPollutant] = useState("");
  const [date, setDate] = useState("");
  const [plotType, setPlotType] = useState(""); // State for plot type
  const [imageSrc, setImageSrc] = useState(""); // State to hold image URL
  const [loading, setLoading] = useState(false); // State to manage loading

  const handleCityChange = (e) => setCity(e.target.value);
  const handlePollutantChange = (e) => setPollutant(e.target.value);
  const handleDateChange = (e) => setDate(e.target.value);
  const handlePlotTypeChange = (e) => setPlotType(e.target.value); // Handle plot type change

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); // Set loading to true when form is submitted

    try {
      const response = await fetch("http://localhost:3001/pollution-data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ city, pollutant, date, plotType }), // Include plot type in the request
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      // Convert response to blob and create an object URL for the image
      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);
      setImageSrc(imageUrl); // Update state with the image URL
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false); // Set loading to false after image is fetched
    }
  };

  return (
    <div className="body">
      <nav>
        <img src={logo1} alt="Logo 1" />
        <h1>Select Pollution Data</h1>
        <img src={logo2} alt="Logo 2" />
      </nav>
      <div className="container">
        <form onSubmit={handleSubmit}>
          <div>
            <label>
              Plot Type:
              <select value={plotType} onChange={handlePlotTypeChange} required>
                <option value="">Select Plot Type</option>
                <option value="Map">Map</option>
                <option value="Time_Series">Time Series</option>
              </select>
            </label>
            <label>
              City:
              <select value={city} onChange={handleCityChange} required>
                <option value="">Select City</option>
                <option value="Hyderabad">Hyderabad</option>
                <option value="Mumbai">Mumbai</option>
                <option value="Chennai">Chennai</option>
                <option value="Banglore">Banglore</option>
                <option value="Kolkata">Kolkata</option>
                <option value="Pune">Pune</option>
                {/* Add more cities as needed */}
              </select>
            </label>
            <label>
              Pollutant:
              <select
                value={pollutant}
                onChange={handlePollutantChange}
                required
              >
                <option value="">Select Pollutant</option>
                <option value="CO">CO</option>
                <option value="HCHO">HCHO</option>
                <option value="NO2">NO2</option>
                <option value="SO2">SO2</option>
              </select>
            </label>
            <label>
              Date:
              <select value={date} onChange={handleDateChange} required>
                <option value="">Select Date</option>
                <option value="2018-04-09 - 2018-07-23">
                  2018-04-09 - 2018-07-23
                </option>
                {/* Add more dates as needed */}
              </select>
            </label>
          </div>
          <button type="submit">Submit</button>
        </form>

        {loading ? (
          <p>Processing...</p>
        ) : (
          imageSrc && (
            <div className="plots">
              <img src={imageSrc} alt={`Pollution ${plotType}`} />
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default App;

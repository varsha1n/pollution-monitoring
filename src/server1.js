const express = require("express");
const bodyParser = require("body-parser");
const { spawn } = require("child_process");
const cors = require("cors");
const path = require("path");
const fs = require("fs");

const app = express();
const port = 3001;

const mapPlotFilePath = path.join(__dirname, "plots", "latest_Map.html");
const timeSeriesPlotFilePath = path.join(
  __dirname,
  "plots",
  "latest_Timeseries.html"
);
const ntlPlotFilePath = path.join(__dirname, "plots", "NTL.png");

// Middleware
app.use(bodyParser.json());
app.use(cors());

// Utility function to execute Python scripts
const executePythonScript = (scriptPath, args) => {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(scriptPath)) {
      return reject(new Error("Python script not found."));
    }

    const pythonProcess = spawn("python", [scriptPath, ...args]);
    let errorData = "";

    pythonProcess.stderr.on("data", (data) => {
      errorData += data.toString();
    });

    pythonProcess.on("error", (error) => {
      reject(new Error(`Failed to start subprocess: ${error.message}`));
    });

    pythonProcess.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(
          new Error("Python script execution failed. Error: " + errorData)
        );
      }
    });
  });
};

app.post("/pollution-data", async (req, res) => {
  const { city, pollutant, startDate, endDate } = req.body;

  if (!city || !pollutant || !startDate || !endDate) {
    return res.status(400).send("All fields are required.");
  }

  const mapPlotFilePath = path.join(__dirname, "plots", "latest_Map.png"); // Path to the PNG file

  try {
    const firstPythonFilePath = path.join(
      __dirname,
      "python",
      `${pollutant}_Map.py`
    );

    // Execute the first Python script
    await executePythonScript(firstPythonFilePath, [city, startDate, endDate]);

    if (fs.existsSync(mapPlotFilePath)) {
      // Send the PNG file
      res.setHeader("Content-Type", "image/png");
      const pngContent = fs.readFileSync(mapPlotFilePath);
      res.send(pngContent);
    } else {
      res.status(404).send("Map plot file not found.");
    }
  } catch (error) {
    console.error(error.message);
    res.status(500).send("Error generating plot. " + error.message);
  }
});

// Endpoint for NTL data
app.post("/ntl-data", async (req, res) => {
  const { ntlCity: city, ntlYear: year, halfYear } = req.body;

  if (!city || !year || !halfYear) {
    return res.status(400).send("All fields are required.");
  }

  try {
    const pythonFilePath = path.join(__dirname, "python", `NTL.py`);
    await executePythonScript(pythonFilePath, [city, year, halfYear]);

    if (fs.existsSync(ntlPlotFilePath)) {
      res.send({
        ntlPlot: fs.readFileSync(ntlPlotFilePath, { encoding: "base64" }),
      });
    } else {
      res.status(404).send("NTL plot file not found.");
    }
  } catch (error) {
    console.error(error.message);
    res.status(500).send("Error generating NTL plot. " + error.message);
  }
});

app.post("/time-series-data", async (req, res) => {
  const {
    timeSeriesCity: city,
    timeSeriesPollutant: pollutant,
    timeSeriesStartDate: startDate,
    timeSeriesEndDate: endDate,
  } = req.body;

  if (!city || !pollutant || !startDate || !endDate) {
    return res.status(400).send("All fields are required.");
  }

  try {
    const pythonFilePath = path.join(
      __dirname,
      "python",
      `${pollutant}_Time_Series.py`
    );
    await executePythonScript(pythonFilePath, [city, startDate, endDate]);

    const timeSeriesPlotFilePath = path.join(
      __dirname,
      "plots",
      "latest_Timeseries.html"
    );

    if (fs.existsSync(timeSeriesPlotFilePath)) {
      const htmlContent = fs.readFileSync(timeSeriesPlotFilePath, {
        encoding: "utf8",
      });
      res.setHeader("Content-Type", "text/html"); // Set content type to HTML
      res.send(htmlContent);
    } else {
      res.status(404).send("Time series plot file not found.");
    }
  } catch (error) {
    console.error(error.message);
    res.status(500).send("Error generating time series plot. " + error.message);
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}/`);
});

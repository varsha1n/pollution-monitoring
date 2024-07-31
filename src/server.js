const express = require("express");
const bodyParser = require("body-parser");
const { spawn } = require("child_process");
const cors = require("cors");
const path = require("path");
const fs = require("fs");

const app = express();
const port = 3001;

const plotFilePath = path.join(__dirname, "plots", "latest_plot.png");

app.use(bodyParser.json());
app.use(cors());

app.post("/pollution-data", (req, res) => {
  const { city, pollutant, startDate, endDate, plotType } = req.body;

  if (!city || !pollutant || !startDate || !endDate || !plotType) {
    return res.status(400).send("All fields are required.");
  }

  const pythonFilePath = path.join(
    __dirname,
    "python",
    `${pollutant}_${plotType}.py`
  );

  if (!fs.existsSync(pythonFilePath)) {
    return res.status(404).send("Python script not found.");
  }

  const pythonProcess = spawn("python", [
    pythonFilePath,
    city,
    startDate,
    endDate,
  ]);

  let errorData = "";

  pythonProcess.stderr.on("data", (data) => {
    errorData += data.toString();
  });

  pythonProcess.on("error", (error) => {
    console.error(`Failed to start subprocess: ${error.message}`);
    res.status(500).send("Failed to start Python script.");
  });

  pythonProcess.on("close", (code) => {
    if (code === 0) {
      if (fs.existsSync(plotFilePath)) {
        res.sendFile(plotFilePath, (err) => {
          if (err) {
            console.error(`Failed to send file: ${err}`);
            res.status(500).send("Failed to send plot file.");
          }
        });
      } else {
        res.status(500).send("Plot file not found.");
      }
    } else {
      console.error("Python script error:", errorData);
      res
        .status(500)
        .send("Python script execution failed. Error: " + errorData);
    }
  });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}/`);
});

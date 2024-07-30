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
  const { city, pollutant, date, plotType } = req.body;

  if (!city || !pollutant || !date || !plotType) {
    return res.status(400).send("All fields are required.");
  }

  var pyfile = "python/" + String(pollutant) + "_" + String(plotType) + ".py";
  // Run the Python script with the provided values
  const pythonProcess = spawn("python", [pyfile, city, date]);

  let errorData = "";

  pythonProcess.stderr.on("data", (data) => {
    console.error(`stderr: ${data}`);
    errorData += data.toString();
  });

  pythonProcess.on("error", (error) => {
    console.error(`Failed to start subprocess: ${error.message}`);
    res.status(500).send("Failed to start Python script.");
  });

  pythonProcess.on("close", (code) => {
    if (code === 0) {
      // Check if the plot file was created
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

const express = require("express");
const app = express();

app.get("/", (req, res) => res.send("Dagster Marketplace"));

app.get("/api/registry", (req, res) =>
  res.json({
    message: "Hello, world!",
    elements: [1, 2, 3, 4, 5],
  }),
);

app.listen(8080, () => console.log("Server ready on port 8080."));

module.exports = app;

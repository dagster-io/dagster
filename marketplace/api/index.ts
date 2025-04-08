import express from "express";

const app = express();

//
// Serve `__generated__` files (e.g. `index.json` at `/integrations/index.json`)
//
app.use("/integrations", express.static("__generated__"));

// Servce static assets, for example:
//
// public/images/dagster-primary-horizontal.svg -> /assets/images/dagster-primary-horizontal.svg
//
app.use("/assets", express.static("public"));

app.listen(8080, () => console.log("Server ready on port 8080."));

module.exports = app;

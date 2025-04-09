import express from "express";

const app = express();

app.get('/', (req, res) => { res.send('Dagster Marketplace API') })

//
// Serve `__generated__` files (e.g. `index.json` at `/api/integrations/index.json`)
//
app.use("/api/integrations", express.static("__generated__"));

// Servce static assets, for example:
//
// public/images/dagster-primary-horizontal.svg -> /assets/images/dagster-primary-horizontal.svg
//
app.use("/assets", express.static("public"));

app.listen(8080, () => console.log("Server ready on port 8080."));

module.exports = app;

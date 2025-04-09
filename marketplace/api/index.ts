import express from 'express';
import path from 'path';

const app = express();

app.get('/', (req, res) => {
  res.send('Dagster Marketplace API');
});

//
// Serve `__generated__` files (e.g. `index.json` at `/api/integrations/index.json`)
//
app.use('/api/integrations', express.static(path.join(__dirname, '../__generated__')));

// Servce static assets, for example:
//
// public/images/dagster-primary-horizontal.svg -> /assets/images/dagster-primary-horizontal.svg
//
app.use('/assets', express.static(path.join(__dirname, '../public')));

app.listen(8080, () => console.log('Server ready on port 8080.'));

module.exports = app;

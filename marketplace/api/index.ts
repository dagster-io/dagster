import express from 'express';
import path from 'path';

const app = express();

app.get('/', (req, res) => {
  res.send('Dagster Marketplace API');
});

/*
 * Serve `__json__` files (e.g. `index.json` at `/api/integrations/index.json`)
 */
app.use('/api/integrations', express.static(path.join(__dirname, '../__json__')));

/*
 * Serve `__logos__` files (e.g. `dagster.svg` at `/api/logos/dagster.svg`)
 */
app.use('/logos', express.static(path.join(__dirname, '../__logos__')));

app.listen(8080, () => console.log('Server ready on port 8080.'));

module.exports = app;

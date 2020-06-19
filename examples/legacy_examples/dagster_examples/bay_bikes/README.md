# Bay Bikes Example

This repository is intended to demo Dagster and Dagit's capabilities for producing datasets and training machine 
learning models. It defines one major pipeline `generate_training_set_and_train_model` which solves the following
time series problem. Given past weather data and historical daily bay bike trip counts, predict the supply of bay bikes
needed today. To solve this problem, we are going to use real world bay bike trip data, and real weather data provided
by lyft and the dark sky weather API. 

## Getting Started

To run the bay bikes demo pipeline locally, you'll need:

    • To be running python 3.6 or greater (the bay bikes demo uses python 3 type annotations).
    • A running Postgres database available at `postgresql://test:test@127.0.0.1:5432/test` (A docker compose file
    is provided in this repo at `dagster/examples`).
    • An API key from `https://darksky.net/dev` which you will then use to set the `DARK_SKY_API_KEY` environment
    variable.

To get up and running:

```python
# Clone Dagster
git clone git@github.com:dagster-io/dagster.git
cd dagster/examples

# Install all dependencies
pip install -e .[full]

# Set DARK_SKY_API_KEY environment variable
export DARK_SKY_API_KEY=<insert key from site>

# Start a local PostgreSQL database
docker-compose up -d

# Load the bay bikes demo in Dagit
cd dagster_examples/bay_bikes
dagit
```

You can now view the bay bikes demo in Dagit at http://127.0.0.1:3000/.

## The Bay Bikes Demo Pipeline

Bay bikes consists of one pipeline `generate_training_set_and_train_model` which consists of 3 major workflows.

    • weather_etl: This is a composite solid that downloads daily weather data from the dark sky API and loads it 
    into a `weather_staging` table.
    • trips_etl: This is a composite solid that downloads monthly trips csv's and batch downloads the data into a 
    `trips_staging` table.
    • train_daily_bike_supply_model: This is a composite solid that downloads all of the data from the `trips_staging` 
    and `weather_staging` table, produces a set of features, converts everything into a training/test set, and 
    trains/uploads an LSTM model that predicts daily bike traffic.
    
To get everything running, use the playground to run the trips_etl composite solid with the trips_etl preset. This will
download all trip data from Jan 2020 into your trips_staging table.

Then use the backfill API by running `dagster pipeline backfill daily_weather_pipeline --mode=development` which will
run 31 daily partitions to populate the weather_etl table for Jan 2020. Note, `daily_weather_pipeline` is just a
placeholder pipeline used to demo the backfill API.

Then you can use the playground to run the `train_daily_bike_supply_model` composite solid with the preset of the 
same name to train a model.

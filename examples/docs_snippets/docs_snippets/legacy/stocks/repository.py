import requests

from dagster import InputDefinition, pipeline, repository, solid

from .schedules import define_schedules
from .simple_partitions import define_partitions

API_URL = "https://financialmodelingprep.com/api/v3/historical-price-full"


@solid(config_schema={"symbol": str, "ds_start": str, "ds_end": str})
def query_historical_stock_data(context):
    symbol = context.solid_config["symbol"]
    ds_start = context.solid_config["ds_start"]
    ds_end = context.solid_config["ds_end"]

    request_url = "{api_url}/{symbol}?from={ds_start}&to={ds_end}".format(
        api_url=API_URL, symbol=symbol, ds_start=ds_start, ds_end=ds_end
    )

    response = requests.get(request_url)
    response.raise_for_status()
    return response.json()


@solid(input_defs=[InputDefinition("json_response", dict)])
def sum_volume(context, json_response):
    historical_data = json_response["historical"]
    total_volume = 0
    for date in historical_data:
        total_volume += date["volume"]

    context.log.info("Total volume: {total_volume}".format(total_volume=str(total_volume)))

    return total_volume


@pipeline
def compute_total_stock_volume():
    sum_volume(query_historical_stock_data())


@repository
def partitioning_tutorial():
    return [compute_total_stock_volume] + define_schedules() + define_partitions()

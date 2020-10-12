import json
import os

import boto3
import requests
from slack import WebClient  # pylint:disable=import-error

from dagster import Array, pipeline, repository, solid


@solid(config_schema={"portfolio": Array(str)})
def query_stock_market_data(context) -> dict:
    portfolio = context.solid_config["portfolio"]

    responses = {}
    for ticker_symbol in portfolio:
        request_url = "{API_URL}/quote/{ticker_symbol}?apikey={API_KEY}".format(
            API_URL="https://financialmodelingprep.com/api/v3",
            API_KEY=os.getenv("DEMO_STOCK_API_KEY"),
            ticker_symbol=ticker_symbol,
        )

        response = requests.get(request_url)
        response.raise_for_status()
        responses[ticker_symbol] = response.json()

    return responses


@solid
def compute_summary_message(_, json_responses: dict) -> str:
    header = "Daily Portfolio Update:\n"
    line_items = []
    for ticker_symbol, response in json_responses.items():
        price = response[0]["price"]
        line_items.append("*{}: *: ${}/share".format(ticker_symbol, price))

    return "{}\n{}".format(header, "\n".join(line_items))


@solid
def send_summary_to_slack(_, message: str):
    client = WebClient(token=os.getenv("DEMO_SLACK_TOKEN"))
    client.chat_postMessage(channel="#portfolio-management", text=message)


@solid
def store_data_in_s3(_, json_responses: dict):
    s3 = boto3.resource("s3")
    for ticker_symbol, response in json_responses.items():
        obj = s3.Object(
            "dagster-stock-data",
            "{date}/{ticker_symbol}.json".format(date="123", ticker_symbol=ticker_symbol),
        )
        obj.put(Body=json.dumps(response))


@pipeline
def my_daily_portfolio_update():
    data = query_stock_market_data()
    send_summary_to_slack(compute_summary_message(data))
    store_data_in_s3(data)


@repository
def my_repository():
    return [my_daily_portfolio_update]

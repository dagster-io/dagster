import json
import os

import boto3
import requests
from slack import WebClient  # pylint:disable=import-error

from dagster import Array, ModeDefinition, ResourceDefinition, pipeline, repository, resource, solid


@resource(config_schema={"slack_token": str})
def slack_resource(context):
    slack_token = context.resource_config["slack_token"]
    client = WebClient(token=slack_token)
    return client


@resource
def mock_slack_resource(context):
    class MockWebClient:
        def chat_postMessage(self, channel, text):
            context.log.info("Message sent to {}: {}".format(channel, text))

    return MockWebClient()


@resource
def s3_resource(_):
    return boto3.resource("s3")


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


@solid(required_resource_keys={"slack"})
def send_summary_to_slack(context, message: str):
    context.resources.slack.chat_postMessage(channel="#portfolio-management", text=message)


@solid(required_resource_keys={"s3"})
def store_data_in_s3(context, json_responses: dict):
    for ticker_symbol, response in json_responses.items():
        obj = context.resources.s3.Object(
            "dagster-stock-data",
            "{date}/{ticker_symbol}.json".format(date="123", ticker_symbol=ticker_symbol),
        )
        obj.put(Body=json.dumps(response))


local_mode = ModeDefinition(
    name="local_mode",
    resource_defs={"slack": mock_slack_resource, "s3": ResourceDefinition.mock_resource()},
)
production_mode = ModeDefinition(
    name="production_mode", resource_defs={"slack": slack_resource, "s3": s3_resource}
)


@pipeline(mode_defs=[local_mode, production_mode])
def my_daily_portfolio_update():
    data = query_stock_market_data()
    send_summary_to_slack(compute_summary_message(data))
    store_data_in_s3(data)


@repository
def my_repository():
    return [my_daily_portfolio_update]

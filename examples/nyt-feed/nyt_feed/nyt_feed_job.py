import csv
import os
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock

import pandas as pd
import requests

from dagster import (
    IOManager,
    InputContext,
    Out,
    Output,
    OutputContext,
    io_manager,
    job,
    op,
    resource,
)

ARTICLES_LINK = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"


class DataframeToCSVIOManager(IOManager):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _get_path(self, output_context: OutputContext):
        return os.path.join(self.base_dir, f"{output_context.step_key}_{output_context.name}.csv")

    def handle_output(self, context: OutputContext, obj: pd.DataFrame):
        obj.to_csv(self._get_path(context), index=False)

    def load_input(self, context: InputContext) -> pd.DataFrame:
        return pd.read_csv(self._get_path(context.upstream_output))


@io_manager(config_schema={"base_dir": str})
def df_to_csv_io_manager(init_context):
    return DataframeToCSVIOManager(base_dir=init_context.resource_config.get("base_dir"))


@resource(config_schema={"token": str})
def mock_slack_resource(_context):
    return MagicMock()


@op(out={"all_articles": Out(is_required=True), "nyc_articles": Out(is_required=False)})
def fetch_stories():
    tree = ET.fromstring(requests.get(ARTICLES_LINK).text)

    all_articles = []
    nyc_articles = []

    for article in tree[0].findall("item"):
        all_articles.append(article)

        if any(category.text == "New York City" for category in article.findall("category")):
            nyc_articles.append(article)

    yield Output(all_articles, "all_articles")

    if nyc_articles:
        yield Output(nyc_articles, "nyc_articles")


@op
def parse_xml(raw_articles):
    rows = []
    for article in raw_articles:
        category_names = [x.text for x in article.findall("category")]
        for category in category_names:
            rows.append(
                {
                    "Title": article.find("title").text,
                    "Link": article.find("link").text,
                    "Category": category,
                    "Description": article.find("description").text,
                }
            )
    return rows


@op(config_schema=str)
def write_to_csv(context, articles):
    with open(context.op_config, "w", encoding="utf8") as csvfile:
        csv_headers = ["Title", "Link", "Category", "Description"]
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(articles)


@op(required_resource_keys={"slack"})
def send_slack_msg(context, articles):
    formatted_str = "\n".join([a["Title"] + ": " + a["Link"] for a in articles])
    context.resources.slack.chat_postMessage(channel="my-news-channel", text=formatted_str)


@job(resource_defs={"slack": mock_slack_resource})
def process_nyt_feed():
    all_articles, nyc_articles = fetch_stories()
    write_to_csv.alias("nyc_csv")(parse_xml(nyc_articles))
    write_to_csv.alias("all_csv")(parse_xml(all_articles))
    send_slack_msg(parse_xml(nyc_articles))

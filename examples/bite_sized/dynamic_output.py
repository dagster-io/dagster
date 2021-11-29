import csv
import re
import os
import xml.etree.ElementTree as ET

import requests
import pandas as pd

from dagster import (
    Out,
    Output,
    job,
    op,
    resource,
    DynamicOut,
    DynamicOutput,
    io_manager,
    OutputContext,
)

from bite_sized.conditional_branching import DataframeToCSVIOManager

ARTICLES_LINK = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"


class DynamicOutIOManager(DataframeToCSVIOManager):
    def _get_path(self, output_context: OutputContext):
        return os.path.join(
            self.base_dir,
            f"{output_context.step_key}_{output_context.name}_{output_context.mapping_key}.csv",
        )


@io_manager(config_schema={"base_dir": str})
def dynamic_df_to_csv_io_manager(init_context):
    return DynamicOutIOManager(base_dir=init_context.resource_config.get("base_dir"))


@op(out=DynamicOut())
def fetch_articles_df():
    tree = ET.fromstring(requests.get(ARTICLES_LINK).text)

    articles_by_category = {}

    for article in tree[0].findall("item"):
        for category in article.findall("category"):
            category_name = category.text
            if category_name not in articles_by_category:
                articles_by_category[category_name] = []
            articles_by_category[category_name].append(
                {
                    "Title": article.find("title").text,
                    "Link": article.find("link").text,
                    "Category": category_name,
                    "Description": article.find("description").text,
                }
            )

    for category_name, articles in articles_by_category.items():
        yield DynamicOutput(pd.DataFrame(articles), mapping_key=re.sub(r"\W+", "", category_name))


@job(resource_defs={"io_manager": dynamic_df_to_csv_io_manager})
def dynamic_output():
    fetch_articles_df()

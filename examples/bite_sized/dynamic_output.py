import csv
import re
import xml.etree.ElementTree as ET

import requests
import pandas as pd
from dagster import Out, Output, job, op, resource, DynamicOut, DynamicOutput

ARTICLES_LINK = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"


@op(out=DynamicOut())
def fetch_articles():
    tree = ET.fromstring(requests.get(ARTICLES_LINK).text)

    articles_by_category = {}

    for article in tree[0].findall("item")[:10]:
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
        yield DynamicOutput(
            (category_name, articles), mapping_key=re.sub(r'\W+', '', category_name)
        )


@op
def write_to_csv(context, category_articles):
    category, articles = category_articles
    with open(f"{category}.csv", "w") as csvfile:
        csv_headers = ["Title", "Link", "Category", "Description"]
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(articles)


@job
def dynamic_output():
    fetch_articles().map(write_to_csv)

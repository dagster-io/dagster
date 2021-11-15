import requests
import csv
import xml.etree.ElementTree as ET
from dagster import Out, Output, job, op
from dagster_slack.resources import slack_resource

ARTICLES_LINK = 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'


@op(out={"all_articles": Out(is_required=True), "nyc_articles": Out(is_required=False)})
def fetch_stories(context):
    tree = ET.fromstring(requests.get(ARTICLES_LINK).text)

    all_articles = []
    nyc_articles = []

    for article in tree[0].findall('item'):
        all_articles.append(article)

        if [
            category for category in article.findall('category') if category.text == "New York City"
        ]:
            nyc_articles.append(article)

    yield Output(all_articles, "all_articles")

    if nyc_articles:
        yield Output(nyc_articles, "nyc_articles")


@op
def parse_xml(raw_articles):
    rows = []
    for article in raw_articles:
        category_names = [x.text for x in article.findall('category')]
        for category in category_names:
            rows.append(
                {
                    "Title": article.find('title').text,
                    "Link": article.find('link').text,
                    "Category": category,
                    "Description": article.find('description').text,
                }
            )
    return rows


@op(config_schema=str)
def write_to_csv(context, articles):
    with open(context.op_config, "w") as csvfile:
        csv_headers = ["Title", "Link", "Category", "Description"]
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(articles)


@op(required_resource_keys={"slack_resource"})
def send_slack_msg(context, articles):
    formatted_str = '\n'.join([a["Title"] + ": " + a["Link"] for a in articles])
    context.resources.slack.chat_postMessage(channel="my-news-channel", text=formatted_str)


@job(
    resource_defs={"slack_resource": slack_resource},
)
def branching():
    all_articles, nyc_articles = fetch_stories()
    write_to_csv.alias("nyc_csv")(parse_xml(nyc_articles))
    write_to_csv.alias("all_csv")(parse_xml(all_articles))
    send_slack_msg(parse_xml(nyc_articles))

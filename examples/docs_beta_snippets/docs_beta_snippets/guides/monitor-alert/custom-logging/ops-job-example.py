import requests

import dagster as dg
from dagster import json_console_logger

LOGGER_CONFIG = {"loggers": {"console": {"config": {"log_level": "INFO"}}}}


@dg.op
def get_hackernews_topstory_ids(context: dg.OpExecutionContext):
    """Get up to 500 top stories from the HackerNews topstories endpoint.

    API Docs: https://github.com/HackerNews/API#new-top-and-best-stories
    """
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_500_newstories = requests.get(newstories_url).json()
    # Log the number of stories fetched
    context.log.info(f"Compute Logger - Got {len(top_500_newstories)} top stories.")
    return top_500_newstories


@dg.job(logger_defs={"console": json_console_logger}, config=LOGGER_CONFIG)
def hackernews_topstory_ids_job():
    get_hackernews_topstory_ids()


defs = dg.Definitions(
    jobs=[hackernews_topstory_ids_job],
)

# copy to a file called hello-dagster.py
from dagster import repository, asset, MetadataValue
import requests
import pandas as pd

# dagster helps you think about datasets, models, 
# and other objects that you want to exist as assets
# instead of worrying about tasks

@asset
def hackernews_topstory_ids():
    """
    Get up to 500 top stories from the HackerNews topstories endpoint.
    API Docs: https://github.com/HackerNews/API#new-top-and-best-stories
    """
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_500_newstories = requests.get(newstories_url).json()
    return top_500_newstories

# dependencies between assets can be expressed as function arguments
@asset 
def hackernews_topstories(context, hackernews_topstory_ids):
    """
    Get items based on story ids from the HackerNews items endpoint
    """

    results = []
    for item_id in hackernews_topstory_ids:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
        results.append(item)
        if len(results) >= 10:
            break

    df = pd.DataFrame(results)

    # dagster tracks rich metadata about our assets
    context.add_output_metadata(
        {
            "num_records": len(df),
            "preview": MetadataValue.md(df.to_markdown()),
        }
    )
    return df

@repository
def hello_dagster():
    return [hackernews_topstory_ids, hackernews_topstories]
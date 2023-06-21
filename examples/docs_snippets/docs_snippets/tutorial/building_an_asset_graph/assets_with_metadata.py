# start_topstories_asset_with_metadata
import base64
from io import BytesIO

import duckdb
import matplotlib.pyplot as plt
import pandas as pd
import requests

from dagster import (
    MetadataValue,
    Output,
    asset,
    get_dagster_logger,
)

# Add the imports above to the top of `assets.py`


@asset
def topstories(context, topstory_ids):
    logger = get_dagster_logger()

    with open("topstory_ids.txt", "r") as input_file:
        ids = input_file.read().split(",")

    results = []
    for item_id in ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            logger.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    conn = duckdb.connect('analytics.db')
    conn.execute("create or replace table topstories as select * from df")

    context.add_output_metadata({
        "preview": MetadataValue.md(df.head().to_markdown()),
        "num_stories": MetadataValue.int(len(df)),
    })

# end_topstories_asset_with_metadata


# start_most_frequent_words_asset_with_metadata
@asset
def most_frequent_words(topstories):
    stopwords = ["a", "the", "an", "of", "to", "in", "for", "and", "with", "on", "is"]

    # loop through the titles and count the frequency of each word
    word_counts = {}
    for raw_title in topstories["title"]:
        title = raw_title.lower()
        for word in title.split():
            cleaned_word = word.strip(".,-!?:;()[]'\"-")
            if cleaned_word not in stopwords and len(cleaned_word) > 0:
                word_counts[cleaned_word] = word_counts.get(cleaned_word, 0) + 1

    # Get the top 25 most frequent words
    top_words = {
        pair[0]: pair[1]
        for pair in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:25]
    }

    # Make a bar chart of the top 25 words
    plt.figure(figsize=(10, 6))
    plt.bar(top_words.keys(), top_words.values())
    plt.xticks(rotation=45, ha="right")
    plt.title("Top 25 Words in Hacker News Titles")
    plt.tight_layout()

    # Convert the image to a saveable format
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())

    # Convert the image to Markdown to preview it within Dagster
    md_content = f"![img](data:image/png;base64,{image_data.decode()})"

    # Attach the Markdown content as metadata to the asset
    return Output(
        value=top_words,
        metadata={"plot": MetadataValue.md(md_content)},
    )


# end_most_frequent_words_asset_with_metadata

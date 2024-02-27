import base64  # noqa: I001
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import requests

from dagster import asset

# start_topstory_ids_asset


from typing import Dict, List  # add imports to the top of `assets.py`


@asset
def topstory_ids() -> List:  # modify return type signature
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_new_story_ids = requests.get(newstories_url).json()[:100]

    return (
        top_new_story_ids  # return top_new_story_ids and the I/O manager will save it
    )


# end_topstory_ids_asset

# start_topstories_asset


from dagster import AssetExecutionContext, MetadataValue, asset, get_dagster_logger


@asset  # remove deps parameter
def topstories(
    context: AssetExecutionContext,
    topstory_ids: List,  # add topstory_ids as a function argument
) -> pd.DataFrame:  # modify the return type signature
    logger = get_dagster_logger()

    # remove manually loading topstory_ids

    results = []
    for item_id in topstory_ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            logger.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    # remove manually saving df

    context.add_output_metadata(
        metadata={
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )

    return df  # return df and the I/O manager will save it


# end_topstories_asset


# start_most_frequent_words_asset


@asset  # remove deps parameter
def most_frequent_words(
    context: AssetExecutionContext,
    topstories: pd.DataFrame,  # add topstories as a function argument
) -> Dict:  # modify the return type signature
    stopwords = ["a", "the", "an", "of", "to", "in", "for", "and", "with", "on", "is"]

    # remove manually loading topstory_ids

    word_counts = {}
    for raw_title in topstories["title"]:
        title = raw_title.lower()
        for word in title.split():
            cleaned_word = word.strip(".,-!?:;()[]'\"-")
            if cleaned_word not in stopwords and len(cleaned_word) > 0:
                word_counts[cleaned_word] = word_counts.get(cleaned_word, 0) + 1

    top_words = {
        pair[0]: pair[1]
        for pair in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:25]
    }

    plt.figure(figsize=(10, 6))
    plt.bar(list(top_words.keys()), list(top_words.values()))
    plt.xticks(rotation=45, ha="right")
    plt.title("Top 25 Words in Hacker News Titles")
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())

    md_content = f"![img](data:image/png;base64,{image_data.decode()})"

    # remove manually saving top_words

    context.add_output_metadata(metadata={"plot": MetadataValue.md(md_content)})

    return top_words  # return top_words and the I/O manager will save it


# end_most_frequent_words_asset

from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import requests
from wordcloud import STOPWORDS, WordCloud
from dagster import (
    Field,
    MetadataValue,
    OpExecutionContext,
    asset,
    StringSource,
)
import base64
from io import BytesIO


@asset(group_name="hackernews", compute_kind="HackerNews API")
def hackernews_topstory_ids() -> List[int]:
    """
    Get up to 500 top stories from the HackerNews topstories endpoint.

    Docs: https://github.com/HackerNews/API#new-top-and-best-stories
    """
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_500_newstories = requests.get(newstories_url).json()
    return top_500_newstories


@asset(group_name="hackernews", compute_kind="HackerNews API")
def hackernews_topstories(
    context: OpExecutionContext, hackernews_topstory_ids: List[int]
) -> pd.DataFrame:
    """
    Get items based on story ids from the HackerNews items endpoint. It may take 1-2 minutes to fetch all 500 items.

    Docs: https://github.com/HackerNews/API#items
    """

    results = []
    for item_id in hackernews_topstory_ids:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
        results.append(item)
        if len(results) % 20 == 0:
            context.log.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    # Dagster supports attaching arbitrary metadata to asset materializations. This metadata will be
    # shown in the run logs and also be displayed on the "Activity" tab of the "Asset Details" page in the UI.
    # This metadata would be useful for monitoring and maintaining the asset as you iterate.
    # Read more: https://docs.dagster.io/concepts/assets/software-defined-assets#recording-materialization-metadata
    context.add_output_metadata(
        {
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )
    return df


@asset(
    group_name="hackernews",
    compute_kind="Plot",
    config_schema={
        "github_token": Field(StringSource, default_value={"env": "MY_GITHUB_TOKEN"}),
    },
)
def hackernews_topstories_word_cloud(
    context: OpExecutionContext, hackernews_topstories: pd.DataFrame
) -> bytes:
    """
    Exploratory analysis: Generate a word cloud from the current top 500 HN top stories. Embed the
    plot into a Markdown metadata.

    Docs: TODO word cloud doc link
    """
    stopwords = set(STOPWORDS)
    stopwords.update(["Ask", "Show", "HN"])
    titles_text = " ".join([str(item) for item in hackernews_topstories["title"]])
    context.pdb.set_trace()
    titles_cloud = WordCloud(stopwords=stopwords, background_color="white").generate(titles_text)

    # Generate the word cloud image
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(titles_cloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)

    # Save the image to a buffer and embed the image into a Markdown metadata attached to the asset
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())
    md_content = f"![img](data:image/png;base64,{image_data.decode()})"

    context.add_output_metadata({"plot": MetadataValue.md(md_content)})

    return image_data

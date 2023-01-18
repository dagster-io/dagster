import base64
from io import BytesIO
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import requests
from wordcloud import STOPWORDS, WordCloud

# start_hackernews_dagster_imports
from dagster import asset, MetadataValue, OpExecutionContext
# end_hackernews_dagster_imports

# start_topstory_ids_asset_marker


@asset(group_name="hackernews", compute_kind="HackerNews API")
def hackernews_topstory_ids() -> List[int]:
    """
    Get up to 100 top stories from the HackerNews topstories endpoint.

    API Docs: https://github.com/HackerNews/API#new-top-and-best-stories
    """
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_100_newstories = requests.get(newstories_url).json()
    return top_100_newstories


# start_topstory_ids_asset_marker

# start_topstories_asset_marker


@asset(group_name="hackernews", compute_kind="HackerNews API")
def hackernews_topstories(
    context: OpExecutionContext, hackernews_topstory_ids: List[int]
) -> pd.DataFrame:
    results = []
    for item_id in hackernews_topstory_ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

    df = pd.DataFrame(results)

    context.add_output_metadata(
        {
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )
    return df


# end_topstories_asset_marker


@asset(group_name="hackernews", compute_kind="Plot")
def hackernews_topstories_word_cloud(
    context: OpExecutionContext, hackernews_topstories: pd.DataFrame
) -> bytes:
    """
    Exploratory analysis: Generate a word cloud from the current top 100 HackerNews top stories.
    Embed the plot into a Markdown metadata for quick view.

    Read more about how to create word clouds in http://amueller.github.io/word_cloud/.
    """
    stopwords = set(STOPWORDS)
    stopwords.update(["Ask", "Show", "HN"])
    titles_text = " ".join([str(item) for item in hackernews_topstories["title"]])
    titles_cloud = WordCloud(stopwords=stopwords, background_color="white").generate(
        titles_text
    )

    # Generate the word cloud image
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(titles_cloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)

    # Save the image to a buffer and embed the image into Markdown content for quick view
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())
    md_content = f"![img](data:image/png;base64,{image_data.decode()})"

    # Attach the Markdown content as metadata to the asset
    # Read about more metadata types in https://docs.dagster.io/_apidocs/ops#metadata-types
    context.add_output_metadata({"plot": MetadataValue.md(md_content)})

    return image_data

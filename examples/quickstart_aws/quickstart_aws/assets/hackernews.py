import base64
import os
from io import BytesIO, StringIO

import matplotlib.pyplot as plt
import pandas as pd
import requests
from dagster import AssetExecutionContext, MaterializeResult, MetadataValue, asset
from dagster_aws.s3 import S3Resource

HACKERNEWS_TOPSTORY_IDS_CSV = "hackernews_topstory_ids.csv"
HACKERNEWS_TOPSTORIES_CSV = "hackernews_topstories.csv"
BAR_CHART_FILE_NAME = "hackernews_topstories_bar_chart.png"

S3_BUCKET = os.environ.get("S3_BUCKET")


@asset(group_name="hackernews", compute_kind="HackerNews API")
def hackernews_topstory_ids(s3: S3Resource) -> None:
    """Get up to 500 top stories from the HackerNews topstories endpoint.

    API Docs: https://github.com/HackerNews/API#new-top-and-best-stories
    """
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_500_newstories = requests.get(newstories_url).json()

    # write the top 500 story ids to an S3 bucket
    s3.get_client().put_object(
        Body=str(top_500_newstories),
        Bucket=S3_BUCKET,
        Key=HACKERNEWS_TOPSTORY_IDS_CSV,
    )


@asset(
    deps=[hackernews_topstory_ids],
    group_name="hackernews",
    compute_kind="HackerNews API",
)
def hackernews_topstories(
    context: AssetExecutionContext,
    s3: S3Resource,
) -> MaterializeResult:
    """Get items based on story ids from the HackerNews items endpoint. It may take 1-2 minutes to fetch all 500 items.

    API Docs: https://github.com/HackerNews/API#items
    """
    # read the top 500 story ids from an S3 bucket
    hackernews_topstory_ids = s3.get_client().get_object(
        Bucket=S3_BUCKET, Key=HACKERNEWS_TOPSTORY_IDS_CSV
    )

    results = []
    for item_id in hackernews_topstory_ids["item_ids"]:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
        results.append(item)
        if len(results) % 20 == 0:
            context.log.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    object_body = df.to_csv(index=False)

    # write the dataframe to an S3 bucket
    s3.get_client().put_object(
        Body=object_body,
        Bucket=S3_BUCKET,
        Key=HACKERNEWS_TOPSTORIES_CSV,
    )

    return MaterializeResult(
        # Dagster supports attaching arbitrary metadata to asset materializations. This metadata will be
        # shown in the run logs and also be displayed on the "Activity" tab of the "Asset Details" page in the UI.
        # This metadata would be useful for monitoring and maintaining the asset as you iterate.
        # Read more about in asset metadata in https://docs.dagster.io/concepts/metadata-tags/asset-metadata
        metadata={
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        },
    )


@asset(deps=[hackernews_topstories], group_name="hackernews", compute_kind="Plot")
def most_frequent_words(
    s3: S3Resource,
) -> MaterializeResult:
    """Exploratory analysis: Generate a bar chart from the current top 500 HackerNews top stories.
    Embed the plot into a Markdown metadata for quick view.
    """
    stopwords = ["a", "the", "an", "of", "to", "in", "for", "and", "with", "on", "is"]

    # read the topstories CSV from an S3 bucket
    topstories = pd.read_csv(
        StringIO(
            s3.get_client()
            .get_object(Bucket=S3_BUCKET, Key=HACKERNEWS_TOPSTORIES_CSV)["Body"]
            .read()
        )
    )

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
    plt.bar(list(top_words.keys()), list(top_words.values()))
    plt.xticks(rotation=45, ha="right")
    plt.title("Top 25 Words in Hacker News Titles")
    plt.tight_layout()

    # Save the image to a buffer and embed the image into Markdown content for quick view
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())
    md_content = f"![img](data:image/png;base64,{image_data.decode()})"

    # Also, upload the image to S3

    bucket_location = s3.get_client().get_bucket_location(Bucket=S3_BUCKET)["LocationConstraint"]
    s3.get_client().upload_fileobj(buffer, S3_BUCKET, BAR_CHART_FILE_NAME)
    s3_path = f"https://s3.{bucket_location}.amazonaws.com/{S3_BUCKET}/{BAR_CHART_FILE_NAME}"

    return MaterializeResult(
        metadata={
            # Attach the Markdown content and s3 file path as metadata to the asset
            # Read about more metadata types in https://docs.dagster.io/_apidocs/ops#metadata-types
            "plot": MetadataValue.md(md_content),
            "plot_s3_path": MetadataValue.url(s3_path),
        }
    )

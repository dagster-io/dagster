# start_topstories_asset_with_metadata
from dagster import asset, get_dagster_logger, MetadataValue, Output, DagsterInstance, AssetKey
from io import BytesIO
import matplotlib.pyplot as plt
import base64
# Add the imports above to the top of `assets.py`

@asset
def topstories(topstory_ids):
    logger = get_dagster_logger()

    results = []
    for item_id in topstory_ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            logger.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    return Output(  # The return value is updated to wrap it in `Output` class
        value=df,   # The original df is passed in with the `value` parameter
        metadata={
            "num_records": len(df), # Metadata can be any key-value pair
            "preview": MetadataValue.md(df.head().to_markdown()),
            # The `MetadataValue` class has useful static methods to build Metadata
        }
    )
# end_topstories_asset_with_metadata



# start_most_frequent_words_asset_with_metadata
@asset
def most_frequent_words(topstories):
    stopwords = ["a", "the", "an", "of", "to", "in", "for", "and", "with", "on", "is"]

    # loop through the titles and count the frequency of each word
    word_counts = {}
    for title in topstories["title"]:
        title = title.lower()
        for word in title.split():
            cleaned_word = word.strip(".,-!?:;()[]'\"-")
            if cleaned_word not in stopwords and len(cleaned_word) > 0:
                word_counts[cleaned_word] = word_counts.get(cleaned_word, 0) + 1

    # Get the top 25 most frequent words
    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:25]

    # Make a bar chart of the top 25 words
    plt.figure(figsize=(10, 6))
    plt.bar(
        [word for word, _count in top_words],
        [count for _word, count in top_words],
        color="orange",
    )
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
        metadata={
            "plot": MetadataValue.md(md_content)
        },
    )
# end_most_frequent_words_asset_with_metadata
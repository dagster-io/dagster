import base64
import json
import sys
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
from dagster._utils import file_relative_path
from utils import NamespaceAwareStorage
from wordcloud import STOPWORDS, WordCloud


def transform(hackernews_topstories: pd.DataFrame) -> str:
    stopwords = set(STOPWORDS)
    stopwords.update(["Ask", "Show", "HN"])
    titles_text = " ".join([str(item) for item in hackernews_topstories["title"]])
    titles_cloud = WordCloud(stopwords=stopwords, background_color="white").generate(titles_text)

    # Generate the word cloud image
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(titles_cloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)

    # Save the image to a buffer
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())
    return f"""
# Wordcloud of top Hacker News stories

![img](data:image/png;base64,{image_data.decode()})
""".strip()


if __name__ == "__main__":
    asset_namespace_lookup_json = sys.argv[1]
    asset_namespace_lookup = json.loads(asset_namespace_lookup_json)
    assert isinstance(asset_namespace_lookup, dict)
    storage_root = file_relative_path(__file__, "storage")

    namespace_aware_storage = NamespaceAwareStorage(
        storage_root=storage_root, asset_namespace_lookup=asset_namespace_lookup
    )

    input_asset_key = "hackernews_source_data"

    hackernews_source_data_df = namespace_aware_storage.load_object(input_asset_key)

    hackernews_wordcloud_df = transform(hackernews_source_data_df)

    output_asset_key = "hackernews_wordcloud"
    namespace_aware_storage.write_object(asset_key=output_asset_key, obj=hackernews_wordcloud_df)

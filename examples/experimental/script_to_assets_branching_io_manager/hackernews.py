import base64
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import requests
from tqdm import tqdm
from wordcloud import STOPWORDS, WordCloud


def extract() -> pd.DataFrame:
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    hackernews_topstory_ids = requests.get(newstories_url).json()

    results = []
    for item_id in tqdm(hackernews_topstory_ids[:100]):
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
        results.append(item)

    hackernews_topstories = pd.DataFrame(results)

    return hackernews_topstories


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


def load(md_content: str):
    with open("output.md", "w") as f:
        f.write(md_content)


if __name__ == "__main__":
    inp = extract()
    output = transform(inp)
    load(output)

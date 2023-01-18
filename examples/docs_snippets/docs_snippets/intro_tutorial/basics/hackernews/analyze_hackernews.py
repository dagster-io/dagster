import requests
import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import STOPWORDS, WordCloud


newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
top_100_newstories = requests.get(newstories_url).json()[:100]


results = []
for item_id in top_100_newstories:
    item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
    results.append(item)

    if len(results) % 20 == 0:
        print(f"Got {len(results)} items so far.")

df = pd.DataFrame(results)


stopwords = set(STOPWORDS)
stopwords.update(["Ask", "Show", "HN", "S"])
titles_text = " ".join([str(item) for item in df["title"]])
titles_cloud = WordCloud(stopwords=stopwords, background_color="white").generate(titles_text)

plt.figure(figsize=(8, 8), facecolor=None)
plt.imshow(titles_cloud, interpolation="bilinear")
plt.axis("off")
plt.tight_layout(pad=0)


plt.show()
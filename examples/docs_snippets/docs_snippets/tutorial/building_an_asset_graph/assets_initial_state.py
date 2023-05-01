# start_topstories_asset
import pandas as pd  # Add new imports to the top of `assets.py`
import requests

from dagster import asset


@asset
def topstories(topstory_ids):  # this asset is dependent on topstory_ids
    results = []
    for item_id in topstory_ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            print(f"Got {len(results)} items so far.") # noqa: T201

    df = pd.DataFrame(results)

    return df


# end_topstories_asset


# start_most_frequent_words_asset
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
    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:25]

    return top_words


# end_most_frequent_words_asset

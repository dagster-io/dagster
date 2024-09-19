# start_stopwords_zip
import urllib.request  # Addition: new import at the top of `assets.py`

from dagster import asset


@asset
def stopwords_zip() -> None:
    urllib.request.urlretrieve(
        "https://docs.dagster.io/assets/stopwords.zip",
        "data/stopwords.zip",
    )


# end_stopwords_zip

# start_stopwords_csv
import zipfile  # Note: remember to add imports to the top of the file


@asset(deps=[stopwords_zip])
def stopwords_csv() -> None:
    with zipfile.ZipFile("data/stopwords.zip", "r") as zip_ref:
        zip_ref.extractall("data")


# end_stopwords_csv


@asset
def topstories():
    pass


# start_updated_most_frequent_words
import csv  # Note: Remember to add all new imports to the top


@asset(
    deps=[stopwords_csv],  # Addition: added the dependency
)
def most_frequent_words(topstories):
    # stopwords = ["a", "the", "an", "of", "to", "in", "for", "and", "with", "on", "is"]
    # Remove the line above

    # Replace the with the two lines below
    with open("data/stopwords.csv", "r") as f:
        stopwords = {row[0] for row in csv.reader(f)}

    # ...

    # Keep the rest of the function the same
    # end_updated_most_frequent_words

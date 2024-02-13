import json
import os

import pandas as pd

from dagster import build_asset_context
from dagster._utils import pushd
from docs_snippets.tutorial.building_an_asset_graph import (
    asset_with_logger,
    assets_initial_state,
    assets_with_metadata,
)


def test_most_frequent_words(tmpdir):
    data = pd.DataFrame(
        [
            {"title": "The quick brown fox"},
            {"title": "The quick brown fox jumps over the lazy dog"},
        ]
    )

    expected = {
        "quick": 2,
        "brown": 2,
        "fox": 2,
        "jumps": 1,
        "over": 1,
        "lazy": 1,
        "dog": 1,
    }

    with pushd(tmpdir):
        os.makedirs("data", exist_ok=True)
        data.to_csv("data/topstories.csv")

        assets_initial_state.most_frequent_words()

        with open("data/most_frequent_words.json") as f:
            results = json.load(f)

    assert results == expected


def test_most_frequent_words_with_metadata(tmpdir):
    data = pd.DataFrame(
        [
            {"title": "The quick brown fox"},
            {"title": "The quick brown fox jumps over the lazy dog"},
        ]
    )

    expected = {
        "quick": 2,
        "brown": 2,
        "fox": 2,
        "jumps": 1,
        "over": 1,
        "lazy": 1,
        "dog": 1,
    }

    with pushd(tmpdir):
        os.makedirs("data", exist_ok=True)
        data.to_csv("data/topstories.csv")

        context = build_asset_context()
        assets_with_metadata.most_frequent_words(context)

        with open("data/most_frequent_words.json") as f:
            results = json.load(f)

    assert results == expected

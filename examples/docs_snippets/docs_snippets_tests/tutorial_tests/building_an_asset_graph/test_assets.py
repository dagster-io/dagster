from docs_snippets.tutorial.building_an_asset_graph import (
    assets_initial_state,
    asset_with_logger,
    assets_with_metadata,
)

import pandas as pd

def test_most_frequent_words():
    input = pd.DataFrame([
        {"title": "The quick brown fox"},
        {"title": "The quick brown fox jumps over the lazy dog"},
    ])

    expected = {
        "quick": 2,
        "brown": 2,
        "fox": 2,
        "jumps": 1,
        "over": 1,
        "lazy": 1,
        "dog": 1,
    }

    results = assets_initial_state.most_frequent_words(input)

    assert results == expected

def test_most_frequent_words_with_metadata():
    input = pd.DataFrame([
        {"title": "The quick brown fox"},
        {"title": "The quick brown fox jumps over the lazy dog"},
    ])

    expected = {
        "quick": 2,
        "brown": 2,
        "fox": 2,
        "jumps": 1,
        "over": 1,
        "lazy": 1,
        "dog": 1,
    }

    results = assets_with_metadata.most_frequent_words(input)

    assert results.value == expected
    assert results.metadata is not None
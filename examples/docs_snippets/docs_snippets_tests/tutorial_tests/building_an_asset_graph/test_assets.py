import pandas as pd

from docs_snippets.tutorial.building_an_asset_graph import (
    asset_with_logger,
    assets_initial_state,
    assets_with_metadata,
)


def test_most_frequent_words():
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

    results = assets_initial_state.most_frequent_words(data)

    assert results == expected


def test_most_frequent_words_with_metadata():
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

    results = assets_with_metadata.most_frequent_words(data)

    assert results.value == expected
    assert results.metadata is not None

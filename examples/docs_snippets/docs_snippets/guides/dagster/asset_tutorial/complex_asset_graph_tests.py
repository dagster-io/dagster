"""isort:skip_file"""
from docs_snippets.guides.dagster.asset_tutorial.complex_asset_graph import (
    cereals,
    cereal_protein_fractions,
    highest_protein_nabisco_cereal,
    nabisco_cereals,
)


# start_asset_test
def test_nabisco_cereals():
    cereals = [
        {"name": "cereal1", "mfr": "N"},
        {"name": "cereal2", "mfr": "K"},
    ]
    result = nabisco_cereals(cereals)
    assert len(result) == 1
    assert result == [{"name": "cereal1", "mfr": "N"}]


# end_asset_test

# start_asset_group_test
from dagster import AssetGroup


def test_cereal_asset_group():
    group = AssetGroup(
        [
            nabisco_cereals,
            cereals,
            cereal_protein_fractions,
            highest_protein_nabisco_cereal,
        ]
    )

    result = group.materialize()
    assert result.success
    assert result.output_for_node("highest_protein_nabisco_cereal") == "100% Bran"


# end_asset_group_test

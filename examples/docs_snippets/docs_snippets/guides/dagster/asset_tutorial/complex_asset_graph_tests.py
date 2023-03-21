# isort: skip_file
from docs_snippets.guides.dagster.asset_tutorial.complex_asset_graph import (
    cereal_protein_fractions,
    cereals,
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

# start_all_assets_test
from dagster import materialize


def test_cereal_assets():
    assets = [
        nabisco_cereals,
        cereals,
        cereal_protein_fractions,
        highest_protein_nabisco_cereal,
    ]

    result = materialize(assets)
    assert result.success
    assert result.output_for_node("highest_protein_nabisco_cereal") == "100% Bran"


# end_all_assets_test

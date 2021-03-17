from dagster import execute_solid
from docs_snippets.concepts.assets.materialization_solids import (
    my_simple_solid,
    my_materialization_solid,
    my_constant_asset_solid,
    my_variable_asset_solid,
    my_metadata_materialization_solid,
    my_asset_key_materialization_solid,
)


def test_solids_compile_and_execute():
    solids = [
        my_simple_solid,
        my_materialization_solid,
        my_constant_asset_solid,
        my_variable_asset_solid,
        my_metadata_materialization_solid,
        my_asset_key_materialization_solid,
    ]

    for solid in solids:
        result = execute_solid(solid)
        assert result
        assert result.success

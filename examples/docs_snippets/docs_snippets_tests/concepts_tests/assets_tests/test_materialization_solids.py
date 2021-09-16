from dagster import execute_solid
from docs_snippets.concepts.assets.materialization_solids import (
    my_asset_key_materialization_solid,
    my_asset_solid,
    my_constant_asset_solid,
    my_materialization_solid,
    my_metadata_materialization_solid,
    my_partitioned_asset_solid,
    my_simple_solid,
    my_variable_asset_solid,
)


def test_solids_compile_and_execute():
    solids = [
        my_asset_key_materialization_solid,
        my_constant_asset_solid,
        my_materialization_solid,
        my_metadata_materialization_solid,
        my_simple_solid,
        my_variable_asset_solid,
        my_asset_solid,
    ]

    for solid in solids:
        result = execute_solid(solid)
        assert result
        assert result.success


def test_partition_config_solids_compile_and_execute():
    solids = [
        my_partitioned_asset_solid,
    ]

    for solid in solids:
        config = {"solids": {solid.name: {"config": {"date": "2020-01-01"}}}}
        result = execute_solid(solid, run_config=config)
        assert result
        assert result.success

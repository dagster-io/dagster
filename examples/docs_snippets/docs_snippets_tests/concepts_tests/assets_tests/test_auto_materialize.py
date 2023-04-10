from dagster import Definitions, load_assets_from_modules
from docs_snippets.concepts.assets import (
    auto_materialize_eager,
    auto_materialize_lazy,
    auto_materialize_lazy_transitive,
    auto_materialize_time_partitions,
)


def test_auto_materialize_eager_asset_defs():
    Definitions(assets=load_assets_from_modules([auto_materialize_eager]))


def test_auto_materialize_lazy_asset_defs():
    Definitions(assets=load_assets_from_modules([auto_materialize_lazy]))


def test_auto_materialize_lazy_transitive_asset_defs():
    Definitions(assets=load_assets_from_modules([auto_materialize_lazy_transitive]))


def test_auto_materialize_observable_source_asset():
    from docs_snippets.concepts.assets.auto_materialize_observable_source_asset import (
        defs,
    )

    assert defs


def test_auto_materialize_time_partitions():
    Definitions(assets=load_assets_from_modules([auto_materialize_time_partitions]))

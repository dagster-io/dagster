import dagster as dg
import project_dbt.defs
import pytest
from project_dbt.defs.assets import metrics, trips
from project_dbt.defs.resources import database_resource

from tests.fixtures import setup_dbt_env  # noqa: F401


@pytest.fixture()
def defs():
    return dg.Definitions.merge(dg.components.load_defs(project_dbt.defs))


def test_trips_partitioned_assets(setup_dbt_env, defs):  # noqa: F811
    assets = [
        trips.taxi_trips_file,
        trips.taxi_zones_file,
        trips.taxi_trips,
        trips.taxi_zones,
        defs.get_assets_def(dg.AssetKey(["taxi_daily_metrics"])),
        defs.get_assets_def(dg.AssetKey(["taxi_location_metrics"])),
        defs.get_assets_def(dg.AssetKey(["taxi_stg_trips"])),
        defs.get_assets_def(dg.AssetKey(["taxi_stg_zones"])),
        metrics.manhattan_stats,
    ]
    result = dg.materialize(
        assets=assets,
        resources={
            "database": database_resource,
        },
        partition_key="2023-01-01",
    )
    assert result.success


def test_defs(setup_dbt_env, defs):  # noqa: F811
    assert defs

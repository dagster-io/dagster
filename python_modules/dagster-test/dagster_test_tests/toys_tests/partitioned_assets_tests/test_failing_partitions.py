from dagster import Definitions, load_assets_from_modules
from dagster_test.toys.partitioned_assets import failing_partitions


def test_assets():
    Definitions(assets=load_assets_from_modules([failing_partitions]))

import os
from typing import List

import pytest
from dagster import (
    DagsterInstance,
    _check as check,
    materialize,
)
from dagster._core.definitions.assets import AssetsDefinition

from dbt_example_tests.integration_tests.conftest import makefile_dir


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture() -> list[str]:
    return ["make", "run_complete", "-C", str(makefile_dir())]


def test_dagster_materializes(
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Trigger materializations on the live dagster instance and ensure they succeed."""
    from dbt_example.dagster_defs.complete import defs

    assert defs.assets
    assets_list = check.list_param(defs.assets, "defs.assets", of_type=AssetsDefinition)
    instance = DagsterInstance.get()
    result = materialize(assets_list, instance=instance, resources=defs.resources)
    assert result.success
    for asset in assets_list:
        for spec in asset.specs:
            assert instance.get_latest_materialization_event(asset_key=spec.key)

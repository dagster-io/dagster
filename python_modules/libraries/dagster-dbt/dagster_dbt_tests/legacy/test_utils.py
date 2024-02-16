from typing import List

import pytest
from dagster import AssetKey
from dagster_dbt.core.utils import _create_command_list
from dagster_dbt.types import DbtOutput
from dagster_dbt.utils import generate_materializations

from .sample_results import (
    DBT_18_RUN_RESULTS_SAMPLE,
    DBT_CLI_V1_RUN_RESULTS_SAMPLE,
)


@pytest.mark.parametrize(
    argnames=["debug", "prefix"],
    argvalues=[
        (True, ["dbt", "--debug"]),
        (False, ["dbt"]),
    ],
    ids=["debug", "no-debug"],
)
def test_create_command_list_debug(debug: bool, prefix: List[str]):
    command_list = _create_command_list(
        executable="dbt",
        warn_error=False,
        json_log_format=False,
        command="run",
        flags_dict={},
        debug=debug,
    )
    assert command_list == prefix + ["run"]


@pytest.mark.parametrize("sample", [DBT_18_RUN_RESULTS_SAMPLE, DBT_CLI_V1_RUN_RESULTS_SAMPLE])
def test_generate_materializations(sample):
    out = DbtOutput(result=sample)
    materializations = [mat for mat in generate_materializations(out)]

    assert len(materializations) == 3

    mat_names = {mat.asset_key for mat in materializations}

    assert mat_names == {AssetKey(["model", "my_schema", f"table_{i}"]) for i in range(1, 4)}

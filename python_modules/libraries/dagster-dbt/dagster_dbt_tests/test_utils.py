import pytest
from dagster import AssetKey
from dagster_dbt.types import DbtOutput
from dagster_dbt.utils import generate_materializations

from .sample_results import (
    DBT_18_RUN_RESULTS_SAMPLE,
    DBT_CLI_V1_RUN_RESULTS_SAMPLE,
    DBT_RPC_RESPONSE_SAMPLE,
)


@pytest.mark.parametrize(
    "sample", [DBT_18_RUN_RESULTS_SAMPLE, DBT_CLI_V1_RUN_RESULTS_SAMPLE, DBT_RPC_RESPONSE_SAMPLE]
)
def test_generate_materializations(sample):
    out = DbtOutput(result=sample)
    materializations = [mat for mat in generate_materializations(out)]

    assert len(materializations) == 3

    mat_names = {mat.asset_key for mat in materializations}

    assert mat_names == {AssetKey(["model", "my_schema", f"table_{i}"]) for i in range(1, 4)}

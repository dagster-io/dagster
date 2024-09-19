import pytest
import responses
from dagster_dbt.cloud.cli import DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR, app
from typer.testing import CliRunner

from dagster_dbt_tests.cloud.utils import (
    DBT_CLOUD_ACCOUNT_ID,
    DBT_CLOUD_EMEA_HOST,
    DBT_CLOUD_US_HOST,
    SAMPLE_API_PREFIX,
    SAMPLE_API_V3_PREFIX,
    SAMPLE_EMEA_API_PREFIX,
    SAMPLE_EMEA_API_V3_PREFIX,
    SAMPLE_JOB_ID,
    SAMPLE_PROJECT_ID,
    sample_get_environment_variables,
    sample_list_job_details,
    sample_run_details,
    sample_set_environment_variable,
)

runner = CliRunner()


@pytest.mark.parametrize(
    ["host", "api_prefix", "api_v3_prefix"],
    [
        (DBT_CLOUD_US_HOST, SAMPLE_API_PREFIX, SAMPLE_API_V3_PREFIX),
        (DBT_CLOUD_EMEA_HOST, SAMPLE_EMEA_API_PREFIX, SAMPLE_EMEA_API_V3_PREFIX),
    ],
)
@responses.activate(assert_all_requests_are_fired=True)
def test_cache_compile_references(
    monkeypatch: pytest.MonkeyPatch, host: str, api_prefix: str, api_v3_prefix: str
) -> None:
    monkeypatch.setenv("DBT_CLOUD_API_KEY", "test")
    monkeypatch.setenv("DBT_CLOUD_ACCOUNT_ID", str(DBT_CLOUD_ACCOUNT_ID))
    monkeypatch.setenv("DBT_CLOUD_PROJECT_ID", str(SAMPLE_PROJECT_ID))
    monkeypatch.setenv("DBT_CLOUD_HOST", str(host))
    compile_run_environment_variable_id = 3

    responses.get(f"{api_prefix}/jobs", json=sample_list_job_details())
    responses.post(f"{api_prefix}/jobs/{SAMPLE_JOB_ID}/run/", json=sample_run_details())
    responses.get(
        f"{api_v3_prefix}/projects/{SAMPLE_PROJECT_ID}/environment-variables/job",
        json=sample_get_environment_variables(
            environment_variable_id=compile_run_environment_variable_id,
            name=DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR,
            value="-1",
        ),
    )
    responses.post(
        f"{api_v3_prefix}/projects/{SAMPLE_PROJECT_ID}/environment-variables/{compile_run_environment_variable_id}",
        json=sample_set_environment_variable(
            environment_variable_id=compile_run_environment_variable_id,
            name=DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR,
            value="500000",
        ),
    )

    result = runner.invoke(app, ["cache-compile-references"])

    assert result.exit_code == 0


@responses.activate(assert_all_requests_are_fired=True)
def test_skip_cache_compile_references(monkeypatch):
    monkeypatch.setenv("DBT_CLOUD_API_KEY", "test")
    monkeypatch.setenv("DBT_CLOUD_ACCOUNT_ID", DBT_CLOUD_ACCOUNT_ID)
    monkeypatch.setenv("DBT_CLOUD_PROJECT_ID", SAMPLE_PROJECT_ID)

    responses.get(f"{SAMPLE_API_PREFIX}/jobs", json=sample_list_job_details())
    responses.get(
        f"{SAMPLE_API_V3_PREFIX}/projects/{SAMPLE_PROJECT_ID}/environment-variables/job",
        json=sample_get_environment_variables(
            environment_variable_id=1,
            name="DBT_DAGSTER_NOT_THE_COMPILE_RUN_ID",
            value="-1",
        ),
    )

    result = runner.invoke(app, ["cache-compile-references"])

    assert result.exit_code == 0

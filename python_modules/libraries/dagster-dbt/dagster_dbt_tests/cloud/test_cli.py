import responses
from dagster_dbt.cloud.cli import DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR, app
from typer.testing import CliRunner

from .utils import (
    SAMPLE_ACCOUNT_ID,
    SAMPLE_API_PREFIX,
    SAMPLE_API_V3_PREFIX,
    SAMPLE_JOB_ID,
    SAMPLE_PROJECT_ID,
    sample_get_environment_variables,
    sample_list_job_details,
    sample_run_details,
    sample_set_environment_variable,
)

runner = CliRunner()


@responses.activate
def test_cache_compile_references(monkeypatch):
    monkeypatch.setenv("DBT_CLOUD_API_KEY", "test")
    monkeypatch.setenv("DBT_CLOUD_ACCOUNT_ID", SAMPLE_ACCOUNT_ID)
    monkeypatch.setenv("DBT_CLOUD_PROJECT_ID", SAMPLE_PROJECT_ID)
    compile_run_environment_variable_id = 3

    responses.get(f"{SAMPLE_API_PREFIX}/jobs", json=sample_list_job_details())
    responses.post(f"{SAMPLE_API_PREFIX}/jobs/{SAMPLE_JOB_ID}/run/", json=sample_run_details())
    responses.get(
        f"{SAMPLE_API_V3_PREFIX}/projects/{SAMPLE_PROJECT_ID}/environment-variables/job",
        json=sample_get_environment_variables(
            environment_variable_id=compile_run_environment_variable_id,
            name=DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR,
        ),
    )
    responses.post(
        f"{SAMPLE_API_V3_PREFIX}/projects/{SAMPLE_PROJECT_ID}/environment-variables/{compile_run_environment_variable_id}",
        json=sample_set_environment_variable(
            environment_variable_id=compile_run_environment_variable_id,
            name=DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR,
            value="500000",
        ),
    )

    result = runner.invoke(app, ["cache-compile-references"])

    assert result.exit_code == 0

from typing import List

import typer

from dagster_dbt.cloud.asset_defs import (
    DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR,
    DbtCloudCacheableAssetsDefinition,
)
from dagster_dbt.cloud.resources import DbtCloudResource

app = typer.Typer()


@app.command()
def cache_compile_references(
    auth_token: str = typer.Argument(..., envvar="DBT_CLOUD_API_KEY"),
    account_id: int = typer.Argument(..., envvar="DBT_CLOUD_ACCOUNT_ID"),
    project_id: int = typer.Argument(..., envvar="DBT_CLOUD_PROJECT_ID"),
) -> None:
    """
    Cache the latest dbt cloud compile run id for a given project.
    """
    dbt_cloud_resource = DbtCloudResource(
        auth_token=auth_token, account_id=account_id, disable_schedule_on_trigger=False
    )

    # List the jobs from the project
    dbt_cloud_jobs = dbt_cloud_resource.list_jobs(project_id=project_id)

    # Compile each job with an override
    for dbt_cloud_job in dbt_cloud_jobs:
        job_id: int = dbt_cloud_job["id"]
        job_commands: List[str] = dbt_cloud_job["execute_steps"]

        # Retrieve the filters for the compile override step
        job_materialization_command_step = (
            DbtCloudCacheableAssetsDefinition.get_job_materialization_command_step(
                execute_steps=job_commands
            )
        )
        dbt_materialization_command = job_commands[job_materialization_command_step]
        parsed_args = DbtCloudCacheableAssetsDefinition.parse_dbt_command(
            dbt_materialization_command
        )
        dbt_compile_options: List[str] = DbtCloudCacheableAssetsDefinition.get_compile_filters(
            parsed_args=parsed_args
        )
        dbt_compile_command = f"dbt compile {' '.join(dbt_compile_options)}"

        # Run the compile command
        dbt_cloud_compile_run = dbt_cloud_resource.run_job(
            job_id=job_id,
            cause="Generating software-defined assets for Dagster.",
            steps_override=[dbt_compile_command],
            generate_docs_override=True,
        )

        # Cache the compile run as a reference in the dbt Cloud job's env var
        dbt_cloud_compile_run_id = str(dbt_cloud_compile_run["id"])
        dbt_cloud_job_env_vars = dbt_cloud_resource.get_job_environment_variables(
            project_id=project_id, job_id=job_id
        )
        compile_run_environment_variable_id = dbt_cloud_job_env_vars[
            DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR
        ]["job"]["id"]

        typer.echo(
            f"Updating the value of environment variable `{DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR}`"
            f" with id `{compile_run_environment_variable_id}` for job id `{job_id}`. Setting new"
            f" value to `{dbt_cloud_compile_run_id}`."
        )

        dbt_cloud_resource.set_job_environment_variable(
            project_id=project_id,
            job_id=job_id,
            environment_variable_id=compile_run_environment_variable_id,
            name=DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR,
            value=dbt_cloud_compile_run_id,
        )

        typer.echo("Update complete.")


# https://typer.tiangolo.com/tutorial/commands/one-or-multiple/#one-command-and-one-callback
@app.callback()
def callback() -> None:
    pass


if __name__ == "__main__":
    app()

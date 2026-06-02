"""Run API commands following GitHub CLI patterns."""

import json
import time
from typing import Final

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_rest_resources.schemas.enums import DgApiRunStatus
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import (
    format_compute_log_links,
    format_compute_logs,
    format_logs_json,
    format_logs_table,
    format_run,
    format_run_launch_result,
    format_runs_list,
)
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema

DG_API_MAX_RUN_LIMIT: Final = 1000
TERMINAL_RUN_STATUSES: Final = frozenset(
    {DgApiRunStatus.SUCCESS, DgApiRunStatus.FAILURE, DgApiRunStatus.CANCELED}
)


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--limit",
    type=click.IntRange(1, DG_API_MAX_RUN_LIMIT),
    default=50,
    help=f"Number of runs to return (default: 50, max: {DG_API_MAX_RUN_LIMIT})",
)
@click.option(
    "--cursor",
    type=str,
    help="Cursor for pagination (run ID)",
)
@click.option(
    "--status",
    "statuses",
    multiple=True,
    type=click.Choice([e.value for e in DgApiRunStatus], case_sensitive=False),
    callback=lambda ctx, param, values: tuple(DgApiRunStatus(v.upper()) for v in values),
    help="Filter by run status. Repeatable.",
)
@click.option(
    "--job",
    "job_name",
    type=str,
    help="Filter by job name",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.run", cls="DgApiRunList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_runs_command(
    ctx: click.Context,
    limit: int,
    cursor: str,
    statuses: tuple[DgApiRunStatus, ...],
    job_name: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List runs with optional filtering and pagination.

    Example::

        $ dg api run list --limit 3
        ID                                    STATUS    JOB                CREATED
        5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a  SUCCESS   ingest_customers   2026-05-06 18:00:12 UTC
        2a1f7b3c-9d8e-4c5b-8a6d-3f1e2b9c4d7a  SUCCESS   ingest_customers   2026-05-05 18:00:08 UTC
        8c4d2e7f-1a9b-4e3d-7c5b-9f2a1d8e3b6c  FAILURE   ingest_customers   2026-05-04 18:00:15 UTC
    """
    from dagster_rest_resources.api.run import DgApiRunApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunApi(client)

    with handle_api_errors(ctx, output_json):
        runs = api.list_runs(
            limit=limit,
            cursor=cursor,
            statuses=list(statuses) if statuses else None,
            job_name=job_name,
        )
        output = format_runs_list(runs, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("run_id", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.run", cls="DgApiRun")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_run_command(
    ctx: click.Context,
    run_id: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get run metadata by ID.

    Example::

        $ dg api run get 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        Run ID:   5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        Status:   SUCCESS
        Created:  2026-05-06 18:00:12 UTC
        Started:  2026-05-06 18:00:14 UTC
        Ended:    2026-05-06 18:04:42 UTC
        Pipeline: ingest_customers
    """
    from dagster_rest_resources.api.run import DgApiRunApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunApi(client)

    with handle_api_errors(ctx, output_json):
        run = api.get_run(run_id)
        output = format_run(run, as_json=output_json)
        click.echo(output)


@click.command(name="get-events", cls=DgClickCommand)
@click.argument("run_id", type=str)
@click.option(
    "--level",
    "levels",
    multiple=True,
    help="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Repeatable.",
)
@click.option(
    "--event-type",
    "event_types",
    multiple=True,
    help="Filter by event type (e.g. STEP_FAILURE, RUN_START). Repeatable.",
)
@click.option(
    "--step",
    "step_keys",
    multiple=True,
    help="Filter by step key (partial matching). Repeatable.",
)
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Maximum number of log entries to return",
)
@click.option(
    "--cursor",
    "after_cursor",
    help="Pagination cursor for retrieving more logs",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.run_event", cls="DgApiRunEventList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_events_run_command(
    ctx: click.Context,
    run_id: str,
    levels: tuple[str, ...],
    event_types: tuple[str, ...],
    step_keys: tuple[str, ...],
    limit: int,
    after_cursor: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get execution log events for a specific run ID.

    Example::

        $ dg api run get-events 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a --limit 4
        Logs for run 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a:

        TIMESTAMP            LEVEL    STEP_KEY                  MESSAGE
        --------------------------------------------------------------------------------
        2026-05-06 18:00:14  INFO                               Started execution of run for "ingest_customers".
        2026-05-06 18:00:14  INFO     ingest_files              Started execution of step "ingest_files".
        2026-05-06 18:04:40  INFO     ingest_files              Finished execution of step "ingest_files" in 4m26s.
        2026-05-06 18:04:42  INFO                               Finished execution of run for "ingest_customers".

        Total log entries: 4
    """
    from dagster_rest_resources.api.run_event import DgApiRunEventApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunEventApi(client)

    with handle_api_errors(ctx, output_json):
        logs = api.get_events(
            run_id=run_id,
            event_types=event_types,
            step_keys=step_keys,
            levels=levels,
            limit=limit,
            after_cursor=after_cursor,
        )

        if output_json:
            output = format_logs_json(logs)
        else:
            output = format_logs_table(logs, run_id)

        click.echo(output)


@click.command(name="get-logs", cls=DgClickCommand)
@click.argument("run_id", type=str)
@click.option(
    "--step-key",
    type=str,
    help="Filter to a specific step",
)
@click.option(
    "--link-only",
    is_flag=True,
    help="Return download URLs instead of log content",
)
@click.option(
    "--max-bytes",
    type=int,
    default=None,
    help="Maximum bytes of log content per step",
)
@click.option(
    "--cursor",
    "cursor",
    type=str,
    help="Cursor for paginating log content",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.compute_log", cls="DgApiComputeLogList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_logs_command(
    ctx: click.Context,
    run_id: str,
    step_key: str | None,
    link_only: bool,
    max_bytes: int | None,
    cursor: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get stdout/stderr compute logs for a specific run.

    Example::

        $ dg api run get-logs 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a --step-key ingest_files
        Compute logs for run 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a:

        --- ingest_files [ingest_files] ---
        STDOUT:
        Loading 1,432 rows into raw_customers
        Done.
        STDERR:
        (no errors)

        Total steps with logs: 1
    """
    from dagster_rest_resources.api.compute_log import DgApiComputeLogApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiComputeLogApi(client)

    with handle_api_errors(ctx, output_json):
        if link_only:
            links = api.get_log_links(run_id=run_id, step_key=step_key)
            output = format_compute_log_links(links, as_json=output_json)
        else:
            logs = api.get_logs(
                run_id=run_id, step_key=step_key, cursor=cursor, max_bytes=max_bytes
            )
            output = format_compute_logs(logs, as_json=output_json)

        click.echo(output)


@click.command(name="launch", cls=DgClickCommand)
@click.option("--location", "-l", required=True, help="Code location name")
@click.option(
    "--repository",
    "-r",
    default="__repository__",
    show_default=True,
    help="Repository name in the code location",
)
@click.option(
    "--job",
    "-j",
    "job_name",
    default=None,
    help="Name of the job to launch",
)
@click.option(
    "--asset-key",
    "asset_keys",
    multiple=True,
    help=(
        "Asset key to materialize. Use slash-separated syntax for prefixed keys "
        "(e.g. 'my_prefix/my_asset'). Repeatable."
    ),
)
@click.option(
    "--partition",
    default=None,
    help="Partition key. Partition ranges are not yet supported.",
)
@click.option(
    "--tag",
    "tag_options",
    multiple=True,
    help="Tag to attach to the run as 'key=value'. Repeatable.",
)
@click.option(
    "--config-json",
    default=None,
    help="JSON string of run config to use for this run",
)
@click.option(
    "--wait",
    "-w",
    is_flag=True,
    help="Wait for the run to reach a terminal status before returning.",
)
@click.option(
    "--interval",
    "-i",
    default=30,
    show_default=True,
    type=click.IntRange(1, 3600),
    help="Polling interval in seconds when --wait is set.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.run", cls="DgApiRunLaunchResult")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def launch_run_command(
    ctx: click.Context,
    location: str,
    repository: str,
    job_name: str | None,
    asset_keys: tuple[str, ...],
    partition: str | None,
    tag_options: tuple[str, ...],
    config_json: str | None,
    wait: bool,
    interval: int,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    r"""Launch a run on a Dagster Plus deployment.

    Use this to materialize assets or launch jobs against a deployed Dagster Plus
    environment. For local in-process execution during development, use ``dg launch``.

    Example::

        $ dg api run launch --location my_location --job ingest_customers
        Run ID: 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        Status: STARTED

        $ dg api run launch --location my_location \
            --asset-key raw_customers --asset-key marts/dim_customers --wait
    """
    from dagster_rest_resources.api.run import DgApiRunApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunApi(client)

    with handle_api_errors(ctx, output_json):
        if not job_name and not asset_keys:
            raise click.UsageError("At least one of --job or --asset-key must be provided.")
        if partition and "..." in partition:
            raise click.UsageError(
                "Partition ranges are not supported by `dg api run launch`. "
                "Use a single partition key."
            )

        tags: dict[str, str] = {}
        for raw in tag_options:
            if "=" not in raw:
                raise click.UsageError(f"Invalid --tag value `{raw}`. Expected `key=value`.")
            key, value = raw.split("=", 1)
            tags[key] = value

        run_config = None
        if config_json:
            try:
                run_config = json.loads(config_json)
            except json.JSONDecodeError as e:
                raise click.UsageError(f"--config-json is not valid JSON: {e}")

        result = api.create_run(
            location_name=location,
            repository_name=repository,
            job_name=job_name,
            asset_keys=list(asset_keys) if asset_keys else None,
            tags=tags or None,
            run_config=run_config,
            partition=partition,
        )

        if wait:
            while result.status not in TERMINAL_RUN_STATUSES:
                time.sleep(interval)
                latest = api.get_run(result.run_id)
                result = result.model_copy(update={"status": latest.status})

        output = format_run_launch_result(result, as_json=output_json)
        click.echo(output)

        if wait and result.status != DgApiRunStatus.SUCCESS:
            raise click.ClickException(
                f"Run {result.run_id} finished with status {result.status.value}"
            )


@click.group(
    name="run",
    cls=DgClickGroup,
    commands={
        "list": list_runs_command,
        "get": get_run_command,
        "get-events": get_events_run_command,
        "get-logs": get_logs_command,
        "launch": launch_run_command,
    },
)
def run_group():
    """Manage runs in Dagster Plus."""

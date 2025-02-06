from typing import Optional

import click

import dagster._check as check
from dagster._cli.job import get_run_config_from_cli_opts
from dagster._cli.utils import (
    assert_no_remaining_opts,
    get_instance_for_cli,
    get_possibly_temporary_instance_for_cli,
)
from dagster._cli.workspace.cli_target import (
    PythonPointerOpts,
    get_repository_python_origin_from_cli_opts,
    python_pointer_options,
    run_config_option,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.backfill_policy import BackfillPolicyType
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterInvalidSubsetError, DagsterUnknownPartitionError
from dagster._core.execution.api import execute_job
from dagster._core.instance import DagsterInstance
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.telemetry import telemetry_wrapper
from dagster._utils.hosted_user_process import recon_job_from_origin, recon_repository_from_origin
from dagster._utils.interrupts import capture_interrupts


@click.group(name="asset")
def asset_cli():
    """Commands for working with Dagster assets."""


@asset_cli.command(name="materialize", help="Execute a run to materialize a selection of assets")
@click.option("--select", help="Comma-separated Asset selection to target", required=True)
@click.option("--partition", help="Asset partition to target", required=False)
@click.option(
    "--partition-range",
    help="Asset partition range to target i.e. <start>...<end>",
    required=False,
)
@click.option(
    "--config-json",
    type=click.STRING,
    help="JSON string of run config to use for this job run. Cannot be used with -c / --config.",
)
@run_config_option(name="config", command_name="materialize")
@python_pointer_options
def asset_materialize_command(
    select: str,
    partition: Optional[str],
    partition_range: Optional[str],
    config: tuple[str, ...],
    config_json: Optional[str],
    **other_opts: object,
) -> None:
    python_pointer_opts = PythonPointerOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    with capture_interrupts():
        with get_possibly_temporary_instance_for_cli(
            "``dagster asset materialize``",
        ) as instance:
            execute_materialize_command(
                instance=instance,
                select=select,
                partition=partition,
                partition_range=partition_range,
                config=config,
                config_json=config_json,
                python_pointer_opts=python_pointer_opts,
            )


@telemetry_wrapper
def execute_materialize_command(
    *,
    instance: DagsterInstance,
    select: str,
    partition: Optional[str],
    partition_range: Optional[str],
    config: tuple[str, ...],
    config_json: Optional[str],
    python_pointer_opts: PythonPointerOpts,
) -> None:
    run_config = get_run_config_from_cli_opts(config, config_json)
    repository_origin = get_repository_python_origin_from_cli_opts(python_pointer_opts)

    recon_repo = recon_repository_from_origin(repository_origin)
    repo_def = recon_repo.get_definition()

    asset_selection = AssetSelection.from_coercible(select.split(","))
    asset_keys = asset_selection.resolve(repo_def.asset_graph)

    implicit_job_def = repo_def.get_implicit_job_def_for_assets(asset_keys)
    # If we can't find an implicit job with all the given assets, it's because they couldn't be
    # placed into the same implicit job, because of their conflicting PartitionsDefinitions.
    if implicit_job_def is None:
        raise DagsterInvalidSubsetError(
            "All selected assets must share the same PartitionsDefinition or have no"
            " PartitionsDefinition"
        )

    reconstructable_job = recon_job_from_origin(
        JobPythonOrigin(implicit_job_def.name, repository_origin=repository_origin)
    )

    if partition and partition_range:
        check.failed("Cannot specify both --partition and --partition-range options. Use only one.")

    if partition:
        if all(
            implicit_job_def.asset_layer.get(asset_key).partitions_def is None
            for asset_key in asset_keys
        ):
            check.failed("Provided '--partition' option, but none of the assets are partitioned")

        try:
            implicit_job_def.validate_partition_key(
                partition, selected_asset_keys=asset_keys, dynamic_partitions_store=instance
            )
            tags = implicit_job_def.get_tags_for_partition_key(
                partition, selected_asset_keys=asset_keys
            )
        except DagsterUnknownPartitionError:
            raise DagsterInvalidSubsetError(
                "All selected assets must have a PartitionsDefinition containing the passed"
                f" partition key `{partition}` or have no PartitionsDefinition."
            )
    elif partition_range:
        if len(partition_range.split("...")) != 2:
            check.failed("Invalid partition range format. Expected <start>...<end>.")

        partition_range_start, partition_range_end = partition_range.split("...")

        for asset_key in asset_keys:
            backfill_policy = implicit_job_def.asset_layer.get(asset_key).backfill_policy
            if (
                backfill_policy is not None
                and backfill_policy.policy_type != BackfillPolicyType.SINGLE_RUN
            ):
                check.failed(
                    "Provided partition range, but not all assets have a single-run backfill policy."
                )
        try:
            implicit_job_def.validate_partition_key(
                partition_range_start,
                selected_asset_keys=asset_keys,
                dynamic_partitions_store=instance,
            )
            implicit_job_def.validate_partition_key(
                check.not_none(partition_range_end),
                selected_asset_keys=asset_keys,
                dynamic_partitions_store=instance,
            )
        except DagsterUnknownPartitionError:
            raise DagsterInvalidSubsetError(
                "All selected assets must have a PartitionsDefinition containing the passed"
                f" partition key `{partition_range_start}` or have no PartitionsDefinition."
            )
        tags = {
            ASSET_PARTITION_RANGE_START_TAG: partition_range_start,
            ASSET_PARTITION_RANGE_END_TAG: partition_range_end,
        }
    else:
        if any(
            implicit_job_def.asset_layer.get(asset_key).partitions_def is not None
            for asset_key in asset_keys
        ):
            check.failed("Asset has partitions, but no '--partition' option was provided")
        tags = {}

    result = execute_job(
        job=reconstructable_job,
        asset_selection=list(asset_keys),
        instance=instance,
        tags=tags,
        run_config=run_config,
    )
    if not result.success:
        raise click.ClickException("Materialization failed.")


@asset_cli.command(name="list", help="List assets")
@click.option("--select", help="Asset selection to target", required=False)
@python_pointer_options
def asset_list_command(select: Optional[str], **other_opts):
    python_pointer_opts = PythonPointerOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    repository_origin = get_repository_python_origin_from_cli_opts(python_pointer_opts)
    recon_repo = recon_repository_from_origin(repository_origin)
    repo_def = recon_repo.get_definition()

    if select is not None:
        asset_selection = AssetSelection.from_coercible(select.split(","))
    else:
        asset_selection = AssetSelection.all()

    asset_keys = asset_selection.resolve(repo_def.asset_graph, allow_missing=True)

    for asset_key in sorted(asset_keys):
        print(asset_key.to_user_string())  # noqa: T201


@asset_cli.command(name="wipe")
@click.argument("key", nargs=-1)
@click.option("--all", is_flag=True, help="Eliminate all asset key indexes")
@click.option("--noprompt", is_flag=True)
def asset_wipe_command(key, **cli_args):
    r"""Eliminate asset key indexes from event logs.

    Warning: Cannot be undone.

    \b
    Usage:
      dagster asset wipe --all
      dagster asset wipe <unstructured_asset_key_name>
      dagster asset wipe <json_string_of_structured_asset_key>
    """
    if not cli_args.get("all") and len(key) == 0:
        raise click.UsageError(
            "Error, you must specify an asset key or use `--all` to wipe all asset keys."
        )

    if cli_args.get("all") and len(key) > 0:
        raise click.UsageError("Error, cannot use more than one of: asset key, `--all`.")

    noprompt = cli_args.get("noprompt")

    with get_instance_for_cli() as instance:
        if len(key) > 0:
            asset_keys = [AssetKey.from_db_string(key_string) for key_string in key]
            prompt = (
                "Are you sure you want to remove the asset key indexes for these keys from the"
                " event logs? Type DELETE"
            )
        else:
            asset_keys = instance.all_asset_keys()
            prompt = (
                "Are you sure you want to remove all asset key indexes from the event logs? Type"
                " DELETE"
            )

        if noprompt:
            confirmation = "DELETE"
        else:
            confirmation = click.prompt(prompt)

        if confirmation == "DELETE":
            instance.wipe_assets(asset_keys)  # pyright: ignore[reportArgumentType]
            click.echo("Removed asset indexes from event logs")
        else:
            click.echo("Exiting without removing asset indexes")


@asset_cli.command(name="wipe-partitions-status-cache")
@click.argument("key", nargs=-1)
@click.option("--all", is_flag=True, help="Wipe partitions status cache of all asset keys")
@click.option("--noprompt", is_flag=True)
def asset_wipe_cache_command(key, **cli_args):
    r"""Clears the asset partitions status cache, which is used by the webserver to load partition
    pages more quickly. The cache will be rebuilt the next time the partition pages are loaded,
    if caching is enabled.

    \b
    Usage:
      dagster asset wipe-cache --all
      dagster asset wipe-cache <unstructured_asset_key_name>
      dagster asset wipe-cache <json_string_of_structured_asset_key>
    """
    if not cli_args.get("all") and len(key) == 0:
        raise click.UsageError(
            "Error, you must specify an asset key or use `--all` to clear the partitions status"
            " cache of all asset keys."
        )

    if cli_args.get("all") and len(key) > 0:
        raise click.UsageError("Error, cannot use more than one of: asset key, `--all`.")

    noprompt = cli_args.get("noprompt")

    with get_instance_for_cli() as instance:
        if instance.can_read_asset_status_cache() is False:
            raise click.UsageError(
                "Error, the instance does not support caching asset status. Wiping the cache is not"
                " supported."
            )

        if len(key) > 0:
            asset_keys = [AssetKey.from_db_string(key_string) for key_string in key]
            prompt = (
                "Are you sure you want to wipe the partitions status cache for these"
                f" keys {asset_keys} from the event logs? Type DELETE"
            )
        else:
            asset_keys = instance.all_asset_keys()
            prompt = (
                "Are you sure you want to wipe the partitions status cache for all asset keys?"
                " Type DELETE"
            )

        if noprompt:
            confirmation = "DELETE"
        else:
            confirmation = click.prompt(prompt)

        if confirmation == "DELETE":
            instance.wipe_asset_cached_status(asset_keys)  # pyright: ignore[reportArgumentType]
            click.echo("Cleared the partitions status cache")
        else:
            click.echo("Exiting without wiping the partitions status cache")

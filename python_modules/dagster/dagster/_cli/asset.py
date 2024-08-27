from typing import Mapping

import click
from rich import print
from rich.progress import Progress

import dagster._check as check
from dagster._cli.utils import get_instance_for_cli, get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import (
    get_repository_python_origin_from_kwargs,
    python_origin_target_argument,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.errors import DagsterInvalidSubsetError, DagsterUnknownPartitionError
from dagster._core.execution.api import execute_job
from dagster._core.execution.context.input import build_input_context
from dagster._core.instance import DagsterInstance
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.upath_io_manager import UPathIOManager
from dagster._core.telemetry import telemetry_wrapper
from dagster._utils.hosted_user_process import recon_job_from_origin, recon_repository_from_origin
from dagster._utils.interrupts import capture_interrupts


@click.group(name="asset")
def asset_cli():
    """Commands for working with Dagster assets."""


@asset_cli.command(name="materialize", help="Execute a run to materialize a selection of assets")
@python_origin_target_argument
@click.option("--select", help="Asset selection to target", required=True)
@click.option("--partition", help="Asset partition to target", required=False)
def asset_materialize_command(**kwargs):
    with capture_interrupts():
        with get_possibly_temporary_instance_for_cli(
            "``dagster asset materialize``",
        ) as instance:
            execute_materialize_command(instance, kwargs)


@telemetry_wrapper
def execute_materialize_command(instance: DagsterInstance, kwargs: Mapping[str, str]) -> None:
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)

    recon_repo = recon_repository_from_origin(repository_origin)
    repo_def = recon_repo.get_definition()

    asset_selection = AssetSelection.from_coercible(kwargs["select"].split(","))
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
    partition = kwargs.get("partition")
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

    else:
        if any(
            implicit_job_def.asset_layer.get(asset_key).partitions_def is not None
            for asset_key in asset_keys
        ):
            check.failed("Asset has partitions, but no '--partition' option was provided")
        tags = {}

    result = execute_job(
        job=reconstructable_job, asset_selection=list(asset_keys), instance=instance, tags=tags
    )
    if not result.success:
        raise click.ClickException("Materialization failed.")


@asset_cli.command(name="list", help="List assets")
@python_origin_target_argument
@click.option("--select", help="Asset selection to target", required=False)
def asset_list_command(**kwargs):
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)
    recon_repo = recon_repository_from_origin(repository_origin)
    repo_def = recon_repo.get_definition()

    select = kwargs.get("select")
    if select is not None:
        asset_selection = AssetSelection.from_coercible(kwargs["select"].split(","))
    else:
        asset_selection = AssetSelection.all()

    asset_keys = asset_selection.resolve(repo_def.asset_graph, allow_missing=True)

    for asset_key in sorted(asset_keys):
        print(asset_key.to_user_string())


@asset_cli.command(name="scan", help="Scan asset materialization")
@python_origin_target_argument
@click.option("--select", help="Asset selection to target", required=True)
@click.option("--verbose", help="Print all partitions' status", default=False)
def asset_materialization_scan_command(**kwargs):
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)
    recon_repo = recon_repository_from_origin(repository_origin)
    repo_def = recon_repo.get_definition()

    select = kwargs.get("select")
    asset = repo_def.assets_defs_by_key.get(AssetKey(select), None)
    with get_instance_for_cli() as instance:
        with Progress() as progress_bar:
            asset_name = asset.key.to_user_string()

            # check if it's a partitioned or non partitioned asset
            if asset.partitions_def is None:
                partitions = [None]
            else:
                # get the list of partitions
                all_partitions = set(asset.partitions_def.get_partition_keys())
                materialized_partitions = set(
                    instance.get_materialized_partitions(asset_key=asset.key)
                )
                # only scan not materialized partitions
                partitions = list(all_partitions - materialized_partitions)

            task_scanning_asset = progress_bar.add_task(
                description=asset_name, total=len(partitions)
            )
            for partition in partitions:
                # pretty the progress bar for partitions
                if partition is not None:
                    progress_bar.update(
                        task_scanning_asset, description=f"{asset_name}:{partition}"
                    )

                with build_input_context(
                    asset_key=asset.key,
                    resources=asset.resource_defs,
                    instance=instance,
                    partition_key=partition,
                    op_def=asset.op,
                    asset_partitions_def=asset.partitions_def,
                ) as asset_context:
                    is_materialized = []
                    for out in asset.op.output_defs:
                        io_manager = asset_context.resources.__getattribute__(out.io_manager_key)

                        if isinstance(io_manager, UPathIOManager):
                            if partition is None:
                                has_output = io_manager.has_output(asset_context)
                            else:
                                path = io_manager._with_extension(
                                    io_manager.get_path_for_partition(
                                        asset_context,
                                        io_manager._get_path_without_extension(asset_context),
                                        asset_context.partition_key,
                                    )
                                )
                                has_output = io_manager.path_exists(path)
                        else:
                            obj = io_manager.load_input(asset_context)
                            has_output = obj is not None
                        if kwargs.get("verbose", False):
                            click.echo(
                                f'{asset_name}#{partition}:{out.name} has {"NOT" if not has_output else ""} been materialized'
                            )
                        is_materialized.append(has_output)
                if all(is_materialized):
                    instance.report_runless_asset_event(
                        AssetMaterialization(
                            asset_key=asset.key,
                            partition=partition,
                            description="Runless materialization via SCAN",
                        )
                    )

                progress_bar.update(task_scanning_asset, advance=1)


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
            instance.wipe_assets(asset_keys)
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
            instance.wipe_asset_cached_status(asset_keys)
            click.echo("Cleared the partitions status cache")
        else:
            click.echo("Exiting without wiping the partitions status cache")

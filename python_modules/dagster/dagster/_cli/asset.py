from typing import Mapping

import click

import dagster._check as check
from dagster._cli.workspace.cli_target import (
    get_repository_python_origin_from_kwargs,
    python_origin_target_argument,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.execution.api import execute_job
from dagster._core.instance import DagsterInstance
from dagster._core.origin import JobPythonOrigin
from dagster._core.selector.subset_selector import parse_asset_selection
from dagster._core.telemetry import telemetry_wrapper
from dagster._utils.hosted_user_process import (
    recon_job_from_origin,
    recon_repository_from_origin,
)
from dagster._utils.interrupts import capture_interrupts

from .utils import get_instance_for_service


@click.group(name="asset")
def asset_cli():
    """Commands for working with Dagster assets."""


@asset_cli.command(name="materialize", help="Execute a run to materialize a selection of assets")
@python_origin_target_argument
@click.option("--select", help="Asset selection to target", required=True)
@click.option("--partition", help="Asset partition to target", required=False)
def asset_materialize_command(**kwargs):
    with capture_interrupts():
        with get_instance_for_service("``dagster asset materialize``") as instance:
            execute_materialize_command(instance, kwargs)


@telemetry_wrapper
def execute_materialize_command(instance: DagsterInstance, kwargs: Mapping[str, str]) -> None:
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)

    recon_repo = recon_repository_from_origin(repository_origin)
    repo_def = recon_repo.get_definition()

    asset_keys = parse_asset_selection(
        assets_defs=list(repo_def.assets_defs_by_key.values()),
        source_assets=list(repo_def.source_assets_by_key.values()),
        asset_selection=kwargs["select"].split(","),
    )

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
        partitions_def = implicit_job_def.partitions_def
        if partitions_def is None or all(
            implicit_job_def.asset_layer.partitions_def_for_asset(asset_key) is None
            for asset_key in asset_keys
        ):
            check.failed("Provided '--partition' option, but none of the assets are partitioned")

        tags = partitions_def.get_tags_for_partition_key(partition)
    else:
        tags = {}

    execute_job(
        job=reconstructable_job, asset_selection=list(asset_keys), instance=instance, tags=tags
    )


@asset_cli.command(name="list", help="List assets")
@python_origin_target_argument
@click.option("--select", help="Asset selection to target", required=False)
def asset_list_command(**kwargs):
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)
    recon_repo = recon_repository_from_origin(repository_origin)
    repo_def = recon_repo.get_definition()

    select = kwargs.get("select")
    if select is not None:
        asset_keys = parse_asset_selection(
            assets_defs=list(repo_def.assets_defs_by_key.values()),
            source_assets=list(repo_def.source_assets_by_key.values()),
            asset_selection=select.split(","),
            raise_on_clause_has_no_matches=False,
        )
    else:
        asset_keys = [
            asset_key
            for assets_def in repo_def.assets_defs_by_key.values()
            for asset_key in assets_def.keys
        ]

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

    with DagsterInstance.get() as instance:
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
    r"""Clears the asset partitions status cache, which is used by Dagit to load partition
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

    with DagsterInstance.get() as instance:
        if instance.can_cache_asset_status_data() is False:
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

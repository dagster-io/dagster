import sys
from typing import Mapping

import click

import dagster._check as check
from dagster._cli.utils import get_instance_for_cli, get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import (
    get_code_location_from_workspace,
    get_external_job_from_external_repo,
    get_external_repository_from_code_location,
    get_repository_python_origin_from_kwargs,
    get_workspace_from_kwargs,
    python_origin_target_argument,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.backfill_policy import BackfillPolicyType, resolve_backfill_policy
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.errors import (
    DagsterBackfillFailedError,
    DagsterInvalidSubsetError,
    DagsterUnknownPartitionError,
)
from dagster._core.execution.api import execute_job
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import create_backfill_run
from dagster._core.instance import DagsterInstance
from dagster._core.origin import JobPythonOrigin
from dagster._core.remote_representation.external_data import ExternalPartitionSetExecutionParamData
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.telemetry import telemetry_wrapper
from dagster._core.utils import make_new_backfill_id
from dagster._time import get_current_timestamp
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.hosted_user_process import recon_job_from_origin, recon_repository_from_origin
from dagster._utils.interrupts import capture_interrupts


@click.group(name="asset")
def asset_cli():
    """Commands for working with Dagster assets."""


@asset_cli.command(name="materialize", help="Execute a run to materialize a selection of assets")
@python_origin_target_argument
@click.option("--select", help="Asset selection to target", required=True)
@click.option("--partition", help="Asset partition to target", required=False)
@click.option(
    "--partition-range-start", help="Start range of asset partition to target", required=False
)
@click.option(
    "--partition-range-end", help="End range of asset partition to target", required=False
)
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
    partition_range_start = kwargs.get("partition_range_start")
    partition_range_end = kwargs.get("partition_range_end")

    if partition and (partition_range_start or partition_range_end):
        check.failed("Cannot specify both --partition and --partition-range options. Use only one.")

    if partition_range_start or partition_range_end:
        if not (partition_range_start and partition_range_end):
            check.failed("Both --partition-range-start and --partition-range-end must be provided.")

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
    elif partition_range_start:
        assert partition_range_end is not None

        backfill_policy_type = resolve_backfill_policy(
            [implicit_job_def.asset_layer.get(next(iter(asset_keys))).backfill_policy]
        ).policy_type

        if any(
            resolve_backfill_policy(
                [implicit_job_def.asset_layer.get(asset_key).backfill_policy]
            ).policy_type
            != backfill_policy_type
            for asset_key in asset_keys
        ):
            check.failed(
                f"Provided partition range, but not all assets have a {backfill_policy_type} backfill policy."
            )
        try:
            implicit_job_def.validate_partition_key(
                partition_range_start,
                selected_asset_keys=asset_keys,
                dynamic_partitions_store=instance,
            )
            implicit_job_def.validate_partition_key(
                partition_range_end,
                selected_asset_keys=asset_keys,
                dynamic_partitions_store=instance,
            )
        except DagsterUnknownPartitionError:
            raise DagsterInvalidSubsetError(
                "All selected assets must have a PartitionsDefinition containing the passed"
                f" partition key `{partition_range_start}` or have no PartitionsDefinition."
            )

        if backfill_policy_type == BackfillPolicyType.SINGLE_RUN:
            tags = {
                ASSET_PARTITION_RANGE_START_TAG: partition_range_start,
                ASSET_PARTITION_RANGE_END_TAG: partition_range_end,
            }
        elif backfill_policy_type == BackfillPolicyType.MULTI_RUN:
            from dagster import __version__ as dagster_version

            with get_workspace_from_kwargs(
                instance, version=dagster_version, kwargs=kwargs
            ) as workspace:
                code_location = get_code_location_from_workspace(workspace, None)

                external_repo = get_external_repository_from_code_location(
                    code_location, repo_def.name
                )

                external_job = get_external_job_from_external_repo(
                    external_repo, implicit_job_def.name
                )

                job_partition_set = next(
                    (
                        external_partition_set
                        for external_partition_set in external_repo.get_external_partition_sets()
                        if external_partition_set.job_name == external_job.name
                    ),
                    None,
                )

                if not job_partition_set:
                    raise click.UsageError(f"Job `{external_job.name}` is not partitioned.")

                repo_handle = RepositoryHandle(
                    repository_name=external_repo.name,
                    code_location=code_location,
                )

                partition_keys = check.not_none(
                    implicit_job_def.partitions_def
                ).get_partition_keys_in_range(
                    PartitionKeyRange(start=partition_range_start, end=partition_range_end)
                )

                backfill_id = make_new_backfill_id()
                backfill_job = PartitionBackfill(
                    backfill_id=backfill_id,
                    partition_set_origin=job_partition_set.get_external_origin(),
                    status=BulkActionStatus.REQUESTED,
                    partition_names=partition_keys,
                    from_failure=False,
                    reexecution_steps=None,
                    tags={},
                    backfill_timestamp=get_current_timestamp(),
                )
                try:
                    partition_execution_data = (
                        code_location.get_external_partition_set_execution_param_data(
                            repository_handle=repo_handle,
                            partition_set_name=job_partition_set.name,
                            partition_names=partition_keys,
                            instance=instance,
                        )
                    )
                except Exception:
                    error_info = serializable_error_info_from_exc_info(sys.exc_info())
                    instance.add_backfill(
                        backfill_job.with_status(BulkActionStatus.FAILED).with_error(error_info)
                    )
                    raise DagsterBackfillFailedError(f"Backfill failed: {error_info}")

                assert isinstance(partition_execution_data, ExternalPartitionSetExecutionParamData)

                for partition_data in partition_execution_data.partition_data:
                    dagster_run = create_backfill_run(
                        instance,
                        code_location,
                        external_job,
                        job_partition_set,
                        backfill_job,
                        partition_data.name,
                        partition_data.tags,
                        partition_data.run_config,
                    )
                    if dagster_run:
                        instance.submit_run(dagster_run.run_id, workspace)

                instance.add_backfill(backfill_job.with_status(BulkActionStatus.COMPLETED))

            return
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

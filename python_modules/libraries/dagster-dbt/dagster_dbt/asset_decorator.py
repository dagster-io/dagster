from collections.abc import Mapping
from typing import Any, Callable, Optional

from dagster import (
    AssetsDefinition,
    BackfillPolicy,
    DagsterInvalidDefinitionError,
    PartitionsDefinition,
    RetryPolicy,
    TimeWindowPartitionsDefinition,
    multi_asset,
)
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    build_dbt_specs,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import DbtManifestParam, validate_manifest
from dagster_dbt.dbt_project import DbtProject


@suppress_dagster_warnings
def dbt_assets(
    *,
    manifest: DbtManifestParam,
    select: str = "fqn:*",
    exclude: Optional[str] = None,
    name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    required_resource_keys: Optional[set[str]] = None,
    project: Optional[DbtProject] = None,
    retry_policy: Optional[RetryPolicy] = None,
    pool: Optional[str] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a definition for how to compute a set of dbt resources, described by a manifest.json.
    When invoking dbt commands using :py:class:`~dagster_dbt.DbtCliResource`'s
    :py:meth:`~dagster_dbt.DbtCliResource.cli` method, Dagster events are emitted by calling
    ``yield from`` on the event stream returned by :py:meth:`~dagster_dbt.DbtCliInvocation.stream`.

    Args:
        manifest (Union[Mapping[str, Any], str, Path]): The contents of a manifest.json file
            or the path to a manifest.json file. A manifest.json contains a representation of a
            dbt project (models, tests, macros, etc). We use this representation to create
            corresponding Dagster assets.
        select (str): A dbt selection string for the models in a project that you want
            to include. Defaults to ``fqn:*``.
        exclude (Optional[str]): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".
        name (Optional[str]): The name of the op.
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the dbt assets.
        dagster_dbt_translator (Optional[DagsterDbtTranslator]): Allows customizing how to map
            dbt models, seeds, etc. to asset keys and asset metadata.
        backfill_policy (Optional[BackfillPolicy]): If a partitions_def is defined, this determines
            how to execute backfills that target multiple partitions. If a time window partition
            definition is used, this parameter defaults to a single-run policy.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the assets.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        required_resource_keys (Optional[Set[str]]): Set of required resource handles.
        project (Optional[DbtProject]): A DbtProject instance which provides a pointer to the dbt
            project location and manifest. Not required, but needed to attach code references from
            model code to Dagster assets.
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that computes the asset.
        pool (Optional[str]): A string that identifies the concurrency pool that governs the dbt
            assets' execution.

    Examples:
        Running ``dbt build`` for a dbt project:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                yield from dbt.cli(["build"], context=context).stream()

        Running dbt commands with flags:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                yield from dbt.cli(["build", "--full-refresh"], context=context).stream()

        Running dbt commands with ``--vars``:

        .. code-block:: python

            import json
            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                dbt_vars = {"key": "value"}

                yield from dbt.cli(["build", "--vars", json.dumps(dbt_vars)], context=context).stream()

        Retrieving dbt artifacts after running a dbt command:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                dbt_build_invocation = dbt.cli(["build"], context=context)

                yield from dbt_build_invocation.stream()

                run_results_json = dbt_build_invocation.get_artifact("run_results.json")

        Running multiple dbt commands for a dbt project:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                yield from dbt.cli(["run"], context=context).stream()
                yield from dbt.cli(["test"], context=context).stream()

        Accessing the dbt event stream alongside the Dagster event stream:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                dbt_cli_invocation = dbt.cli(["build"], context=context)

                # Each dbt event is structured: https://docs.getdbt.com/reference/events-logging
                for dbt_event in dbt_invocation.stream_raw_events():
                    for dagster_event in dbt_event.to_default_asset_events(
                        manifest=dbt_invocation.manifest,
                        dagster_dbt_translator=dbt_invocation.dagster_dbt_translator,
                        context=dbt_invocation.context,
                        target_path=dbt_invocation.target_path,
                    ):
                        # Manipulate `dbt_event`
                        ...

                        # Then yield the Dagster event
                        yield dagster_event

        Customizing the Dagster asset definition metadata inferred from a dbt project using :py:class:`~dagster_dbt.DagsterDbtTranslator`:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets


            class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                ...


            @dbt_assets(
                manifest=Path("target", "manifest.json"),
                dagster_dbt_translator=CustomDagsterDbtTranslator(),
            )
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                yield from dbt.cli(["build"], context=context).stream()

        Using a custom resource key for dbt:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, my_custom_dbt_resource_key: DbtCliResource):
                yield from my_custom_dbt_resource_key.cli(["build"], context=context).stream()

        Using a dynamically generated resource key for dbt using `required_resource_keys`:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            dbt_resource_key = "my_custom_dbt_resource_key"

            @dbt_assets(manifest=Path("target", "manifest.json"), required_resource_keys={my_custom_dbt_resource_key})
            def my_dbt_assets(context: AssetExecutionContext):
                dbt = getattr(context.resources, dbt_resource_key)
                yield from dbt.cli(["build"], context=context).stream()

        Invoking another Dagster :py:class:`~dagster.ResourceDefinition` alongside dbt:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets
            from dagster_slack import SlackResource


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource, slack: SlackResource):
                yield from dbt.cli(["build"], context=context).stream()

                slack_client = slack.get_client()
                slack_client.chat_postMessage(channel="#my-channel", text="dbt build succeeded!")

        Defining and accessing Dagster :py:class:`~dagster.Config` alongside dbt:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext, Config
            from dagster_dbt import DbtCliResource, dbt_assets


            class MyDbtConfig(Config):
                full_refresh: bool


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource, config: MyDbtConfig):
                dbt_build_args = ["build"]
                if config.full_refresh:
                    dbt_build_args += ["--full-refresh"]

                yield from dbt.cli(dbt_build_args, context=context).stream()

        Defining Dagster :py:class:`~dagster.PartitionDefinition` alongside dbt:


        .. code-block:: python

            import json
            from pathlib import Path

            from dagster import AssetExecutionContext, DailyPartitionDefinition
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(
                manifest=Path("target", "manifest.json"),
                partitions_def=DailyPartitionsDefinition(start_date="2023-01-01")
            )
            def partitionshop_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                time_window = context.partition_time_window

                dbt_vars = {
                    "min_date": time_window.start.isoformat(),
                    "max_date": time_window.end.isoformat()
                }
                dbt_build_args = ["build", "--vars", json.dumps(dbt_vars)]

                yield from dbt.cli(dbt_build_args, context=context).stream()

    """
    dagster_dbt_translator = validate_translator(dagster_dbt_translator or DagsterDbtTranslator())
    manifest = validate_manifest(manifest)

    specs, check_specs = build_dbt_specs(
        translator=dagster_dbt_translator,
        manifest=manifest,
        select=select,
        exclude=exclude or "",
        io_manager_key=io_manager_key,
        project=project,
    )

    if op_tags and DAGSTER_DBT_SELECT_METADATA_KEY in op_tags:
        raise DagsterInvalidDefinitionError(
            f"To specify a dbt selection, use the 'select' argument, not '{DAGSTER_DBT_SELECT_METADATA_KEY}'"
            " with op_tags"
        )

    if op_tags and DAGSTER_DBT_EXCLUDE_METADATA_KEY in op_tags:
        raise DagsterInvalidDefinitionError(
            f"To specify a dbt exclusion, use the 'exclude' argument, not '{DAGSTER_DBT_EXCLUDE_METADATA_KEY}'"
            " with op_tags"
        )

    resolved_op_tags = {
        **({DAGSTER_DBT_SELECT_METADATA_KEY: select} if select else {}),
        **({DAGSTER_DBT_EXCLUDE_METADATA_KEY: exclude} if exclude else {}),
        **(op_tags if op_tags else {}),
    }

    if (
        partitions_def
        and isinstance(partitions_def, TimeWindowPartitionsDefinition)
        and not backfill_policy
    ):
        backfill_policy = BackfillPolicy.single_run()

    return multi_asset(
        name=name,
        specs=specs,
        check_specs=check_specs,
        can_subset=True,
        required_resource_keys=required_resource_keys,
        partitions_def=partitions_def,
        op_tags=resolved_op_tags,
        backfill_policy=backfill_policy,
        retry_policy=retry_policy,
        pool=pool,
    )

from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

import dagster._check as check
from dagster import (
    AssetCheckSpec,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    Nothing,
    PartitionsDefinition,
    multi_asset,
)

from .asset_utils import (
    DAGSTER_DBT_TRANSLATOR_METADATA_KEY,
    MANIFEST_METADATA_KEY,
    default_asset_check_fn,
    default_code_version_fn,
    get_deps,
)
from .dagster_dbt_translator import DagsterDbtTranslator, DbtManifestWrapper
from .dbt_manifest import DbtManifestParam, validate_manifest
from .utils import (
    ASSET_RESOURCE_TYPES,
    get_dbt_resource_props_by_dbt_unique_id_from_manifest,
    output_name_fn,
    select_unique_ids_from_manifest,
)


def dbt_assets(
    *,
    manifest: DbtManifestParam,
    select: str = "fqn:*",
    exclude: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    dagster_dbt_translator: DagsterDbtTranslator = DagsterDbtTranslator(),
) -> Callable[..., AssetsDefinition]:
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
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the dbt assets.
        dagster_dbt_translator (Optional[DagsterDbtTranslator]): Allows customizing how to map
            dbt models, seeds, etc. to asset keys and asset metadata.

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

        Customizing the Dagster asset metadata inferred from a dbt project using :py:class:`~dagster_dbt.DagsterDbtTranslator`:

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

        Invoking another Dagster :py:class:`~dagster.ResourceDefinition` alongside dbt:

        .. code-block:: python

            from pathlib import Path

            from dagster import AssetExecutionContext
            from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
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
            from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets


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
                time_window = context.asset_partitions_time_window_for_output(
                    list(context.selected_output_names)[0]
                )

                dbt_vars = {
                    "min_date": time_window.start.isoformat(),
                    "max_date": time_window.end.isoformat()
                }
                dbt_build_args = ["build", "--vars", json.dumps(dbt_vars)]

                yield from dbt.cli(dbt_build_args, context=context).stream()

    """
    check.inst_param(
        dagster_dbt_translator,
        "dagster_dbt_translator",
        DagsterDbtTranslator,
        additional_message=(
            "Ensure that the argument is an instantiated class that subclasses"
            " DagsterDbtTranslator."
        ),
    )
    manifest = validate_manifest(manifest)

    unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude or "", manifest_json=manifest
    )
    node_info_by_dbt_unique_id = get_dbt_resource_props_by_dbt_unique_id_from_manifest(manifest)
    deps = get_deps(
        dbt_nodes=node_info_by_dbt_unique_id,
        selected_unique_ids=unique_ids,
        asset_resource_types=ASSET_RESOURCE_TYPES,
    )
    (
        non_argument_deps,
        outs,
        internal_asset_deps,
        check_specs,
    ) = get_dbt_multi_asset_args(
        dbt_nodes=node_info_by_dbt_unique_id,
        deps=deps,
        io_manager_key=io_manager_key,
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
    )

    def inner(fn) -> AssetsDefinition:
        asset_definition = multi_asset(
            outs=outs,
            internal_asset_deps=internal_asset_deps,
            deps=non_argument_deps,
            compute_kind="dbt",
            partitions_def=partitions_def,
            can_subset=True,
            op_tags={
                **({"dagster-dbt/select": select} if select else {}),
                **({"dagster-dbt/exclude": exclude} if exclude else {}),
            },
            check_specs=check_specs,
        )(fn)

        return asset_definition

    return inner


def get_dbt_multi_asset_args(
    dbt_nodes: Mapping[str, Any],
    deps: Mapping[str, FrozenSet[str]],
    io_manager_key: Optional[str],
    manifest: Mapping[str, Any],
    dagster_dbt_translator: DagsterDbtTranslator,
) -> Tuple[
    Sequence[AssetKey],
    Dict[str, AssetOut],
    Dict[str, Set[AssetKey]],
    Sequence[AssetCheckSpec],
]:
    non_argument_deps: Set[AssetKey] = set()
    outs: Dict[str, AssetOut] = {}
    internal_asset_deps: Dict[str, Set[AssetKey]] = {}
    check_specs: Sequence[AssetCheckSpec] = []

    for unique_id, parent_unique_ids in deps.items():
        dbt_resource_props = dbt_nodes[unique_id]

        output_name = output_name_fn(dbt_resource_props)
        asset_key = dagster_dbt_translator.get_asset_key(dbt_resource_props)

        outs[output_name] = AssetOut(
            key=asset_key,
            dagster_type=Nothing,
            io_manager_key=io_manager_key,
            description=dagster_dbt_translator.get_description(dbt_resource_props),
            is_required=False,
            metadata={  # type: ignore
                **dagster_dbt_translator.get_metadata(dbt_resource_props),
                MANIFEST_METADATA_KEY: DbtManifestWrapper(manifest=manifest),
                DAGSTER_DBT_TRANSLATOR_METADATA_KEY: dagster_dbt_translator,
            },
            group_name=dagster_dbt_translator.get_group_name(dbt_resource_props),
            code_version=default_code_version_fn(dbt_resource_props),
            freshness_policy=dagster_dbt_translator.get_freshness_policy(dbt_resource_props),
            auto_materialize_policy=dagster_dbt_translator.get_auto_materialize_policy(
                dbt_resource_props
            ),
        )

        test_unique_ids = [
            child_unique_id
            for child_unique_id in manifest["child_map"][unique_id]
            if child_unique_id.startswith("test")
        ]
        for test_unique_id in test_unique_ids:
            test_resource_props = manifest["nodes"][test_unique_id]
            check_spec = default_asset_check_fn(
                asset_key, unique_id, dagster_dbt_translator.settings, test_resource_props
            )

            if check_spec:
                check_specs.append(check_spec)

        # Translate parent unique ids to internal asset deps and non argument dep
        output_internal_deps = internal_asset_deps.setdefault(output_name, set())
        for parent_unique_id in parent_unique_ids:
            parent_resource_props = dbt_nodes[parent_unique_id]
            parent_asset_key = dagster_dbt_translator.get_asset_key(parent_resource_props)

            # Add this parent as an internal dependency
            output_internal_deps.add(parent_asset_key)

            # Mark this parent as an input if it has no dependencies
            if parent_unique_id not in deps:
                non_argument_deps.add(parent_asset_key)

    return list(non_argument_deps), outs, internal_asset_deps, check_specs

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

from dagster import (
    AssetCheckSpec,
    AssetDep,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    BackfillPolicy,
    DagsterInvalidDefinitionError,
    Nothing,
    PartitionsDefinition,
    multi_asset,
)
from dagster._utils.warnings import (
    disable_dagster_warnings,
    experimental_warning,
)

from .asset_utils import (
    DAGSTER_DBT_TRANSLATOR_METADATA_KEY,
    MANIFEST_METADATA_KEY,
    default_asset_check_fn,
    default_code_version_fn,
    get_deps,
    has_self_dependency,
)
from .dagster_dbt_translator import DagsterDbtTranslator, DbtManifestWrapper, validate_translator
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
    name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    dagster_dbt_translator: DagsterDbtTranslator = DagsterDbtTranslator(),
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
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
        name (Optional[str]): The name of the op.
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager".
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the dbt assets.
        dagster_dbt_translator (Optional[DagsterDbtTranslator]): Allows customizing how to map
            dbt models, seeds, etc. to asset keys and asset metadata.
        backfill_policy (Optional[BackfillPolicy]): If a partitions_def is defined, this determines
            how to execute backfills that target multiple partitions.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the assets.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.

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
    dagster_dbt_translator = validate_translator(dagster_dbt_translator)
    manifest = validate_manifest(manifest)

    unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude or "", manifest_json=manifest
    )
    node_info_by_dbt_unique_id = get_dbt_resource_props_by_dbt_unique_id_from_manifest(manifest)
    dbt_unique_id_deps = get_deps(
        dbt_nodes=node_info_by_dbt_unique_id,
        selected_unique_ids=unique_ids,
        asset_resource_types=ASSET_RESOURCE_TYPES,
    )
    (
        deps,
        outs,
        internal_asset_deps,
        check_specs,
    ) = get_dbt_multi_asset_args(
        dbt_nodes=node_info_by_dbt_unique_id,
        dbt_unique_id_deps=dbt_unique_id_deps,
        io_manager_key=io_manager_key,
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
    )

    if op_tags and "dagster-dbt/select" in op_tags:
        raise DagsterInvalidDefinitionError(
            "To specify a dbt selection, use the 'select' argument, not 'dagster-dbt/select'"
            " with op_tags"
        )

    if op_tags and "dagster-dbt/exclude" in op_tags:
        raise DagsterInvalidDefinitionError(
            "To specify a dbt exclusion, use the 'exclude' argument, not 'dagster-dbt/exclude'"
            " with op_tags"
        )

    resolved_op_tags = {
        **({"dagster-dbt/select": select} if select else {}),
        **({"dagster-dbt/exclude": exclude} if exclude else {}),
        **(op_tags if op_tags else {}),
    }

    def inner(fn) -> AssetsDefinition:
        asset_definition = multi_asset(
            outs=outs,
            name=name,
            internal_asset_deps=internal_asset_deps,
            deps=deps,
            compute_kind="dbt",
            partitions_def=partitions_def,
            can_subset=True,
            op_tags=resolved_op_tags,
            check_specs=check_specs,
            backfill_policy=backfill_policy,
        )(fn)

        return asset_definition

    return inner


def get_dbt_multi_asset_args(
    dbt_nodes: Mapping[str, Any],
    dbt_unique_id_deps: Mapping[str, FrozenSet[str]],
    io_manager_key: Optional[str],
    manifest: Mapping[str, Any],
    dagster_dbt_translator: DagsterDbtTranslator,
) -> Tuple[
    Sequence[AssetDep],
    Dict[str, AssetOut],
    Dict[str, Set[AssetKey]],
    Sequence[AssetCheckSpec],
]:
    deps: Set[AssetDep] = set()
    outs: Dict[str, AssetOut] = {}
    internal_asset_deps: Dict[str, Set[AssetKey]] = {}
    check_specs: Sequence[AssetCheckSpec] = []

    for unique_id, parent_unique_ids in dbt_unique_id_deps.items():
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

        # Translate parent unique ids to dependencies
        with disable_dagster_warnings():
            output_internal_deps = internal_asset_deps.setdefault(output_name, set())
            for parent_unique_id in parent_unique_ids:
                dbt_parent_resource_props = dbt_nodes[parent_unique_id]
                parent_asset_key = dagster_dbt_translator.get_asset_key(dbt_parent_resource_props)
                parent_partition_mapping = dagster_dbt_translator.get_partition_mapping(
                    dbt_resource_props,
                    dbt_parent_resource_props=dbt_parent_resource_props,
                )

                if parent_partition_mapping:
                    experimental_warning("DagsterDbtTranslator.get_partition_mapping")

                # Add this parent as an internal dependency
                output_internal_deps.add(parent_asset_key)

                # Mark this parent as an input if it has no dependencies
                if parent_unique_id not in dbt_unique_id_deps:
                    deps.add(
                        AssetDep(
                            asset=parent_asset_key,
                            partition_mapping=parent_partition_mapping,
                        )
                    )

            self_partition_mapping = dagster_dbt_translator.get_partition_mapping(
                dbt_resource_props,
                dbt_parent_resource_props=dbt_resource_props,
            )
            if self_partition_mapping and has_self_dependency(dbt_resource_props):
                experimental_warning("+meta.dagster.has_self_dependency")

                deps.add(
                    AssetDep(
                        asset=asset_key,
                        partition_mapping=self_partition_mapping,
                    )
                )
                output_internal_deps.add(asset_key)

    return list(deps), outs, internal_asset_deps, check_specs

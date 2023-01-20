import json
import shlex
from argparse import Namespace
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import dagster._check as check
from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    FreshnessPolicy,
    MetadataValue,
    OpExecutionContext,
    PartitionsDefinition,
    ResourceDefinition,
    multi_asset,
    with_resources,
)
from dagster._annotations import experimental
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._core.execution.context.init import build_init_resource_context
from dagster._utils.backcompat import experimental_arg_warning
from dbt.main import parse_args as dbt_parse_args

from ..asset_defs import (
    _get_asset_deps,
    _get_deps,
    _get_node_asset_key,
    _get_node_freshness_policy,
    _get_node_group_name,
)
from ..errors import DagsterDbtCloudJobInvariantViolationError
from ..utils import ASSET_RESOURCE_TYPES, result_to_events
from .resources import DbtCloudResource, DbtCloudRunStatus

DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR = "DBT_DAGSTER_COMPILE_RUN_ID"


class DbtCloudCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        dbt_cloud_resource_def: ResourceDefinition,
        job_id: int,
        node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
        node_info_to_group_fn: Callable[[Mapping[str, Any]], Optional[str]],
        node_info_to_freshness_policy_fn: Callable[[Mapping[str, Any]], Optional[FreshnessPolicy]],
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
    ):
        self._dbt_cloud_resource_def = dbt_cloud_resource_def
        self._dbt_cloud: DbtCloudResource = dbt_cloud_resource_def(build_init_resource_context())
        self._job_id = job_id
        self._project_id: int
        self._has_generate_docs: bool
        self._job_commands: List[str]
        self._job_materialization_command_step: int
        self._node_info_to_asset_key = node_info_to_asset_key
        self._node_info_to_group_fn = node_info_to_group_fn
        self._node_info_to_freshness_policy_fn = node_info_to_freshness_policy_fn
        self._partitions_def = partitions_def
        self._partition_key_to_vars_fn = partition_key_to_vars_fn

        super().__init__(unique_id=f"dbt-cloud-{job_id}")

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        dbt_nodes, dbt_dependencies = self._get_dbt_nodes_and_dependencies()
        return [self._build_dbt_cloud_assets_cacheable_data(dbt_nodes, dbt_dependencies)]

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        return with_resources(
            [
                self._build_dbt_cloud_assets_from_cacheable_data(assets_definition_metadata)
                for assets_definition_metadata in data
            ],
            {"dbt_cloud": self._dbt_cloud_resource_def},
        )

    @staticmethod
    def parse_dbt_command(dbt_command: str) -> Namespace:
        return dbt_parse_args(args=shlex.split(dbt_command)[1:])

    @staticmethod
    def get_job_materialization_command_step(execute_steps: List[str]) -> int:
        materialization_command_filter = [
            DbtCloudCacheableAssetsDefinition.parse_dbt_command(command).which in ["run", "build"]
            for command in execute_steps
        ]

        if sum(materialization_command_filter) != 1:
            raise DagsterDbtCloudJobInvariantViolationError(
                "The dbt Cloud job must have a single `dbt run` or `dbt build` in its commands. "
                f"Received commands: {execute_steps}."
            )

        return materialization_command_filter.index(True)

    @staticmethod
    def get_compile_filters(parsed_args: Namespace) -> List[str]:
        dbt_compile_options: List[str] = []

        selected_models = parsed_args.select or []
        if selected_models:
            dbt_compile_options.append(f"--select {' '.join(selected_models)}")

        excluded_models = parsed_args.exclude or []
        if excluded_models:
            dbt_compile_options.append(f"--exclude {' '.join(excluded_models)}")

        if parsed_args.selector_name:
            dbt_compile_options.append(f"--selector {parsed_args.selector_name}")

        return dbt_compile_options

    def _get_cached_compile_dbt_cloud_job_run(self, compile_run_id: int) -> Tuple[int, int]:
        compile_run = self._dbt_cloud.get_run(
            run_id=compile_run_id, include_related=["trigger", "run_steps"]
        )

        compile_run_status: str = compile_run["status_humanized"]
        if compile_run_status != DbtCloudRunStatus.SUCCESS:
            raise DagsterDbtCloudJobInvariantViolationError(
                f"The cached dbt Cloud job run `{compile_run_id}` must have a status of"
                f" `{DbtCloudRunStatus.SUCCESS}`. Received status: `{compile_run_status}. You can"
                f" view the full status of your dbt Cloud run at {compile_run['href']}. Once it has"
                " successfully completed, reload your Dagster definitions. If your run has failed,"
                " you must manually refresh the cache using the `dagster-dbt"
                " cache-compile-references` CLI."
            )

        compile_run_has_generate_docs = compile_run["trigger"]["generate_docs_override"]

        compile_job_materialization_command_step = len(compile_run["run_steps"])
        if compile_run_has_generate_docs:
            compile_job_materialization_command_step -= 1

        return compile_run_id, compile_job_materialization_command_step

    def _compile_dbt_cloud_job(self, dbt_cloud_job: Mapping[str, Any]) -> Tuple[int, int]:
        # Retrieve the filters options from the dbt Cloud job's materialization command.
        #
        # There are three filters: `--select`, `--exclude`, and `--selector`.
        materialization_command = self._job_commands[self._job_materialization_command_step]
        parsed_args = DbtCloudCacheableAssetsDefinition.parse_dbt_command(materialization_command)
        dbt_compile_options = DbtCloudCacheableAssetsDefinition.get_compile_filters(
            parsed_args=parsed_args
        )

        # Add the partition variable as a variable to the dbt Cloud job command.
        #
        # If existing variables passed through the dbt Cloud job's command, an error will be
        # raised. Since these are static variables anyways, they can be moved to the
        # `dbt_project.yml` without loss of functionality.
        #
        # Since we're only doing this to generate the dependency structure, just use an arbitrary
        # partition key (e.g. the last one) to retrieve the partition variable.
        dbt_vars = json.loads(parsed_args.vars or "{}")
        if dbt_vars:
            raise DagsterDbtCloudJobInvariantViolationError(
                f"The dbt Cloud job '{dbt_cloud_job['name']}' ({dbt_cloud_job['id']}) must not have"
                " variables defined from `--vars` in its `dbt run` or `dbt build` command."
                " Instead, declare the variables in the `dbt_project.yml` file. Received commands:"
                f" {self._job_commands}."
            )

        if self._partitions_def and self._partition_key_to_vars_fn:
            last_partition_key = self._partitions_def.get_last_partition_key()
            if last_partition_key is None:
                check.failed("PartitionsDefinition has no partitions")
            partition_var = self._partition_key_to_vars_fn(last_partition_key)

            dbt_compile_options.append(f"--vars '{json.dumps(partition_var)}'")

        # We need to retrieve the dependency structure for the assets in the dbt Cloud project.
        # However, we can't just use the dependency structure from the latest run, because
        # this historical structure may not be up-to-date with the current state of the project.
        #
        # By always doing a compile step, we can always get the latest dependency structure.
        # This incurs some latency, but at least it doesn't run through the entire materialization
        # process.
        dbt_compile_command = f"dbt compile {' '.join(dbt_compile_options)}"
        compile_run_dbt_output = self._dbt_cloud.run_job_and_poll(
            job_id=self._job_id,
            cause="Generating software-defined assets for Dagster.",
            steps_override=[dbt_compile_command],
        )

        # Target the compile execution step when retrieving run artifacts, rather than assuming
        # that the last step is the correct target.
        #
        # Here, we ignore the `dbt docs generate` step.
        compile_job_materialization_command_step = len(
            compile_run_dbt_output.run_details.get("run_steps", [])
        )
        if self._has_generate_docs:
            compile_job_materialization_command_step -= 1

        return compile_run_dbt_output.run_id, compile_job_materialization_command_step

    def _get_dbt_nodes_and_dependencies(
        self,
    ) -> Tuple[Mapping[str, Any], Mapping[str, FrozenSet[str]]]:
        """
        For a given dbt Cloud job, fetch the latest run's dependency structure of executed nodes.
        """
        # Fetch information about the job.
        job = self._dbt_cloud.get_job(job_id=self._job_id)
        self._project_id = job["project_id"]
        self._has_generate_docs = job["generate_docs"]

        # We constraint the kinds of dbt Cloud jobs that we support running.
        #
        # A simple constraint is that we only support jobs that run multiple steps,
        # but it must contain one of either `dbt run` or `dbt build`.
        #
        # As a reminder, `dbt deps` is automatically run before the job's configured commands.
        # And if the settings are enabled, `dbt docs generate` and `dbt source freshness` can
        # automatically run after the job's configured commands.
        #
        # These commands that execute before and after the job's configured commands do not count
        # towards the single command constraint.
        self._job_commands = job["execute_steps"]
        self._job_materialization_command_step = (
            DbtCloudCacheableAssetsDefinition.get_job_materialization_command_step(
                execute_steps=self._job_commands
            )
        )

        # Determine whether to use a cached compile run. This should only be set up if the user is
        # using a GitHub action along with their dbt project.
        dbt_cloud_job_env_vars = self._dbt_cloud.get_job_environment_variables(
            project_id=self._project_id, job_id=self._job_id
        )
        compile_run_id = (
            dbt_cloud_job_env_vars.get(DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR, {})
            .get("job", {})
            .get("value")
        )

        compile_run_id, compile_job_materialization_command_step = (
            # If a compile run is cached, then use it.
            self._get_cached_compile_dbt_cloud_job_run(compile_run_id=int(compile_run_id))
            if compile_run_id
            # Otherwise, compile the dbt Cloud project in an ad-hoc manner.
            else self._compile_dbt_cloud_job(dbt_cloud_job=job)
        )

        manifest_json = self._dbt_cloud.get_manifest(
            run_id=compile_run_id, step=compile_job_materialization_command_step
        )
        run_results_json = self._dbt_cloud.get_run_results(
            run_id=compile_run_id, step=compile_job_materialization_command_step
        )

        # Filter the manifest to only include the nodes that were executed.
        dbt_nodes: Dict[str, Any] = {
            **manifest_json.get("nodes", {}),
            **manifest_json.get("sources", {}),
            **manifest_json.get("metrics", {}),
        }
        executed_node_ids: Set[str] = set(
            result["unique_id"] for result in run_results_json["results"]
        )

        # If there are no executed nodes, then there are no assets to generate.
        # Inform the user to inspect their dbt Cloud job's command.
        if not executed_node_ids:
            raise DagsterDbtCloudJobInvariantViolationError(
                f"The dbt Cloud job '{job['name']}' ({job['id']}) does not generate any "
                "software-defined assets. Ensure that your dbt project has nodes to execute, "
                "and that your dbt Cloud job's materialization command has the proper filter "
                f"options applied. Received commands: {self._job_commands}."
            )

        # Generate the dependency structure for the executed nodes.
        dbt_dependencies = _get_deps(
            dbt_nodes=dbt_nodes,
            selected_unique_ids=executed_node_ids,
            asset_resource_types=ASSET_RESOURCE_TYPES,
        )

        return dbt_nodes, dbt_dependencies

    def _build_dbt_cloud_assets_cacheable_data(
        self, dbt_nodes: Mapping[str, Any], dbt_dependencies: Mapping[str, FrozenSet[str]]
    ) -> AssetsDefinitionCacheableData:
        """
        Given all of the nodes and dependencies for a dbt Cloud job, build the cacheable
        representation that generate the asset definition for the job.
        """
        (
            asset_deps,
            asset_ins,
            asset_outs,
            group_names_by_key,
            freshness_policies_by_key,
            fqns_by_output_name,
            metadata_by_output_name,
        ) = _get_asset_deps(
            dbt_nodes=dbt_nodes,
            deps=dbt_dependencies,
            node_info_to_asset_key=self._node_info_to_asset_key,
            node_info_to_group_fn=self._node_info_to_group_fn,
            node_info_to_freshness_policy_fn=self._node_info_to_freshness_policy_fn,
            # TODO: In the future, allow the IO manager to be specified.
            io_manager_key=None,
            # We shouldn't display the raw sql. Instead, inspect if dbt docs were generated,
            # and attach metadata to link to the docs.
            display_raw_sql=False,
        )

        return AssetsDefinitionCacheableData(
            # TODO: In the future, we should allow additional upstream assets to be specified.
            keys_by_input_name={
                input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
            },
            keys_by_output_name={
                output_name: asset_key for asset_key, (output_name, _) in asset_outs.items()
            },
            internal_asset_deps={
                asset_outs[asset_key][0]: asset_deps for asset_key, asset_deps in asset_deps.items()
            },
            # We don't rely on a static group name. Instead, we map over the dbt metadata to
            # determine the group name for each asset.
            group_name=None,
            metadata_by_output_name={
                output_name: self._build_dbt_cloud_assets_metadata(dbt_metadata)
                for output_name, dbt_metadata in metadata_by_output_name.items()
            },
            # TODO: In the future, we should allow the key prefix to be specified.
            key_prefix=None,
            can_subset=True,
            extra_metadata={
                "job_id": self._job_id,
                "job_commands": self._job_commands,
                "job_materialization_command_step": self._job_materialization_command_step,
                "group_names_by_output_name": {
                    asset_outs[asset_key][0]: group_name
                    for asset_key, group_name in group_names_by_key.items()
                },
                "fqns_by_output_name": fqns_by_output_name,
            },
            freshness_policies_by_output_name={
                asset_outs[asset_key][0]: freshness_policy
                for asset_key, freshness_policy in freshness_policies_by_key.items()
            },
        )

    def _build_dbt_cloud_assets_metadata(self, dbt_metadata: Dict[str, Any]) -> MetadataUserInput:
        metadata = {
            "dbt Cloud Job": MetadataValue.url(
                self._dbt_cloud.build_url_for_job(
                    project_id=self._project_id,
                    job_id=self._job_id,
                )
            ),
        }

        if self._has_generate_docs:
            metadata["dbt Cloud Documentation"] = MetadataValue.url(
                self._dbt_cloud.build_url_for_cloud_docs(
                    job_id=self._job_id,
                    resource_type=dbt_metadata["resource_type"],
                    unique_id=dbt_metadata["unique_id"],
                )
            )

        return metadata

    def _build_dbt_cloud_assets_from_cacheable_data(
        self, assets_definition_cacheable_data: AssetsDefinitionCacheableData
    ) -> AssetsDefinition:
        metadata = cast(Mapping[str, Any], assets_definition_cacheable_data.extra_metadata)
        job_id = cast(int, metadata["job_id"])
        job_commands = cast(List[str], list(metadata["job_commands"]))
        job_materialization_command_step = cast(int, metadata["job_materialization_command_step"])
        group_names_by_output_name = cast(Mapping[str, str], metadata["group_names_by_output_name"])
        fqns_by_output_name = cast(Mapping[str, List[str]], metadata["fqns_by_output_name"])

        @multi_asset(
            name=f"dbt_cloud_job_{job_id}",
            non_argument_deps=set(
                (assets_definition_cacheable_data.keys_by_input_name or {}).values()
            ),
            outs={
                output_name: AssetOut(
                    key=asset_key,
                    group_name=group_names_by_output_name.get(output_name),
                    freshness_policy=(
                        assets_definition_cacheable_data.freshness_policies_by_output_name or {}
                    ).get(
                        output_name,
                    ),
                    metadata=(assets_definition_cacheable_data.metadata_by_output_name or {}).get(
                        output_name
                    ),
                    is_required=False,
                )
                for output_name, asset_key in (
                    assets_definition_cacheable_data.keys_by_output_name or {}
                ).items()
            },
            internal_asset_deps={
                output_name: set(asset_deps)
                for output_name, asset_deps in (
                    assets_definition_cacheable_data.internal_asset_deps or {}
                ).items()
            },
            partitions_def=self._partitions_def,
            can_subset=assets_definition_cacheable_data.can_subset,
            required_resource_keys={"dbt_cloud"},
            compute_kind="dbt",
        )
        def _assets(context: OpExecutionContext):
            dbt_cloud = cast(DbtCloudResource, context.resources.dbt_cloud)

            # Add the partition variable as a variable to the dbt Cloud job command.
            dbt_options: List[str] = []
            if context.has_partition_key and self._partition_key_to_vars_fn:
                partition_var = self._partition_key_to_vars_fn(context.partition_key)

                dbt_options.append(f"--vars '{json.dumps(partition_var)}'")

            # Map the selected outputs to dbt models that should be materialized.
            #
            # HACK: This selection filter works even if an existing `--select` is specified in the
            # dbt Cloud job. We take advantage of the fact that the last `--select` will be used.
            #
            # This is not ideal, as the triggered run for the dbt Cloud job will still have both
            # `--select` options when displayed in the UI, but parsing the command line argument
            # to remove the initial select using argparse.
            if len(context.selected_output_names) != len(
                assets_definition_cacheable_data.keys_by_output_name or {}
            ):
                selected_models = [
                    ".".join(fqns_by_output_name[output_name])
                    for output_name in context.selected_output_names
                ]

                dbt_options.append(f"--select {' '.join(sorted(selected_models))}")

            # Override the materialization step with the selection filter
            materialization_command = job_commands[job_materialization_command_step]
            job_commands[
                job_materialization_command_step
            ] = f"{materialization_command} {' '.join(dbt_options)}".strip()

            # Run the dbt Cloud job to rematerialize the assets.
            dbt_cloud_output = dbt_cloud.run_job_and_poll(
                job_id=job_id,
                cause=f"Materializing software-defined assets in Dagster run {context.run_id[:8]}",
                steps_override=job_commands,
            )

            # Target the materialization step when retrieving run artifacts, rather than assuming
            # that the last step is the correct target.
            #
            # We ignore the commands in front of the materialization command. And again, we ignore
            # the `dbt docs generate` step.
            materialization_command_step = len(dbt_cloud_output.run_details.get("run_steps", []))
            materialization_command_step -= len(job_commands) - job_materialization_command_step - 1
            if dbt_cloud_output.run_details.get("job", {}).get("generate_docs"):
                materialization_command_step -= 1

            # TODO: Assume the run completely fails or completely succeeds.
            # In the future, we can relax this assumption.
            manifest_json = dbt_cloud.get_manifest(
                run_id=dbt_cloud_output.run_id, step=materialization_command_step
            )
            run_results_json = self._dbt_cloud.get_run_results(
                run_id=dbt_cloud_output.run_id, step=materialization_command_step
            )

            for result in run_results_json.get("results", []):
                yield from result_to_events(
                    result=result,
                    docs_url=dbt_cloud_output.docs_url,
                    node_info_to_asset_key=self._node_info_to_asset_key,
                    manifest_json=manifest_json,
                    # TODO: In the future, allow arbitrary mappings to Dagster output metadata from
                    # the dbt metadata.
                    extra_metadata=None,
                    generate_asset_outputs=True,
                )

        return _assets


@experimental
def load_assets_from_dbt_cloud_job(
    dbt_cloud: ResourceDefinition,
    job_id: int,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
    node_info_to_group_fn: Callable[[Mapping[str, Any]], Optional[str]] = _get_node_group_name,
    node_info_to_freshness_policy_fn: Callable[
        [Mapping[str, Any]], Optional[FreshnessPolicy]
    ] = _get_node_freshness_policy,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
) -> CacheableAssetsDefinition:
    """
    Loads a set of dbt models, managed by a dbt Cloud job, into Dagster assets. In order to
    determine the set of dbt models, the project is compiled to generate the necessary artifacts
    that define the dbt models and their dependencies.

    One Dagster asset is created for each dbt model.

    Args:
        dbt_cloud (ResourceDefinition): The dbt Cloud resource to use to connect to the dbt Cloud API.
        job_id (int): The ID of the dbt Cloud job to load assets from.
        node_info_to_asset_key: (Mapping[str, Any] -> AssetKey): A function that takes a dictionary
            of dbt metadata and returns the AssetKey that you want to represent a given model or
            source. By default: dbt model -> AssetKey([model_name]) and
            dbt source -> AssetKey([source_name, table_name])
        node_info_to_group_fn (Dict[str, Any] -> Optional[str]): A function that takes a
            dictionary of dbt node info and returns the group that this node should be assigned to.
        node_info_to_freshness_policy_fn (Dict[str, Any] -> Optional[FreshnessPolicy]): A function
            that takes a dictionary of dbt node info and optionally returns a FreshnessPolicy that
            should be applied to this node. By default, freshness policies will be created from
            config applied to dbt models, i.e.:
            `dagster_freshness_policy={"maximum_lag_minutes": 60, "cron_schedule": "0 9 * * *"}`
            will result in that model being assigned
            `FreshnessPolicy(maximum_lag_minutes=60, cron_schedule="0 9 * * *")`
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the dbt assets.
        partition_key_to_vars_fn (Optional[str -> Dict[str, Any]]): A function to translate a given
            partition key (e.g. '2022-01-01') to a dictionary of vars to be passed into the dbt
            invocation (e.g. {"run_date": "2022-01-01"})

    Returns:
        CacheableAssetsDefinition: A definition for the loaded assets.

    Examples:
        .. code-block:: python

            from dagster import repository
            from dagster_dbt import dbt_cloud_resource, load_assets_from_dbt_cloud_job

            DBT_CLOUD_JOB_ID = 1234

            dbt_cloud = dbt_cloud_resource.configured(
                {
                    "auth_token": {"env": "DBT_CLOUD_API_TOKEN"},
                    "account_id": {"env": "DBT_CLOUD_ACCOUNT_ID"},
                }
            )

            dbt_cloud_assets = load_assets_from_dbt_cloud_job(
                dbt_cloud=dbt_cloud, job_id=DBT_CLOUD_JOB_ID
            )


            @repository
            def dbt_cloud_sandbox():
                return [dbt_cloud_assets]
    """
    if partitions_def:
        experimental_arg_warning("partitions_def", "load_assets_from_dbt_manifest")
    if partition_key_to_vars_fn:
        experimental_arg_warning("partition_key_to_vars_fn", "load_assets_from_dbt_manifest")
        check.invariant(
            partitions_def is not None,
            "Cannot supply a `partition_key_to_vars_fn` without a `partitions_def`.",
        )

    return DbtCloudCacheableAssetsDefinition(
        dbt_cloud_resource_def=dbt_cloud,
        job_id=job_id,
        node_info_to_asset_key=node_info_to_asset_key,
        node_info_to_group_fn=node_info_to_group_fn,
        node_info_to_freshness_policy_fn=node_info_to_freshness_policy_fn,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
    )

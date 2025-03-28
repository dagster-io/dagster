import json
import shlex
from argparse import ArgumentParser, Namespace
from collections.abc import Mapping, Sequence
from contextlib import suppress
from typing import Any, Callable, Optional, Union, cast

import dagster._check as check
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AutoMaterializePolicy,
    FreshnessPolicy,
    MetadataValue,
    PartitionsDefinition,
    ResourceDefinition,
    multi_asset,
    with_resources,
)
from dagster._annotations import beta, beta_param
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.execution.context.init import build_init_resource_context

from dagster_dbt.asset_specs import build_dbt_asset_specs
from dagster_dbt.asset_utils import (
    DAGSTER_DBT_UNIQUE_ID_METADATA_KEY,
    default_asset_key_fn,
    default_auto_materialize_policy_fn,
    default_description_fn,
    default_freshness_policy_fn,
    default_group_from_dbt_resource_props,
)
from dagster_dbt.cloud.resources import DbtCloudClient, DbtCloudClientResource, DbtCloudRunStatus
from dagster_dbt.cloud.utils import result_to_events
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.errors import DagsterDbtCloudJobInvariantViolationError
from dagster_dbt.utils import get_dbt_resource_props_by_dbt_unique_id_from_manifest

DAGSTER_DBT_COMPILE_RUN_ID_ENV_VAR = "DBT_DAGSTER_COMPILE_RUN_ID"


class DbtCloudCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        dbt_cloud_resource_def: Union[DbtCloudClientResource, ResourceDefinition],
        job_id: int,
        node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey],
        node_info_to_group_fn: Callable[[Mapping[str, Any]], Optional[str]],
        node_info_to_freshness_policy_fn: Callable[[Mapping[str, Any]], Optional[FreshnessPolicy]],
        node_info_to_auto_materialize_policy_fn: Callable[
            [Mapping[str, Any]], Optional[AutoMaterializePolicy]
        ],
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
    ):
        self._dbt_cloud_resource_def: ResourceDefinition = (
            dbt_cloud_resource_def.get_resource_definition()
            if isinstance(dbt_cloud_resource_def, DbtCloudClientResource)
            else dbt_cloud_resource_def
        )

        self._dbt_cloud: DbtCloudClient = (
            dbt_cloud_resource_def.process_config_and_initialize().get_dbt_client()
            if isinstance(dbt_cloud_resource_def, DbtCloudClientResource)
            else dbt_cloud_resource_def(build_init_resource_context())
        )
        self._job_id = job_id
        self._project_id: int
        self._has_generate_docs: bool
        self._job_commands: list[str]
        self._job_materialization_command_step: int
        self._node_info_to_asset_key = node_info_to_asset_key
        self._node_info_to_group_fn = node_info_to_group_fn
        self._node_info_to_freshness_policy_fn = node_info_to_freshness_policy_fn
        self._node_info_to_auto_materialize_policy_fn = node_info_to_auto_materialize_policy_fn
        self._partitions_def = partitions_def
        self._partition_key_to_vars_fn = partition_key_to_vars_fn

        super().__init__(unique_id=f"dbt-cloud-{job_id}")

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        manifest_json, executed_unique_ids = self._get_manifest_json_and_executed_unique_ids()
        return [self._build_dbt_cloud_assets_cacheable_data(manifest_json, executed_unique_ids)]

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
        from dbt.cli.flags import Flags, args_to_context

        args = shlex.split(dbt_command)[1:]

        # nasty hack to get dbt to parse the args, profiles-dir must be set to an existing directory
        return Namespace(**vars(Flags(args_to_context(args + ["--profiles-dir", "."]))))

    @staticmethod
    def get_job_materialization_command_step(execute_steps: list[str]) -> int:
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
    def get_compile_filters(parsed_args: Namespace) -> list[str]:
        dbt_compile_options: list[str] = []

        selected_models = parsed_args.select or []
        if selected_models:
            dbt_compile_options.append(f"--select {' '.join(selected_models)}")

        excluded_models = parsed_args.exclude or []
        if excluded_models:
            dbt_compile_options.append(f"--exclude {' '.join(excluded_models)}")

        selector = getattr(parsed_args, "selector_name", None) or getattr(
            parsed_args, "selector", None
        )
        if selector:
            dbt_compile_options.append(f"--selector {selector}")

        return dbt_compile_options

    def _get_cached_compile_dbt_cloud_job_run(self, compile_run_id: int) -> tuple[int, int]:
        # If the compile run is ongoing, allow it a grace period of 10 minutes to finish.
        with suppress(Exception):
            self._dbt_cloud.poll_run(run_id=compile_run_id, poll_timeout=600)

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

    def _compile_dbt_cloud_job(self, dbt_cloud_job: Mapping[str, Any]) -> tuple[int, int]:
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
        if parsed_args.vars and parsed_args.vars != "{}":
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

    def _get_manifest_json_and_executed_unique_ids(
        self,
    ) -> tuple[Mapping[str, Any], frozenset[str]]:
        """For a given dbt Cloud job, fetch the latest run's dependency structure of executed nodes."""
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
        executed_node_ids: set[str] = set(
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

        # sort to stabilize job snapshots
        return manifest_json, frozenset(sorted(executed_node_ids))

    def _build_dbt_cloud_assets_cacheable_data(
        self, manifest_json: Mapping[str, Any], executed_unique_ids: frozenset[str]
    ) -> AssetsDefinitionCacheableData:
        """Given all of the nodes and dependencies for a dbt Cloud job, build the cacheable
        representation that generate the asset definition for the job.
        """

        class CustomDagsterDbtTranslator(DagsterDbtTranslator):
            @classmethod
            def get_asset_key(cls, dbt_resource_props):  # pyright: ignore[reportIncompatibleMethodOverride]
                return self._node_info_to_asset_key(dbt_resource_props)

            @classmethod
            def get_description(cls, dbt_resource_props):  # pyright: ignore[reportIncompatibleMethodOverride]
                # We shouldn't display the raw sql. Instead, inspect if dbt docs were generated,
                # and attach metadata to link to the docs.
                return default_description_fn(dbt_resource_props, display_raw_sql=False)

            @classmethod
            def get_group_name(cls, dbt_resource_props):  # pyright: ignore[reportIncompatibleMethodOverride]
                return self._node_info_to_group_fn(dbt_resource_props)

            @classmethod
            def get_freshness_policy(cls, dbt_resource_props):  # pyright: ignore[reportIncompatibleMethodOverride]
                return self._node_info_to_freshness_policy_fn(dbt_resource_props)

            @classmethod
            def get_auto_materialize_policy(cls, dbt_resource_props):  # pyright: ignore[reportIncompatibleMethodOverride]
                return self._node_info_to_auto_materialize_policy_fn(dbt_resource_props)

        # generate specs for each executed node
        dbt_nodes = get_dbt_resource_props_by_dbt_unique_id_from_manifest(manifest_json)
        specs = build_dbt_asset_specs(
            manifest=manifest_json,
            dagster_dbt_translator=CustomDagsterDbtTranslator(),
            select=" ".join(
                f"fqn:{'.'.join(dbt_nodes[unique_id]['fqn'])}" for unique_id in executed_unique_ids
            ),
        )

        return AssetsDefinitionCacheableData(
            # TODO: In the future, we should allow additional upstream assets to be specified.
            keys_by_output_name={spec.key.to_python_identifier(): spec.key for spec in specs},
            internal_asset_deps={
                spec.key.to_python_identifier(): {dep.asset_key for dep in spec.deps}
                for spec in specs
            },
            metadata_by_output_name={
                spec.key.to_python_identifier(): self._build_dbt_cloud_assets_metadata(
                    dbt_nodes[spec.metadata[DAGSTER_DBT_UNIQUE_ID_METADATA_KEY]]
                )
                for spec in specs
            },
            extra_metadata={
                "job_id": self._job_id,
                "job_commands": self._job_commands,
                "job_materialization_command_step": self._job_materialization_command_step,
                "group_names_by_output_name": {
                    spec.key.to_python_identifier(): spec.group_name for spec in specs
                },
                "fqns_by_output_name": {
                    spec.key.to_python_identifier(): dbt_nodes[
                        spec.metadata[DAGSTER_DBT_UNIQUE_ID_METADATA_KEY]
                    ]["fqn"]
                    for spec in specs
                },
            },
            freshness_policies_by_output_name={
                spec.key.to_python_identifier(): spec.freshness_policy
                for spec in specs
                if spec.freshness_policy
            },
            auto_materialize_policies_by_output_name={
                spec.key.to_python_identifier(): spec.auto_materialize_policy
                for spec in specs
                if spec.auto_materialize_policy
            },
        )

    def _build_dbt_cloud_assets_metadata(
        self, resource_props: Mapping[str, Any]
    ) -> RawMetadataMapping:
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
                    resource_type=resource_props["resource_type"],
                    unique_id=resource_props["unique_id"],
                )
            )

        return metadata

    def _rebuild_specs(self, cacheable_data: AssetsDefinitionCacheableData) -> Sequence[AssetSpec]:
        specs = []
        for id, key in (cacheable_data.keys_by_output_name or {}).items():
            specs.append(
                AssetSpec(
                    key=key,
                    group_name=(cacheable_data.extra_metadata or {})[
                        "group_names_by_output_name"
                    ].get(id),
                    deps=(cacheable_data.internal_asset_deps or {}).get(id),
                    metadata=(cacheable_data.metadata_by_output_name or {}).get(id),
                    freshness_policy=(cacheable_data.freshness_policies_by_output_name or {}).get(
                        id
                    ),
                    auto_materialize_policy=(
                        cacheable_data.auto_materialize_policies_by_output_name or {}
                    ).get(id),
                    skippable=False,
                )
            )
        return specs

    def _build_dbt_cloud_assets_from_cacheable_data(
        self, assets_definition_cacheable_data: AssetsDefinitionCacheableData
    ) -> AssetsDefinition:
        metadata = cast(Mapping[str, Any], assets_definition_cacheable_data.extra_metadata)
        job_id = cast(int, metadata["job_id"])
        job_commands = cast(list[str], list(metadata["job_commands"]))
        job_materialization_command_step = cast(int, metadata["job_materialization_command_step"])
        fqns_by_output_name = cast(Mapping[str, list[str]], metadata["fqns_by_output_name"])

        @multi_asset(
            name=f"dbt_cloud_job_{job_id}",
            specs=self._rebuild_specs(assets_definition_cacheable_data),
            partitions_def=self._partitions_def,
            can_subset=True,
            required_resource_keys={"dbt_cloud"},
            compute_kind="dbt",
        )
        def _assets(context: AssetExecutionContext):
            dbt_cloud = cast(DbtCloudClient, context.resources.dbt_cloud)

            # Add the partition variable as a variable to the dbt Cloud job command.
            dbt_options: list[str] = []
            if context.has_partition_key and self._partition_key_to_vars_fn:
                partition_var = self._partition_key_to_vars_fn(context.partition_key)

                dbt_options.append(f"--vars '{json.dumps(partition_var)}'")

            # Prepare the materialization step to be overriden with the selection filter
            materialization_command = job_commands[job_materialization_command_step]

            # Map the selected outputs to dbt models that should be materialized.
            #
            # From version 1.5.0 dbt allows multiple select args to be used in command,
            # so we cannot just add our arg as last one to be used and need to remove
            # both command-native --select args and --selector arg to run dagster-generated
            # subset of models
            #
            # See https://docs.getdbt.com/reference/node-selection/syntax for details.
            if context.is_subset:
                selected_models = [
                    ".".join(fqns_by_output_name[output_name])
                    for output_name in context.op_execution_context.selected_output_names
                    # outputs corresponding to asset checks from dbt tests won't be in this dict
                    if output_name in fqns_by_output_name
                ]

                dbt_options.append(f"--select {' '.join(sorted(selected_models))}")

                parser = ArgumentParser(description="Parse selection args from dbt command")
                # Select arg should have nargs="+", but we probably want dbt itself to deal with it
                parser.add_argument("-s", "--select", nargs="*", action="append")
                parser.add_argument("--selector", nargs="*")

                split_materialization_command = shlex.split(materialization_command)
                _, non_selection_command_parts = parser.parse_known_args(
                    split_materialization_command
                )
                materialization_command = " ".join(non_selection_command_parts)

            job_commands[job_materialization_command_step] = (
                f"{materialization_command} {' '.join(dbt_options)}".strip()
            )

            # Run the dbt Cloud job to rematerialize the assets.
            dbt_cloud_output = dbt_cloud.run_job_and_poll(
                job_id=job_id,
                cause=f"Materializing software-defined assets in Dagster run {context.run.run_id[:8]}",
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


@beta
@beta_param(param="partitions_def")
@beta_param(param="partition_key_to_vars_fn")
def load_assets_from_dbt_cloud_job(
    dbt_cloud: Union[DbtCloudClientResource, ResourceDefinition],
    job_id: int,
    node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = default_asset_key_fn,
    node_info_to_group_fn: Callable[
        [Mapping[str, Any]], Optional[str]
    ] = default_group_from_dbt_resource_props,
    node_info_to_freshness_policy_fn: Callable[
        [Mapping[str, Any]], Optional[FreshnessPolicy]
    ] = default_freshness_policy_fn,
    node_info_to_auto_materialize_policy_fn: Callable[
        [Mapping[str, Any]], Optional[AutoMaterializePolicy]
    ] = default_auto_materialize_policy_fn,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_key_to_vars_fn: Optional[Callable[[str], Mapping[str, Any]]] = None,
) -> CacheableAssetsDefinition:
    """Loads a set of dbt models, managed by a dbt Cloud job, into Dagster assets. In order to
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
        node_info_to_auto_materialize_policy_fn (Dict[str, Any] -> Optional[AutoMaterializePolicy]):
            A function that takes a dictionary of dbt node info and optionally returns a AutoMaterializePolicy
            that should be applied to this node. By default, AutoMaterializePolicies will be created from
            config applied to dbt models, i.e.:
            `dagster_auto_materialize_policy={"type": "lazy"}` will result in that model being assigned
            `AutoMaterializePolicy.lazy()`
        node_info_to_definition_metadata_fn (Dict[str, Any] -> Optional[Dict[str, RawMetadataMapping]]):
            A function that takes a dictionary of dbt node info and optionally returns a dictionary
            of metadata to be attached to the corresponding definition. This is added to the default
            metadata assigned to the node, which consists of the node's schema (if present).
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
    if partition_key_to_vars_fn:
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
        node_info_to_auto_materialize_policy_fn=node_info_to_auto_materialize_policy_fn,
        partitions_def=partitions_def,
        partition_key_to_vars_fn=partition_key_to_vars_fn,
    )

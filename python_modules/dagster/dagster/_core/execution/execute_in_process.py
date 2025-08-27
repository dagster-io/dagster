from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from dagster import _check as check
from dagster._core.definitions import GraphDefinition, JobDefinition, Node, NodeHandle, OpDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.job_base import IJob
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.execution.api import (
    ExecuteRunWithPlanIterable,
    create_execution_plan,
    ephemeral_instance_if_missing,
    job_execution_iterator,
)
from dagster._core.execution.context_creation_job import (
    PlanOrchestrationContextManager,
    orchestration_context_event_generator,
)
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance import DagsterInstance
from dagster._core.types.dagster_type import DagsterTypeKind
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._core.definitions.resource_definition import ResourceDefinition
    from dagster._core.definitions.run_config import RunConfig
    from dagster._core.execution.plan.outputs import StepOutputHandle
    from dagster._core.storage.dagster_run import DagsterRun


def merge_run_tags(
    job_def: JobDefinition,
    partition_key: Optional[str],
    tags: Optional[Mapping[str, str]],
    asset_selection: Optional[Sequence[AssetKey]],
    instance: Optional[DagsterInstance],
    run_config: Optional[Mapping[str, object]],
) -> Mapping[str, str]:
    merged_run_tags = merge_dicts(job_def.run_tags, tags or {})
    if partition_key:
        with partition_loading_context(dynamic_partitions_store=instance) as ctx:
            job_def.validate_partition_key(
                partition_key,
                selected_asset_keys=asset_selection,
                context=ctx,
            )
        tags_for_partition_key = job_def.get_tags_for_partition_key(
            partition_key,
            selected_asset_keys=asset_selection,
        )

        if not run_config and job_def.partitioned_config:
            run_config = job_def.partitioned_config.get_run_config_for_partition_key(partition_key)

        if job_def.partitioned_config:
            merged_run_tags.update(
                job_def.partitioned_config.get_tags_for_partition_key(
                    partition_key, job_name=job_def.name
                )
            )
        else:
            merged_run_tags.update(tags_for_partition_key)
    return merged_run_tags


def type_check_and_normalize_args(
    run_config: Optional[Union[Mapping[str, Any], "RunConfig"]] = None,
    partition_key: Optional[str] = None,
    op_selection: Optional[Sequence[str]] = None,
    asset_selection: Optional[Sequence[AssetKey]] = None,
    input_values: Optional[Mapping[str, object]] = None,
    resources: Optional[Mapping[str, object]] = None,
) -> tuple[
    Mapping[str, object],
    Sequence[str],
    Sequence[AssetKey],
    Mapping[str, "ResourceDefinition"],
    Optional[str],
    Mapping[str, object],
]:
    from dagster._core.definitions.run_config import convert_config_input
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    run_config = check.opt_mapping_param(convert_config_input(run_config), "run_config")
    op_selection = check.opt_sequence_param(op_selection, "op_selection", str)
    asset_selection = check.opt_sequence_param(asset_selection, "asset_selection", AssetKey)
    resources = check.opt_mapping_param(resources, "resources", key_type=str)

    resource_defs = wrap_resources_for_execution(resources)

    check.invariant(
        not (op_selection and asset_selection),
        "op_selection and asset_selection cannot both be provided as args to execute_in_process",
    )

    partition_key = check.opt_str_param(partition_key, "partition_key")
    input_values = check.opt_mapping_param(input_values, "input_values")
    return (
        run_config,
        op_selection,
        asset_selection,
        resource_defs,
        partition_key,
        input_values,
    )


def core_execute_in_process(
    run_config: Mapping[str, object],
    job: IJob,
    instance: Optional[DagsterInstance],
    output_capturing_enabled: bool,
    raise_on_error: bool,
    run_tags: Optional[Mapping[str, str]] = None,
    run_id: Optional[str] = None,
    asset_selection: Optional[frozenset[AssetKey]] = None,
) -> ExecuteInProcessResult:
    job_def = job.get_definition()

    _check_top_level_inputs(job_def)

    execution_plan = create_execution_plan(
        job,
        run_config=run_config,
        instance_ref=instance.get_ref() if instance and instance.is_persistent else None,
    )

    output_capture: dict[StepOutputHandle, Any] = {}

    with ephemeral_instance_if_missing(instance) as execute_instance:
        run = execute_instance.create_run_for_job(
            job_def=job_def,
            run_config=run_config,
            tags={**job_def.run_tags, **(run_tags or {})},
            run_id=run_id,
            asset_selection=asset_selection,
            execution_plan=execution_plan,
        )
        run_id = run.run_id

        execute_run_iterable = ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=job_execution_iterator,
            execution_context_manager=PlanOrchestrationContextManager(
                context_event_generator=orchestration_context_event_generator,
                job=job,
                execution_plan=execution_plan,
                dagster_run=run,
                instance=execute_instance,
                run_config=run_config,
                executor_defs=None,
                output_capture=output_capture if output_capturing_enabled else None,
                raise_on_error=raise_on_error,
            ),
        )
        event_list = list(execute_run_iterable)
        run = execute_instance.get_run_by_id(run_id)

    return ExecuteInProcessResult(
        job_def=job_def,
        event_list=event_list,
        dagster_run=cast("DagsterRun", run),
        output_capture=output_capture,
    )


def _check_top_level_inputs(job_def: JobDefinition) -> None:
    for input_mapping in job_def.graph.input_mappings:
        node = job_def.graph.node_named(input_mapping.maps_to.node_name)
        top_level_input_name = input_mapping.graph_input_name
        input_name = input_mapping.maps_to.input_name
        _check_top_level_inputs_for_node(
            node,
            top_level_input_name,
            job_def.has_direct_input_value(top_level_input_name),
            input_name,
            job_def.name,
            None,
        )


def _check_top_level_inputs_for_node(
    node: Node,
    top_level_input_name: str,
    top_level_input_provided: bool,
    input_name: str,
    job_name: str,
    parent_handle: Optional[NodeHandle],
) -> None:
    if isinstance(node.definition, GraphDefinition):
        graph_def = cast("GraphDefinition", node.definition)
        for input_mapping in graph_def.input_mappings:
            next_node = graph_def.node_named(input_mapping.maps_to.node_name)
            input_name = input_mapping.maps_to.input_name
            _check_top_level_inputs_for_node(
                next_node,
                top_level_input_name,
                top_level_input_provided,
                input_name,
                job_name,
                NodeHandle(node.name, parent_handle),
            )
    else:
        cur_node_handle = NodeHandle(node.name, parent_handle)
        op_def = cast("OpDefinition", node.definition)
        input_def = op_def.input_def_named(input_name)
        if (
            not input_def.dagster_type.loader
            and not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
            and not input_def.has_default_value
            and not top_level_input_provided
        ):
            raise DagsterInvalidInvocationError(
                f"Attempted to invoke execute_in_process for '{job_name}' without specifying an"
                f" input_value for input '{top_level_input_name}', but downstream input"
                f" {input_def.name} of op '{cur_node_handle}' has no other way of being"
                " loaded."
            )

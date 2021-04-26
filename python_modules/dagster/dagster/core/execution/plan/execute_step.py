from collections import defaultdict
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union, cast

from dagster import check
from dagster.core.definitions import (
    AssetKey,
    AssetMaterialization,
    ExpectationResult,
    Failure,
    Materialization,
    Output,
    OutputDefinition,
    RetryRequested,
    SolidDefinition,
    TypeCheck,
)
from dagster.core.definitions.events import (
    AssetLineageInfo,
    DynamicOutput,
    EventMetadataEntry,
    PartitionMetadataEntry,
)
from dagster.core.errors import (
    DagsterExecutionHandleOutputError,
    DagsterExecutionStepExecutionError,
    DagsterInvariantViolationError,
    DagsterStepOutputNotFoundError,
    DagsterTypeCheckDidNotPass,
    DagsterTypeCheckError,
    DagsterTypeMaterializationError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.output import OutputContext
from dagster.core.execution.context.system import StepExecutionContext, TypeCheckContext
from dagster.core.execution.plan.compute import execute_core_compute
from dagster.core.execution.plan.inputs import StepInputData
from dagster.core.execution.plan.objects import StepSuccessData, TypeCheckData
from dagster.core.execution.plan.outputs import StepOutputData, StepOutputHandle
from dagster.core.execution.resolve_versions import resolve_step_output_versions
from dagster.core.storage.intermediate_storage import IntermediateStorageAdapter
from dagster.core.storage.io_manager import IOManager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.types.dagster_type import DagsterType, DagsterTypeKind
from dagster.utils import ensure_gen, iterate_with_context
from dagster.utils.backcompat import experimental_functionality_warning
from dagster.utils.timing import time_execution_scope

from .compute import SolidOutputUnion


def _step_output_error_checked_user_event_sequence(
    step_context: StepExecutionContext, user_event_sequence: Iterator[SolidOutputUnion]
) -> Iterator[SolidOutputUnion]:
    """
    Process the event sequence to check for invariant violations in the event
    sequence related to Output events emitted from the compute_fn.

    This consumes and emits an event sequence.
    """
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.generator_param(user_event_sequence, "user_event_sequence")

    step = step_context.step
    output_names = list([output_def.name for output_def in step.step_outputs])
    seen_outputs: Set[str] = set()
    seen_mapping_keys: Dict[str, Set[str]] = defaultdict(set)

    for user_event in user_event_sequence:
        if not isinstance(user_event, (Output, DynamicOutput)):
            yield user_event
            continue

        # do additional processing on Outputs
        output = user_event
        if not step.has_step_output(output.output_name):
            raise DagsterInvariantViolationError(
                'Core compute for solid "{handle}" returned an output '
                '"{output.output_name}" that does not exist. The available '
                "outputs are {output_names}".format(
                    handle=str(step.solid_handle), output=output, output_names=output_names
                )
            )

        step_output = step.step_output_named(output.output_name)
        output_def = step_context.pipeline_def.get_solid(step_output.solid_handle).output_def_named(
            step_output.name
        )

        if isinstance(output, Output):
            if output.output_name in seen_outputs:
                raise DagsterInvariantViolationError(
                    'Compute for solid "{handle}" returned an output '
                    '"{output.output_name}" multiple times'.format(
                        handle=str(step.solid_handle), output=output
                    )
                )

            if output_def.is_dynamic:
                raise DagsterInvariantViolationError(
                    f'Compute for solid "{step.solid_handle}" for output "{output.output_name}" '
                    "defined as dynamic must yield DynamicOutput, got Output."
                )
        else:
            if not output_def.is_dynamic:
                raise DagsterInvariantViolationError(
                    f'Compute for solid "{step.solid_handle}" yielded a DynamicOutput, '
                    "but did not use DynamicOutputDefinition."
                )
            if output.mapping_key in seen_mapping_keys[output.output_name]:
                raise DagsterInvariantViolationError(
                    f'Compute for solid "{step.solid_handle}" yielded a DynamicOutput with '
                    f'mapping_key "{output.mapping_key}" multiple times.'
                )
            seen_mapping_keys[output.output_name].add(output.mapping_key)

        yield output
        seen_outputs.add(output.output_name)

    for step_output in step.step_outputs:
        step_output_def = step_context.solid_def.output_def_named(step_output.name)
        if not step_output_def.name in seen_outputs and not step_output_def.optional:
            if step_output_def.dagster_type.kind == DagsterTypeKind.NOTHING:
                step_context.log.info(
                    'Emitting implicit Nothing for output "{output}" on solid {solid}'.format(
                        output=step_output_def.name, solid={str(step.solid_handle)}
                    )
                )
                yield Output(output_name=step_output_def.name, value=None)
            elif not step_output_def.is_dynamic:
                raise DagsterStepOutputNotFoundError(
                    'Core compute for solid "{handle}" did not return an output '
                    'for non-optional output "{step_output_def.name}"'.format(
                        handle=str(step.solid_handle), step_output_def=step_output_def
                    ),
                    step_key=step.key,
                    output_name=step_output_def.name,
                )


def _do_type_check(context: TypeCheckContext, dagster_type: DagsterType, value: Any) -> TypeCheck:
    type_check = dagster_type.type_check(context, value)
    if not isinstance(type_check, TypeCheck):
        return TypeCheck(
            success=False,
            description=(
                "Type checks must return TypeCheck. Type check for type {type_name} returned "
                "value of type {return_type} when checking runtime value of type {dagster_type}."
            ).format(
                type_name=dagster_type.display_name,
                return_type=type(type_check),
                dagster_type=type(value),
            ),
        )
    return type_check


def _create_step_input_event(
    step_context: StepExecutionContext, input_name: str, type_check: TypeCheck, success: bool
) -> DagsterEvent:
    return DagsterEvent.step_input_event(
        step_context,
        StepInputData(
            input_name=input_name,
            type_check_data=TypeCheckData(
                success=success,
                label=input_name,
                description=type_check.description if type_check else None,
                metadata_entries=type_check.metadata_entries if type_check else [],
            ),
        ),
    )


def _type_checked_event_sequence_for_input(
    step_context: StepExecutionContext, input_name: str, input_value: Any
) -> Iterator[DagsterEvent]:
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.str_param(input_name, "input_name")

    step_input = step_context.step.step_input_named(input_name)
    input_def = step_input.source.get_input_def(step_context.pipeline_def)
    dagster_type = input_def.dagster_type
    with user_code_error_boundary(
        DagsterTypeCheckError,
        lambda: (
            f'Error occurred while type-checking input "{input_name}" of solid '
            f'"{str(step_context.step.solid_handle)}", with Python type {type(input_value)} and '
            f"Dagster type {dagster_type.display_name}"
        ),
    ):
        type_check = _do_type_check(step_context.for_type(dagster_type), dagster_type, input_value)

    yield _create_step_input_event(
        step_context, input_name, type_check=type_check, success=type_check.success
    )

    if not type_check.success:
        raise DagsterTypeCheckDidNotPass(
            description=(
                f'Type check failed for step input "{input_name}" - '
                f'expected type "{dagster_type.display_name}". '
                f"Description: {type_check.description}."
            ),
            metadata_entries=type_check.metadata_entries,
            dagster_type=dagster_type,
        )


def _type_check_output(
    step_context: StepExecutionContext,
    step_output_handle: StepOutputHandle,
    output: Any,
    version: Optional[str],
) -> Iterator[DagsterEvent]:
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.inst_param(output, "output", (Output, DynamicOutput))

    step_output = step_context.step.step_output_named(output.output_name)
    step_output_def = step_context.solid_def.output_def_named(step_output.name)

    dagster_type = step_output_def.dagster_type
    with user_code_error_boundary(
        DagsterTypeCheckError,
        lambda: (
            f'Error occurred while type-checking output "{output.output_name}" of solid '
            f'"{str(step_context.step.solid_handle)}", with Python type {type(output.value)} and '
            f"Dagster type {dagster_type.display_name}"
        ),
    ):
        type_check = _do_type_check(step_context.for_type(dagster_type), dagster_type, output.value)

    yield DagsterEvent.step_output_event(
        step_context=step_context,
        step_output_data=StepOutputData(
            step_output_handle=step_output_handle,
            type_check_data=TypeCheckData(
                success=type_check.success,
                label=step_output_handle.output_name,
                description=type_check.description if type_check else None,
                metadata_entries=type_check.metadata_entries if type_check else [],
            ),
            version=version,
            metadata_entries=[
                entry for entry in output.metadata_entries if isinstance(entry, EventMetadataEntry)
            ],
        ),
    )

    if not type_check.success:
        raise DagsterTypeCheckDidNotPass(
            description='Type check failed for step output "{output_name}" - expected type "{dagster_type}".'.format(
                output_name=output.output_name,
                dagster_type=dagster_type.display_name,
            ),
            metadata_entries=type_check.metadata_entries,
            dagster_type=dagster_type,
        )


def core_dagster_event_sequence_for_step(
    step_context: StepExecutionContext, prior_attempt_count: int
) -> Iterator[DagsterEvent]:
    """
    Execute the step within the step_context argument given the in-memory
    events. This function yields a sequence of DagsterEvents, but without
    catching any exceptions that have bubbled up during the computation
    of the step.
    """
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.int_param(prior_attempt_count, "prior_attempt_count")
    if prior_attempt_count > 0:
        yield DagsterEvent.step_restarted_event(step_context, prior_attempt_count)
    else:
        yield DagsterEvent.step_start_event(step_context)

    inputs = {}
    input_lineage = []

    for step_input in step_context.step.step_inputs:
        input_def = step_input.source.get_input_def(step_context.pipeline_def)
        dagster_type = input_def.dagster_type

        if dagster_type.kind == DagsterTypeKind.NOTHING:
            continue

        input_lineage.extend(step_input.source.get_asset_lineage(step_context))

        for event_or_input_value in ensure_gen(step_input.source.load_input_object(step_context)):
            if isinstance(event_or_input_value, DagsterEvent):
                yield event_or_input_value
            else:
                check.invariant(step_input.name not in inputs)
                inputs[step_input.name] = event_or_input_value

    for input_name, input_value in inputs.items():
        for evt in check.generator(
            _type_checked_event_sequence_for_input(step_context, input_name, input_value)
        ):
            yield evt

    input_lineage = _dedup_asset_lineage(input_lineage)
    with time_execution_scope() as timer_result:
        user_event_sequence = check.generator(
            _user_event_sequence_for_step_compute_fn(step_context, inputs)
        )

        # It is important for this loop to be indented within the
        # timer block above in order for time to be recorded accurately.
        for user_event in check.generator(
            _step_output_error_checked_user_event_sequence(step_context, user_event_sequence)
        ):

            if isinstance(user_event, (Output, DynamicOutput)):
                for evt in _type_check_and_store_output(step_context, user_event, input_lineage):
                    yield evt
            # for now, I'm ignoring AssetMaterializations yielded manually, but we might want
            # to do something with these in the above path eventually
            elif isinstance(user_event, (AssetMaterialization, Materialization)):
                yield DagsterEvent.asset_materialization(step_context, user_event, input_lineage)
            elif isinstance(user_event, ExpectationResult):
                yield DagsterEvent.step_expectation_result(step_context, user_event)
            else:
                check.failed(
                    "Unexpected event {event}, should have been caught earlier".format(
                        event=user_event
                    )
                )

    yield DagsterEvent.step_success_event(
        step_context, StepSuccessData(duration_ms=timer_result.millis)
    )


def _type_check_and_store_output(
    step_context: StepExecutionContext,
    output: Union[DynamicOutput, Output],
    input_lineage: List[AssetLineageInfo],
) -> Iterator[DagsterEvent]:

    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.inst_param(output, "output", (Output, DynamicOutput))
    check.list_param(input_lineage, "input_lineage", AssetLineageInfo)

    mapping_key = output.mapping_key if isinstance(output, DynamicOutput) else None

    step_output_handle = StepOutputHandle(
        step_key=step_context.step.key, output_name=output.output_name, mapping_key=mapping_key
    )

    # If we are executing using the execute_in_process API, then we allow for the outputs of solids
    # to be directly captured to a dictionary after they are computed.
    if step_context.output_capture is not None:
        step_context.output_capture[step_output_handle] = output.value

    version = (
        resolve_step_output_versions(
            step_context.pipeline_def, step_context.execution_plan, step_context.environment_config
        ).get(step_output_handle)
        if MEMOIZED_RUN_TAG in step_context.pipeline.get_definition().tags
        else None
    )

    for output_event in _type_check_output(step_context, step_output_handle, output, version):
        yield output_event

    for evt in _store_output(step_context, step_output_handle, output, input_lineage):
        yield evt

    for evt in _create_type_materializations(step_context, output.output_name, output.value):
        yield evt


def _asset_key_and_partitions_for_output(
    output_context: OutputContext,
    output_def: OutputDefinition,
    output_manager: IOManager,
) -> Tuple[Optional[AssetKey], Set[str]]:

    manager_asset_key = output_manager.get_output_asset_key(output_context)

    if output_def.is_asset:
        if manager_asset_key is not None:
            solid_def = cast(SolidDefinition, output_context.solid_def)
            raise DagsterInvariantViolationError(
                f'Both the OutputDefinition and the IOManager of output "{output_def.name}" on '
                f'solid "{solid_def.name}" associate it with an asset. Either remove '
                "the asset_key parameter on the OutputDefinition or use an IOManager that does not "
                "specify an AssetKey in its get_output_asset_key() function."
            )
        return (
            output_def.get_asset_key(output_context),
            output_def.get_asset_partitions(output_context) or set(),
        )
    elif manager_asset_key:
        return manager_asset_key, output_manager.get_output_asset_partitions(output_context)

    return None, set()


def _dedup_asset_lineage(asset_lineage: List[AssetLineageInfo]) -> List[AssetLineageInfo]:
    """Method to remove duplicate specifications of the same Asset/Partition pair from the lineage
    information. Duplicates can occur naturally when calculating transitive dependencies from solids
    with multiple Outputs, which in turn have multiple Inputs (because each Output of the solid will
    inherit all dependencies from all of the solid Inputs).
    """
    key_partition_mapping: Dict[AssetKey, Set[str]] = defaultdict(set)

    for lineage_info in asset_lineage:
        if not lineage_info.partitions:
            key_partition_mapping[lineage_info.asset_key] |= set()
        for partition in lineage_info.partitions:
            key_partition_mapping[lineage_info.asset_key].add(partition)
    return [
        AssetLineageInfo(asset_key=asset_key, partitions=partitions)
        for asset_key, partitions in key_partition_mapping.items()
    ]


def _get_output_asset_materializations(
    asset_key: AssetKey,
    asset_partitions: Set[str],
    output: Union[Output, DynamicOutput],
    output_def: OutputDefinition,
    io_manager_metadata_entries: List[Union[EventMetadataEntry, PartitionMetadataEntry]],
) -> Iterator[AssetMaterialization]:

    all_metadata = output.metadata_entries + io_manager_metadata_entries

    if asset_partitions:
        metadata_mapping: Dict[str, List[str]] = {partition: [] for partition in asset_partitions}
        for entry in all_metadata:
            # if you target a given entry at a partition, only apply it to the requested partition
            # otherwise, apply it to all partitions
            if isinstance(entry, PartitionMetadataEntry):
                if entry.partition not in asset_partitions:
                    raise DagsterInvariantViolationError(
                        f"Output {output_def.name} associated a metadata entry ({entry}) with the partition "
                        f"`{entry.partition}`, which is not one of the declared partition mappings ({asset_partitions})."
                    )
                metadata_mapping[entry.partition].append(entry.entry)
            else:
                for partition in metadata_mapping.keys():
                    metadata_mapping[partition].append(entry)

        for partition in asset_partitions:
            yield AssetMaterialization(
                asset_key=asset_key,
                partition=partition,
                metadata_entries=metadata_mapping[partition],
            )
    else:
        for entry in all_metadata:
            if isinstance(entry, PartitionMetadataEntry):
                raise DagsterInvariantViolationError(
                    f"Output {output_def.name} got a PartitionMetadataEntry ({entry}), but "
                    "is not associated with any specific partitions."
                )
        yield AssetMaterialization(asset_key=asset_key, metadata_entries=all_metadata)


def _store_output(
    step_context: StepExecutionContext,
    step_output_handle: StepOutputHandle,
    output: Union[Output, DynamicOutput],
    input_lineage: List[AssetLineageInfo],
) -> Iterator[DagsterEvent]:

    output_def = step_context.solid_def.output_def_named(step_output_handle.output_name)
    output_manager = step_context.get_io_manager(step_output_handle)
    output_context = step_context.get_output_context(step_output_handle)

    with user_code_error_boundary(
        DagsterExecutionHandleOutputError,
        control_flow_exceptions=[Failure, RetryRequested],
        msg_fn=lambda: (
            f'Error occurred while handling output "{output_context.name}" of '
            f'step "{step_context.step.key}":'
        ),
        step_key=step_context.step.key,
        output_name=output_context.name,
    ):
        handle_output_res = output_manager.handle_output(output_context, output.value)

    manager_materializations = []
    manager_metadata_entries = []
    if handle_output_res is not None:
        for elt in ensure_gen(handle_output_res):
            if isinstance(elt, AssetMaterialization):
                manager_materializations.append(elt)
            elif isinstance(elt, (EventMetadataEntry, PartitionMetadataEntry)):
                experimental_functionality_warning(
                    "Yielding metadata from an IOManager's handle_output() function"
                )
                manager_metadata_entries.append(elt)
            else:
                raise DagsterInvariantViolationError(
                    f"IO manager on output {output_def.name} has returned "
                    f"value {elt} of type {type(elt).__name__}. The return type can only be "
                    "one of AssetMaterialization, EventMetadataEntry, PartitionMetadataEntry."
                )

    # do not alter explicitly created AssetMaterializations
    for materialization in manager_materializations:
        yield DagsterEvent.asset_materialization(step_context, materialization, input_lineage)

    asset_key, partitions = _asset_key_and_partitions_for_output(
        output_context, output_def, output_manager
    )
    if asset_key:
        for materialization in _get_output_asset_materializations(
            asset_key,
            partitions,
            output,
            output_def,
            manager_metadata_entries,
        ):
            yield DagsterEvent.asset_materialization(step_context, materialization, input_lineage)

    yield DagsterEvent.handled_output(
        step_context,
        output_name=step_output_handle.output_name,
        manager_key=output_def.io_manager_key,
        message_override=f'Handled input "{step_output_handle.output_name}" using intermediate storage'
        if isinstance(output_manager, IntermediateStorageAdapter)
        else None,
        metadata_entries=[
            entry for entry in manager_metadata_entries if isinstance(entry, EventMetadataEntry)
        ],
    )


def _create_type_materializations(
    step_context: StepExecutionContext, output_name: str, value: Any
) -> Iterator[DagsterEvent]:
    """If the output has any dagster type materializers, runs them."""

    step = step_context.step
    current_handle = step.solid_handle

    # check for output mappings at every point up the composition hierarchy
    while current_handle:
        solid_config = step_context.environment_config.solids.get(current_handle.to_string())
        current_handle = current_handle.parent

        if solid_config is None:
            continue

        for output_spec in solid_config.outputs.type_materializer_specs:
            check.invariant(len(output_spec) == 1)
            config_output_name, output_spec = list(output_spec.items())[0]
            if config_output_name == output_name:
                step_output = step.step_output_named(output_name)
                with user_code_error_boundary(
                    DagsterTypeMaterializationError,
                    msg_fn=lambda: (
                        "Error occurred during output materialization:"
                        f'\n    output name: "{output_name}"'
                        f'\n    solid invocation: "{step_context.solid.name}"'
                        f'\n    solid definition: "{step_context.solid_def.name}"'
                    ),
                ):
                    output_def = step_context.solid_def.output_def_named(step_output.name)
                    dagster_type = output_def.dagster_type
                    materializations = dagster_type.materializer.materialize_runtime_values(
                        step_context, output_spec, value
                    )

                for materialization in materializations:
                    if not isinstance(materialization, (AssetMaterialization, Materialization)):
                        raise DagsterInvariantViolationError(
                            (
                                "materialize_runtime_values on type {type_name} has returned "
                                "value {value} of type {python_type}. You must return an "
                                "AssetMaterialization."
                            ).format(
                                type_name=dagster_type.display_name,
                                value=repr(materialization),
                                python_type=type(materialization).__name__,
                            )
                        )

                    yield DagsterEvent.asset_materialization(step_context, materialization)


def _user_event_sequence_for_step_compute_fn(
    step_context: StepExecutionContext, evaluated_inputs: Dict[str, Any]
) -> Iterator[SolidOutputUnion]:
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.dict_param(evaluated_inputs, "evaluated_inputs", key_type=str)

    gen = execute_core_compute(
        step_context,
        evaluated_inputs,
        step_context.solid_def.compute_fn,
    )

    for event in iterate_with_context(
        lambda: user_code_error_boundary(
            DagsterExecutionStepExecutionError,
            control_flow_exceptions=[Failure, RetryRequested],
            msg_fn=lambda: f'Error occurred while executing solid "{step_context.solid.name}":',
            step_key=step_context.step.key,
            solid_def_name=step_context.solid_def.name,
            solid_name=step_context.solid.name,
        ),
        gen,
    ):
        yield event

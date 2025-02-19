import inspect
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Optional, Union, cast

from typing_extensions import TypedDict

import dagster._check as check
from dagster._core.definitions import (
    AssetCheckEvaluation,
    AssetCheckSeverity,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    ExpectationResult,
    Output,
    OutputDefinition,
    TypeCheck,
)
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_version import (
    CODE_VERSION_TAG,
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
    DEFAULT_DATA_VERSION,
    NULL_EVENT_POINTER,
    DataVersion,
    compute_logical_data_version,
    get_input_data_version_tag,
    get_input_event_pointer_tag,
)
from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction
from dagster._core.definitions.events import DynamicOutput
from dagster._core.definitions.metadata import MetadataValue, normalize_metadata
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    get_tags_from_multi_partition_key,
)
from dagster._core.definitions.result import AssetResult
from dagster._core.definitions.source_asset import SYSTEM_METADATA_KEY_SOURCE_ASSET_OBSERVATION
from dagster._core.errors import (
    DagsterAssetCheckFailedError,
    DagsterExecutionHandleOutputError,
    DagsterInvariantViolationError,
    DagsterStepOutputNotFoundError,
    DagsterTypeCheckDidNotPass,
    DagsterTypeCheckError,
    user_code_error_boundary,
)
from dagster._core.events import DagsterEvent, DagsterEventBatchMetadata, generate_event_batch_id
from dagster._core.execution.context.compute import enter_execution_context
from dagster._core.execution.context.output import OutputContext
from dagster._core.execution.context.system import StepExecutionContext, TypeCheckContext
from dagster._core.execution.plan.compute import OpOutputUnion, execute_core_compute
from dagster._core.execution.plan.compute_generator import create_op_compute_wrapper
from dagster._core.execution.plan.inputs import StepInputData
from dagster._core.execution.plan.objects import StepSuccessData, TypeCheckData
from dagster._core.execution.plan.outputs import StepOutputData, StepOutputHandle
from dagster._core.execution.plan.utils import op_execution_error_boundary
from dagster._core.storage.tags import BACKFILL_ID_TAG
from dagster._core.types.dagster_type import DagsterType
from dagster._utils import iterate_with_context
from dagster._utils.timing import time_execution_scope
from dagster._utils.warnings import beta_warning, disable_dagster_warnings


class AssetResultOutput(Output):
    """This is a marker subclass that represents an Output that was produced from an AssetResult."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def _process_asset_results_to_events(
    step_context: StepExecutionContext,
    user_event_sequence: Iterator[OpOutputUnion],
) -> Iterator[OpOutputUnion]:
    """Handle converting MaterializeResult (& AssetCheckResult soon) to their appropriate events.

    MaterializeResults get converted to an Output event, which is later use to derive an AssetMaterialization.

    AssetCheckResult get converted to two events:
     - An Output, which allows downstream steps to depend on it
     - An AssetCheckEvaluation, which combines the check result with information from the context
         to create a full picture of the asset check's evaluation.
    """
    for user_event in user_event_sequence:
        yield from _process_user_event(step_context, user_event)


def _process_user_event(
    step_context: StepExecutionContext, user_event: OpOutputUnion
) -> Iterator[OpOutputUnion]:
    if isinstance(user_event, AssetResult):
        assets_def = _get_assets_def_for_step(step_context, user_event)
        asset_key = _resolve_asset_result_asset_key(user_event, assets_def)
        output_name = assets_def.get_output_name_for_asset_key(asset_key)

        for check_result in user_event.check_results or []:
            yield from _process_user_event(step_context, check_result)

        with disable_dagster_warnings():
            yield AssetResultOutput(
                value=None,
                output_name=output_name,
                metadata=user_event.metadata,
                data_version=user_event.data_version,
                tags=user_event.tags,
            )
    elif isinstance(user_event, AssetCheckResult):
        asset_check_evaluation = user_event.to_asset_check_evaluation(step_context)
        spec = check.not_none(
            step_context.job_def.asset_layer.asset_graph.get_check_spec(
                asset_check_evaluation.asset_check_key
            ),
            "If we were able to create an AssetCheckEvaluation from the AssetCheckResult, then"
            " there should be a spec for the check",
        )

        output_name = step_context.job_def.asset_layer.get_output_name_for_asset_check(
            asset_check_evaluation.asset_check_key
        )
        output = Output(value=None, output_name=output_name)

        yield asset_check_evaluation

        if (
            not asset_check_evaluation.passed
            and asset_check_evaluation.severity == AssetCheckSeverity.ERROR
            and spec.blocking
        ):
            raise DagsterAssetCheckFailedError(
                f"Blocking check '{spec.name}' for asset '{spec.asset_key.to_user_string()}' failed with"
                " ERROR severity."
            )
        yield output
    else:
        yield user_event


def _get_assets_def_for_step(
    step_context: StepExecutionContext, user_event: OpOutputUnion
) -> AssetsDefinition:
    assets_def = step_context.job_def.asset_layer.assets_def_for_node(step_context.node_handle)
    if not assets_def:
        raise DagsterInvariantViolationError(
            f"{user_event.__class__.__name__} is only valid within asset computations, no backing"
            " AssetsDefinition found."
        )
    return assets_def


def _resolve_asset_result_asset_key(
    asset_result: AssetResult, assets_def: AssetsDefinition
) -> AssetKey:
    if asset_result.asset_key:
        return asset_result.asset_key
    else:
        if len(assets_def.keys) != 1:
            raise DagsterInvariantViolationError(
                f"{asset_result.__class__.__name__} did not include asset_key and it can not be inferred."
                f" Specify which asset_key, options are: {assets_def.keys}."
            )
        return assets_def.key


def _step_output_error_checked_user_event_sequence(
    step_context: StepExecutionContext, user_event_sequence: Iterator[OpOutputUnion]
) -> Iterator[OpOutputUnion]:
    """Process the event sequence to check for invariant violations in the event
    sequence related to Output events emitted from the compute_fn.

    This consumes and emits an event sequence.
    """
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.iterator_param(user_event_sequence, "user_event_sequence")

    step = step_context.step
    op_label = step_context.describe_op()
    output_names = list([output_def.name for output_def in step.step_outputs])
    selected_output_names = step_context.selected_output_names

    for user_event in user_event_sequence:
        if not isinstance(user_event, (Output, DynamicOutput)):
            yield user_event
            continue

        # do additional processing on Outputs
        output = user_event
        if not step.has_step_output(cast(str, output.output_name)):
            raise DagsterInvariantViolationError(
                f'Core compute for {op_label} returned an output "{output.output_name}" that does '
                f"not exist. The available outputs are {output_names}"
            )

        if output.output_name not in selected_output_names:
            raise DagsterInvariantViolationError(
                f'Core compute for {op_label} returned an output "{output.output_name}" that is '
                f"not selected. The selected outputs are {selected_output_names}"
            )

        step_output = step.step_output_named(cast(str, output.output_name))
        output_def = step_context.job_def.get_node(step_output.node_handle).output_def_named(
            step_output.name
        )

        if isinstance(output, Output):
            if step_context.has_seen_output(output.output_name):
                raise DagsterInvariantViolationError(
                    f'Compute for {op_label} returned an output "{output.output_name}" multiple '
                    "times"
                )

            if output_def.is_dynamic:
                raise DagsterInvariantViolationError(
                    f'Compute for {op_label} for output "{output.output_name}" defined as dynamic '
                    "must yield DynamicOutput, got Output."
                )

            # For any output associated with an asset, make sure that none of its dependent assets
            # have already been yielded. If this condition (outputs yielded in topological order) is
            # not satisfied, automatic data version computation can yield wrong results.
            #
            # We look for dependent keys that have already been yielded rather than dependency keys
            # that have not yet been yielded. This is because we don't always know which
            # dependencies will actually be computed within the step. If A depends on B, it is
            # possible that a cached version of B will be used and B will never be yielded. In
            # contrast, if both A and B are yielded, A should never precede B.
            asset_layer = step_context.job_def.asset_layer
            node_handle = step_context.node_handle
            asset_key = asset_layer.asset_key_for_output(node_handle, output_def.name)
            if asset_key is not None and asset_key in asset_layer.asset_keys_for_node(node_handle):
                asset_node = asset_layer.get(asset_key)
                assets_def = asset_node.assets_def
                all_dependent_keys = asset_node.child_keys
                step_local_asset_keys = step_context.get_output_asset_keys()
                step_local_dependent_keys = all_dependent_keys & step_local_asset_keys
                for dependent_key in step_local_dependent_keys:
                    output_name = assets_def.get_output_name_for_asset_key(dependent_key)
                    # Need to skip self-dependent assets (possible with partitions)
                    self_dep = dependent_key in asset_node.parent_keys
                    if not self_dep and step_context.has_seen_output(output_name):
                        raise DagsterInvariantViolationError(
                            f'Asset "{dependent_key.to_user_string()}" was yielded before its'
                            f' dependency "{asset_key.to_user_string()}".Multiassets'
                            " yielding multiple asset outputs must yield them in topological"
                            " order."
                        )

            step_context.observe_output(output.output_name)

            metadata = step_context.get_output_metadata(output.output_name)
            with disable_dagster_warnings():
                output = output.with_metadata(
                    metadata={**output.metadata, **normalize_metadata(metadata or {})}
                )
        else:
            if not output_def.is_dynamic:
                raise DagsterInvariantViolationError(
                    f"Compute for {op_label} yielded a DynamicOutput, but did not use "
                    "DynamicOutputDefinition."
                )
            if step_context.has_seen_output(output.output_name, output.mapping_key):
                raise DagsterInvariantViolationError(
                    f"Compute for {op_label} yielded a DynamicOutput with mapping_key "
                    f'"{output.mapping_key}" multiple times.'
                )
            step_context.observe_output(output.output_name, output.mapping_key)
            metadata = step_context.get_output_metadata(
                output.output_name, mapping_key=output.mapping_key
            )
            output = DynamicOutput(
                value=output.value,
                output_name=output.output_name,
                metadata={**output.metadata, **normalize_metadata(metadata or {})},
                mapping_key=output.mapping_key,
            )

        yield output

    for step_output in step.step_outputs:
        step_output_def = step_context.op_def.output_def_named(step_output.name)
        if not step_context.has_seen_output(step_output_def.name) and not step_output_def.optional:
            asset_layer = step_context.job_def.asset_layer
            asset_key = asset_layer.asset_key_for_output(
                step_context.node_handle, step_output_def.name
            )
            # We require explicitly returned/yielded for asset observations
            is_observable_asset = asset_key is not None and asset_layer.get(asset_key).is_observable

            if step_output_def.dagster_type.is_nothing and not is_observable_asset:
                if step_output.name in selected_output_names:
                    step_context.log.info(
                        f'Emitting implicit Nothing for output "{step_output_def.name}" on {op_label}'
                    )
                    yield Output(output_name=step_output_def.name, value=None)
            elif not step_output_def.is_dynamic:
                raise DagsterStepOutputNotFoundError(
                    f"Core compute for {op_label} did not return an output for non-optional "
                    f'output "{step_output_def.name}"',
                    step_key=step.key,
                    output_name=step_output_def.name,
                )


def do_type_check(context: TypeCheckContext, dagster_type: DagsterType, value: Any) -> TypeCheck:
    type_check = dagster_type.type_check(context, value)
    if not isinstance(type_check, TypeCheck):
        return TypeCheck(
            success=False,
            description=(
                f"Type checks must return TypeCheck. Type check for type {dagster_type.display_name} returned "
                f"value of type {type(type_check)} when checking runtime value of type {type(value)}."
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
                metadata=type_check.metadata if type_check else {},
            ),
        ),
    )


def _type_checked_event_sequence_for_input(
    step_context: StepExecutionContext,
    input_name: str,
    input_value: Any,
) -> Iterator[DagsterEvent]:
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.str_param(input_name, "input_name")

    step_input = step_context.step.step_input_named(input_name)
    input_def = step_context.op_def.input_def_named(step_input.name)

    check.invariant(
        input_def.name == input_name,
        f"InputDefinition name does not match, expected {input_name} got {input_def.name}",
    )

    dagster_type = input_def.dagster_type
    type_check_context = step_context.for_type(dagster_type)
    input_type = type(input_value)
    op_label = step_context.describe_op()

    with user_code_error_boundary(
        DagsterTypeCheckError,
        lambda: (
            f'Error occurred while type-checking input "{input_name}" of {op_label}, with Python'
            f" type {input_type} and Dagster type {dagster_type.display_name}"
        ),
        log_manager=type_check_context.log,
    ):
        type_check = do_type_check(type_check_context, dagster_type, input_value)

    yield _create_step_input_event(
        step_context, input_name, type_check=type_check, success=type_check.success
    )

    if not type_check.success:
        raise DagsterTypeCheckDidNotPass(
            description=(
                f'Type check failed for step input "{input_name}" - '
                f'expected type "{dagster_type.display_name}". '
                f"Description: {type_check.description}"
            ),
            metadata=type_check.metadata,
            dagster_type=dagster_type,
        )


def _type_check_output(
    step_context: StepExecutionContext,
    step_output_handle: StepOutputHandle,
    output: Any,
) -> Iterator[DagsterEvent]:
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.inst_param(output, "output", (Output, DynamicOutput))

    step_output = step_context.step.step_output_named(output.output_name)
    step_output_def = step_context.op_def.output_def_named(step_output.name)

    dagster_type = step_output_def.dagster_type
    type_check_context = step_context.for_type(dagster_type)
    op_label = step_context.describe_op()
    output_type = type(output.value)

    with user_code_error_boundary(
        DagsterTypeCheckError,
        lambda: (
            f'Error occurred while type-checking output "{output.output_name}" of {op_label}, with'
            f" Python type {output_type} and Dagster type {dagster_type.display_name}"
        ),
        log_manager=type_check_context.log,
    ):
        type_check = do_type_check(type_check_context, dagster_type, output.value)

    yield DagsterEvent.step_output_event(
        step_context=step_context,
        step_output_data=StepOutputData(
            step_output_handle=step_output_handle,
            type_check_data=TypeCheckData(
                success=type_check.success,
                label=step_output_handle.output_name,
                description=type_check.description if type_check else None,
                metadata=type_check.metadata if type_check else {},
            ),
            metadata=output.metadata,
        ),
    )

    if not type_check.success:
        raise DagsterTypeCheckDidNotPass(
            description=(
                f'Type check failed for step output "{output.output_name}" - '
                f'expected type "{dagster_type.display_name}". '
                f"Description: {type_check.description}"
            ),
            metadata=type_check.metadata,
            dagster_type=dagster_type,
        )


def core_dagster_event_sequence_for_step(
    step_context: StepExecutionContext,
) -> Iterator[DagsterEvent]:
    """Execute the step within the step_context argument given the in-memory
    events. This function yields a sequence of DagsterEvents, but without
    catching any exceptions that have bubbled up during the computation
    of the step.
    """
    check.inst_param(step_context, "step_context", StepExecutionContext)

    if step_context.previous_attempt_count > 0:
        yield DagsterEvent.step_restarted_event(step_context, step_context.previous_attempt_count)
    else:
        yield DagsterEvent.step_start_event(step_context)

    with (
        time_execution_scope() as timer_result,
        enter_execution_context(step_context) as compute_context,
    ):
        inputs = {}

        if step_context.is_sda_step:
            step_context.fetch_external_input_asset_version_info()

        for step_input in step_context.step.step_inputs:
            input_def = step_context.op_def.input_def_named(step_input.name)
            dagster_type = input_def.dagster_type

            if dagster_type.is_nothing:
                continue

            for event_or_input_value in step_input.source.load_input_object(
                step_context, input_def
            ):
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

        # The core execution loop expects a compute generator in a specific format: a generator that
        # takes a context and dictionary of inputs as input, yields output events. If an op definition
        # was generated from the @op decorator, then compute_fn needs to be coerced
        # into this format. If the op definition was created directly, then it is expected that the
        # compute_fn is already in this format.
        if isinstance(step_context.op_def.compute_fn, DecoratedOpFunction):
            core_gen = create_op_compute_wrapper(step_context.op_def)
        else:
            core_gen = step_context.op_def.compute_fn

        user_event_sequence = execute_core_compute(
            step_context,
            inputs,
            core_gen,
            compute_context,
        )

        # It is important for this loop to be indented within the
        # timer block above in order for time to be recorded accurately.
        for user_event in _step_output_error_checked_user_event_sequence(
            step_context,
            _process_asset_results_to_events(step_context, user_event_sequence),
        ):
            if isinstance(user_event, DagsterEvent):
                yield user_event
            elif isinstance(user_event, (Output, DynamicOutput)):
                for evt in _type_check_and_store_output(step_context, user_event):
                    yield evt
            # for now, I'm ignoring AssetMaterializations yielded manually, but we might want
            # to do something with these in the above path eventually
            elif isinstance(user_event, AssetMaterialization):
                yield DagsterEvent.asset_materialization(step_context, user_event)
            elif isinstance(user_event, AssetObservation):
                yield DagsterEvent.asset_observation(step_context, user_event)
            elif isinstance(user_event, AssetCheckEvaluation):
                yield DagsterEvent.asset_check_evaluation(step_context, user_event)
            elif isinstance(user_event, ExpectationResult):
                yield DagsterEvent.step_expectation_result(step_context, user_event)
            else:
                check.failed(f"Unexpected event {user_event}, should have been caught earlier")

    yield DagsterEvent.step_success_event(
        step_context, StepSuccessData(duration_ms=timer_result.millis)
    )


def _type_check_and_store_output(
    step_context: StepExecutionContext, output: Union[DynamicOutput, Output]
) -> Iterator[DagsterEvent]:
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.inst_param(output, "output", (Output, DynamicOutput))

    mapping_key = output.mapping_key if isinstance(output, DynamicOutput) else None

    step_output_handle = StepOutputHandle(
        step_key=step_context.step.key, output_name=output.output_name, mapping_key=mapping_key
    )

    # If we are executing using the execute_in_process API, then we allow for the outputs of ops
    # to be directly captured to a dictionary after they are computed.
    if step_context.output_capture is not None:
        step_context.output_capture[step_output_handle] = output.value
    # capture output at the step level for threading the computed output values to hook context
    if (
        step_context.step_output_capture is not None
        and step_context.step_output_metadata_capture is not None
    ):
        step_context.step_output_capture[step_output_handle] = output.value
        step_context.step_output_metadata_capture[step_output_handle] = output.metadata

    yield from _type_check_output(step_context, step_output_handle, output)

    yield from _store_output(step_context, step_output_handle, output)


def _get_output_asset_events(
    asset_key: AssetKey,
    asset_partitions: Iterable[str],
    output: Union[Output, DynamicOutput],
    output_def: OutputDefinition,
    io_manager_metadata: Mapping[str, MetadataValue],
    step_context: StepExecutionContext,
    execution_type: AssetExecutionType,
) -> Iterator[Union[AssetMaterialization, AssetObservation]]:
    # Metadata scoped to all events for this asset.
    key_scoped_metadata = {**output.metadata, **io_manager_metadata}

    # Clear any cached record associated with this asset, since we are about to generate a new
    # materialization.
    step_context.wipe_input_asset_version_info(asset_key)
    tags: dict[str, str]
    if (
        execution_type == AssetExecutionType.MATERIALIZATION
        and step_context.is_external_input_asset_version_info_loaded
        and asset_key in step_context.job_def.asset_layer.executable_asset_keys
    ):
        assert isinstance(output, Output)
        code_version = _get_code_version(asset_key, step_context)
        input_provenance_data = _get_input_provenance_data(asset_key, step_context)
        cached_data_version = (
            step_context.get_data_version(asset_key)
            if step_context.has_data_version(asset_key)
            else None
        )
        user_provided_data_version = output.data_version or cached_data_version
        data_version = (
            compute_logical_data_version(
                code_version,
                {k: meta["data_version"] for k, meta in input_provenance_data.items()},
            )
            if user_provided_data_version is None
            else user_provided_data_version
        )
        tags = _build_data_version_tags(
            data_version,
            code_version,
            input_provenance_data,
            user_provided_data_version is not None,
        )
        if not step_context.has_data_version(asset_key):
            data_version = DataVersion(tags[DATA_VERSION_TAG])
            step_context.set_data_version(asset_key, data_version)
    elif execution_type == AssetExecutionType.OBSERVATION:
        assert isinstance(output, Output)
        tags = (
            _build_data_version_observation_tags(output.data_version) if output.data_version else {}
        )
    else:
        tags = {}

    all_tags = {**tags, **((output.tags if not isinstance(output, DynamicOutput) else None) or {})}

    backfill_id = step_context.get_tag(BACKFILL_ID_TAG)
    if backfill_id:
        tags[BACKFILL_ID_TAG] = backfill_id

    if execution_type == AssetExecutionType.MATERIALIZATION:
        event_class = AssetMaterialization
        event_class = AssetMaterialization
    elif execution_type == AssetExecutionType.OBSERVATION:
        event_class = AssetObservation
    else:
        check.failed(f"Unexpected asset execution type {execution_type}")

    unpartitioned_asset_metadata = step_context.get_asset_metadata(asset_key=asset_key)
    all_unpartitioned_asset_metadata = {
        **key_scoped_metadata,
        **(unpartitioned_asset_metadata or {}),
    }
    if asset_partitions:
        for partition in asset_partitions:
            with disable_dagster_warnings():
                partition_scoped_metadata = step_context.get_asset_metadata(
                    asset_key=asset_key, partition_key=partition
                )
                all_metadata_for_partitioned_event = {
                    **all_unpartitioned_asset_metadata,
                    **(partition_scoped_metadata or {}),
                }
                # copy the tags dictionary before setting the partition key tags. Otherwise
                # all asset materialization events will point to the same dictionary with the
                # partition key tags of the last partition processed.
                tags_for_event = {**all_tags}
                tags_for_event.update(
                    get_tags_from_multi_partition_key(partition)
                    if isinstance(partition, MultiPartitionKey)
                    else {}
                )

                yield event_class(
                    asset_key=asset_key,
                    partition=partition,
                    metadata=all_metadata_for_partitioned_event,
                    tags=tags_for_event,
                )
    else:
        with disable_dagster_warnings():
            yield event_class(
                asset_key=asset_key, metadata=all_unpartitioned_asset_metadata, tags=all_tags
            )


def _get_code_version(asset_key: AssetKey, step_context: StepExecutionContext) -> str:
    return (
        step_context.job_def.asset_layer.get(asset_key).code_version
        or step_context.dagster_run.run_id
    )


class _InputProvenanceData(TypedDict):
    data_version: DataVersion
    storage_id: Optional[int]


def _get_input_provenance_data(
    asset_key: AssetKey, step_context: StepExecutionContext
) -> Mapping[AssetKey, _InputProvenanceData]:
    input_provenance: dict[AssetKey, _InputProvenanceData] = {}
    deps = step_context.job_def.asset_layer.get(asset_key).parent_keys
    for key in deps:
        # For deps external to this step, this will retrieve the cached record that was stored prior
        # to step execution. For inputs internal to this step, it may trigger a query to retrieve
        # the most recent materialization record (it will retrieve a cached record if it's already
        # been asked for). For this to be correct, the output materializations for the step must be
        # generated in topological order -- we assume this.
        version_info = step_context.maybe_fetch_and_get_input_asset_version_info(key)

        # This can only happen for source assets that have never been observed.
        if version_info is None:
            storage_id = None
            data_version = DEFAULT_DATA_VERSION
        else:
            storage_id = version_info.storage_id
            data_version = version_info.data_version or DEFAULT_DATA_VERSION

        input_provenance[key] = {
            "data_version": data_version,
            "storage_id": storage_id,
        }
    return input_provenance


def _build_data_version_tags(
    data_version: DataVersion,
    code_version: str,
    input_provenance_data: Mapping[AssetKey, _InputProvenanceData],
    data_version_is_user_provided: bool,
) -> dict[str, str]:
    tags: dict[str, str] = {}
    tags[CODE_VERSION_TAG] = code_version
    for key, meta in input_provenance_data.items():
        tags[get_input_data_version_tag(key)] = meta["data_version"].value
        tags[get_input_event_pointer_tag(key)] = (
            str(meta["storage_id"]) if meta["storage_id"] else NULL_EVENT_POINTER
        )
    tags[DATA_VERSION_TAG] = data_version.value
    if data_version_is_user_provided:
        tags[DATA_VERSION_IS_USER_PROVIDED_TAG] = "true"
    return tags


def _build_data_version_observation_tags(data_version: DataVersion) -> dict[str, str]:
    return {
        DATA_VERSION_TAG: data_version.value,
        DATA_VERSION_IS_USER_PROVIDED_TAG: "true",
    }


def _store_output(
    step_context: StepExecutionContext,
    step_output_handle: StepOutputHandle,
    output: Union[Output, DynamicOutput],
) -> Iterator[DagsterEvent]:
    output_def = step_context.op_def.output_def_named(step_output_handle.output_name)
    output_manager = step_context.get_io_manager(step_output_handle)
    output_context = step_context.get_output_context(step_output_handle, output.metadata)

    manager_materializations = []
    manager_metadata: dict[str, MetadataValue] = {}

    # don't store asset check outputs, asset observation outputs, asset result outputs, or Nothing
    # type outputs
    step_output = step_context.step.step_output_named(step_output_handle.output_name)
    if (
        step_output.properties.asset_check_key
        or (step_context.output_observes_source_asset(step_output_handle.output_name))
        or isinstance(output, AssetResultOutput)
        or output_context.dagster_type.is_nothing
    ):
        yield from _log_materialization_or_observation_events_for_asset(
            step_context=step_context,
            output_context=output_context,
            output=output,
            output_def=output_def,
            manager_metadata={},
        )
    # otherwise invoke the I/O manager
    else:
        # output_manager.handle_output is either a generator function, or a normal function with or
        # without a return value. In the case that handle_output is a normal function, we need to
        # catch errors should they be raised before a return value. We can do this by wrapping
        # handle_output in a generator so that errors will be caught within iterate_with_context.
        if not inspect.isgeneratorfunction(output_manager.handle_output):

            def _gen_fn():
                gen_output = output_manager.handle_output(output_context, output.value)
                yield from output_context.consume_events()
                if gen_output:
                    yield gen_output

            handle_output_gen = _gen_fn()
        else:
            handle_output_gen = output_manager.handle_output(output_context, output.value)

        for elt in iterate_with_context(
            lambda: op_execution_error_boundary(
                DagsterExecutionHandleOutputError,
                msg_fn=lambda: f'Error occurred while handling output "{output_context.name}" of step "{step_context.step.key}":',
                step_context=step_context,
                step_key=step_context.step.key,
                output_name=output_context.name,
            ),
            handle_output_gen,
        ):
            for event in output_context.consume_events():
                yield event

            manager_metadata = {**manager_metadata, **output_context.consume_logged_metadata()}
            if isinstance(elt, DagsterEvent):
                yield elt
            elif isinstance(elt, AssetMaterialization):
                manager_materializations.append(elt)
            elif isinstance(elt, dict):  # should remove this?
                beta_warning("Yielding metadata from an IOManager's handle_output() function")
                manager_metadata = {**manager_metadata, **normalize_metadata(elt)}
            else:
                raise DagsterInvariantViolationError(
                    f"IO manager on output {output_def.name} has returned "
                    f"value {elt} of type {type(elt).__name__}. The return type can only be "
                    "one of AssetMaterialization, Dict[str, MetadataValue]."
                )

        for event in output_context.consume_events():
            yield event

        manager_metadata = {**manager_metadata, **output_context.consume_logged_metadata()}
        # do not alter explicitly created AssetMaterializations
        for mgr_materialization in manager_materializations:
            if mgr_materialization.metadata and manager_metadata:
                raise DagsterInvariantViolationError(
                    f"When handling output '{output_context.name}' of"
                    f" {output_context.op_def.node_type_str} '{output_context.op_def.name}', received a"
                    " materialization with metadata, while context.add_output_metadata was used within"
                    " the same call to handle_output. Due to potential conflicts, this is not allowed."
                    " Please specify metadata in one place within the `handle_output` function."
                )

            if manager_metadata:
                with disable_dagster_warnings():
                    materialization = AssetMaterialization(
                        asset_key=mgr_materialization.asset_key,
                        description=mgr_materialization.description,
                        metadata=manager_metadata,
                        partition=mgr_materialization.partition,
                    )
            else:
                materialization = mgr_materialization

            yield DagsterEvent.asset_materialization(step_context, materialization)

        yield from _log_materialization_or_observation_events_for_asset(
            step_context=step_context,
            output_context=output_context,
            output=output,
            output_def=output_def,
            manager_metadata=manager_metadata,
        )

        yield DagsterEvent.handled_output(
            step_context,
            output_name=step_output_handle.output_name,
            manager_key=output_def.io_manager_key,
            metadata=manager_metadata,
        )


def _log_materialization_or_observation_events_for_asset(
    step_context: StepExecutionContext,
    output_context: OutputContext,
    output: Union[Output, DynamicOutput],
    output_def: OutputDefinition,
    manager_metadata: Mapping[str, MetadataValue],
) -> Iterable[DagsterEvent]:
    # This is a temporary workaround to prevent duplicate observation events from external
    # observable assets that were auto-converted from source assets. These assets yield
    # observation events through the context in their body, and will continue to do so until we
    # can convert them to using ObserveResult, which requires a solution to partition-scoped
    # metadata and data version on output. We identify these auto-converted assets by looking
    # for OBSERVATION-type asset that have this special metadata key (added in
    # `wrap_source_asset_observe_fn_in_op_compute_fn`), which should only occur for these
    # auto-converted source assets. This can be removed when source asset observation functions
    # are converted to use ObserveResult.
    if SYSTEM_METADATA_KEY_SOURCE_ASSET_OBSERVATION in output.metadata:
        return

    asset_key = output_context.asset_key if output_context.has_asset_key else None
    partitions = output_context.asset_partition_keys if output_context.has_asset_partitions else []

    if asset_key:
        asset_layer = step_context.job_def.asset_layer
        assets_def = asset_layer.assets_def_for_node(step_context.node_handle)
        execution_type = check.not_none(assets_def).execution_type

        check.invariant(
            execution_type != AssetExecutionType.UNEXECUTABLE,
            "There should never be unexecutable assets here",
        )

        check.invariant(
            execution_type in {AssetExecutionType.MATERIALIZATION, AssetExecutionType.OBSERVATION},
            f"Unexpected asset execution type {execution_type}",
        )

        asset_events = list(
            _get_output_asset_events(
                asset_key,
                partitions,
                output,
                output_def,
                manager_metadata,
                step_context,
                execution_type,
            )
        )

        batch_id = generate_event_batch_id()
        last_index = len(asset_events) - 1
        for i, asset_event in enumerate(asset_events):
            batch_metadata = (
                DagsterEventBatchMetadata(batch_id, i == last_index) if partitions else None
            )
            yield _dagster_event_for_asset_event(step_context, asset_event, batch_metadata)


def _dagster_event_for_asset_event(
    step_context: StepExecutionContext,
    asset_event: Union[AssetMaterialization, AssetObservation],
    batch_metadata: Optional[DagsterEventBatchMetadata],
) -> DagsterEvent:
    if isinstance(asset_event, AssetMaterialization):
        return DagsterEvent.asset_materialization(step_context, asset_event, batch_metadata)
    else:  # observation
        return DagsterEvent.asset_observation(step_context, asset_event, batch_metadata)

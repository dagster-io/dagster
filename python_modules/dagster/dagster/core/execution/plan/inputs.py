import hashlib
from abc import ABC, abstractmethod, abstractproperty
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, NamedTuple, Optional, Set, Union, cast

from dagster import check
from dagster.core.definitions import (
    Failure,
    InputDefinition,
    PipelineDefinition,
    RetryRequested,
    SolidHandle,
)
from dagster.core.definitions.events import AssetLineageInfo
from dagster.core.errors import (
    DagsterExecutionLoadInputError,
    DagsterTypeLoadingError,
    user_code_error_boundary,
)
from dagster.core.storage.io_manager import IOManager
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.serdes import whitelist_for_serdes
from dagster.utils import ensure_gen

from .objects import TypeCheckData
from .outputs import StepOutputHandle, UnresolvedStepOutputHandle
from .utils import build_resources_for_manager

if TYPE_CHECKING:
    from dagster.core.types.dagster_type import DagsterType
    from dagster.core.storage.input_manager import InputManager
    from dagster.core.events import DagsterEvent
    from dagster.core.execution.context.system import StepExecutionContext
    from dagster.core.execution.context.input import InputContext


def _get_asset_lineage_from_fns(
    context, asset_key_fn, asset_partitions_fn
) -> Optional[AssetLineageInfo]:
    asset_key = asset_key_fn(context)
    if not asset_key:
        return None
    return AssetLineageInfo(
        asset_key=asset_key,
        partitions=asset_partitions_fn(context),
    )


@whitelist_for_serdes
class StepInputData(
    NamedTuple("_StepInputData", [("input_name", str), ("type_check_data", TypeCheckData)])
):
    """"Serializable payload of information for the result of processing a step input"""

    def __new__(cls, input_name: str, type_check_data: TypeCheckData):
        return super(StepInputData, cls).__new__(
            cls,
            input_name=check.str_param(input_name, "input_name"),
            type_check_data=check.opt_inst_param(type_check_data, "type_check_data", TypeCheckData),
        )


class StepInput(
    NamedTuple(
        "_StepInput",
        [("name", str), ("dagster_type_key", str), ("source", "StepInputSource")],
    )
):
    """Holds information for how to prepare an input for an ExecutionStep"""

    def __new__(cls, name, dagster_type_key, source):
        return super(StepInput, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type_key=check.str_param(dagster_type_key, "dagster_type_key"),
            source=check.inst_param(source, "source", StepInputSource),
        )

    @property
    def dependency_keys(self) -> Set[str]:
        return self.source.step_key_dependencies

    def get_step_output_handle_dependencies(self) -> List[StepOutputHandle]:
        return self.source.step_output_handle_dependencies


def join_and_hash(*args) -> Optional[str]:
    lst = [check.opt_str_param(elem, "elem") for elem in args]
    if None in lst:
        return None

    lst = cast(List[str], lst)
    unhashed = "".join(sorted(lst))
    return hashlib.sha1(unhashed.encode("utf-8")).hexdigest()


class StepInputSource(ABC):
    """How to load the data for a step input"""

    @property
    def step_key_dependencies(self) -> Set[str]:
        return set()

    @property
    def step_output_handle_dependencies(self) -> List[StepOutputHandle]:
        return []

    def get_input_def(self, pipeline_def: PipelineDefinition) -> InputDefinition:
        return pipeline_def.get_solid(self.solid_handle).input_def_named(self.input_name)

    @abstractproperty
    def solid_handle(self) -> SolidHandle:
        pass

    @abstractproperty
    def input_name(self) -> str:
        pass

    @abstractmethod
    def load_input_object(self, step_context: "StepExecutionContext"):
        raise NotImplementedError()

    def required_resource_keys(self, _pipeline_def: PipelineDefinition) -> Set[str]:
        return set()

    def get_asset_lineage(self, _step_context: "StepExecutionContext") -> List[AssetLineageInfo]:
        return []

    @abstractmethod
    def compute_version(
        self,
        step_versions: Dict[str, Optional[str]],
        pipeline_def: PipelineDefinition,
        environment_config: EnvironmentConfig,
    ) -> Optional[str]:
        """See resolve_step_versions in resolve_versions.py for explanation of step_versions"""
        raise NotImplementedError()


@whitelist_for_serdes
class FromRootInputManager(
    NamedTuple(
        "_FromRootInputManager",
        [("solid_handle", SolidHandle), ("input_name", str)],
    ),
    StepInputSource,
):
    def load_input_object(self, step_context: "StepExecutionContext") -> Iterator["DagsterEvent"]:
        from dagster.core.events import DagsterEvent

        input_def = self.get_input_def(step_context.pipeline_def)

        solid_config = step_context.environment_config.solids.get(str(self.solid_handle))
        config_data = solid_config.inputs.get(self.input_name) if solid_config else None

        loader = getattr(step_context.resources, input_def.root_manager_key)
        load_input_context = step_context.for_input_manager(
            input_def.name,
            config_data,
            metadata=input_def.metadata,
            dagster_type=input_def.dagster_type,
            resource_config=step_context.environment_config.resources[
                input_def.root_manager_key
            ].config,
            resources=build_resources_for_manager(input_def.root_manager_key, step_context),
        )
        yield _load_input_with_input_manager(loader, load_input_context)
        yield DagsterEvent.loaded_input(
            step_context,
            input_name=input_def.name,
            manager_key=input_def.root_manager_key,
        )

    def compute_version(self, step_versions, pipeline_def, environment_config) -> Optional[str]:
        # TODO: support versioning for root loaders
        return None

    def required_resource_keys(self, pipeline_def: PipelineDefinition) -> Set[str]:
        input_def = self.get_input_def(pipeline_def)
        return {input_def.root_manager_key}


@whitelist_for_serdes
class FromStepOutput(
    NamedTuple(
        "_FromStepOutput",
        [
            ("step_output_handle", StepOutputHandle),
            ("solid_handle", SolidHandle),
            ("input_name", str),
            ("fan_in", bool),
        ],
    ),
    StepInputSource,
):
    """This step input source is the output of a previous step"""

    def __new__(cls, step_output_handle, solid_handle, input_name, fan_in):
        return super(FromStepOutput, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, "step_output_handle", StepOutputHandle
            ),
            solid_handle=check.inst_param(solid_handle, "solid_handle", SolidHandle),
            input_name=check.str_param(input_name, "input_name"),
            fan_in=check.bool_param(fan_in, "fan_in"),
        )

    @property
    def step_key_dependencies(self) -> Set[str]:
        return {self.step_output_handle.step_key}

    @property
    def step_output_handle_dependencies(self) -> List[StepOutputHandle]:
        return [self.step_output_handle]

    def get_load_context(self, step_context: "StepExecutionContext") -> "InputContext":
        io_manager_key = step_context.execution_plan.get_manager_key(
            self.step_output_handle, step_context.pipeline_def
        )
        resource_config = step_context.environment_config.resources[io_manager_key].config
        resources = build_resources_for_manager(io_manager_key, step_context)

        input_def = self.get_input_def(step_context.pipeline_def)

        solid_config = step_context.environment_config.solids.get(str(self.solid_handle))
        config_data = solid_config.inputs.get(self.input_name) if solid_config else None

        return step_context.for_input_manager(
            input_def.name,
            config_data,
            input_def.metadata,
            input_def.dagster_type,
            self.step_output_handle,
            resource_config,
            resources,
        )

    def load_input_object(self, step_context: "StepExecutionContext") -> Iterator["DagsterEvent"]:
        from dagster.core.events import DagsterEvent
        from dagster.core.storage.intermediate_storage import IntermediateStorageAdapter

        source_handle = self.step_output_handle
        manager_key = step_context.execution_plan.get_manager_key(
            source_handle, step_context.pipeline_def
        )
        input_manager = step_context.get_io_manager(source_handle)
        check.invariant(
            isinstance(input_manager, IOManager),
            f'Input "{self.input_name}" for step "{step_context.step.key}" is depending on '
            f'the manager of upstream output "{source_handle.output_name}" from step '
            f'"{source_handle.step_key}" to load it, but that manager is not an IOManager. '
            f"Please ensure that the resource returned for resource key "
            f'"{manager_key}" is an IOManager.',
        )
        yield _load_input_with_input_manager(input_manager, self.get_load_context(step_context))
        yield DagsterEvent.loaded_input(
            step_context,
            input_name=self.input_name,
            manager_key=manager_key,
            upstream_output_name=source_handle.output_name,
            upstream_step_key=source_handle.step_key,
            message_override=f'Loaded input "{self.input_name}" using intermediate storage'
            if isinstance(input_manager, IntermediateStorageAdapter)
            else None,
        )

    def compute_version(
        self,
        step_versions: Dict[str, Optional[str]],
        pipeline_def: PipelineDefinition,
        environment_config: EnvironmentConfig,
    ) -> Optional[str]:
        if (
            self.step_output_handle.step_key not in step_versions
            or not step_versions[self.step_output_handle.step_key]
        ):
            return None
        else:
            return join_and_hash(
                step_versions[self.step_output_handle.step_key], self.step_output_handle.output_name
            )

    def required_resource_keys(self, _pipeline_def: PipelineDefinition) -> Set[str]:
        return set()

    def get_asset_lineage(self, step_context: "StepExecutionContext") -> List[AssetLineageInfo]:
        source_handle = self.step_output_handle
        input_manager = step_context.get_io_manager(source_handle)
        load_context = self.get_load_context(step_context)

        # check input_def
        input_def = self.get_input_def(step_context.pipeline_def)
        if input_def.is_asset:
            lineage_info = _get_asset_lineage_from_fns(
                load_context, input_def.get_asset_key, input_def.get_asset_partitions
            )
            return [lineage_info] if lineage_info else []

        # check io manager
        io_lineage_info = _get_asset_lineage_from_fns(
            load_context,
            input_manager.get_input_asset_key,
            input_manager.get_input_asset_partitions,
        )
        if io_lineage_info is not None:
            return [io_lineage_info]

        # check output_def
        upstream_output = step_context.execution_plan.get_step_output(self.step_output_handle)
        if upstream_output.is_asset:
            output_def = step_context.pipeline_def.get_solid(
                upstream_output.solid_handle
            ).output_def_named(upstream_output.name)
            lineage_info = _get_asset_lineage_from_fns(
                load_context.upstream_output,
                output_def.get_asset_key,
                output_def.get_asset_partitions,
            )
            return [lineage_info] if lineage_info else []

        return []


@whitelist_for_serdes
class FromConfig(
    NamedTuple("_FromConfig", [("solid_handle", SolidHandle), ("input_name", str)]),
    StepInputSource,
):
    """This step input source is configuration to be passed to a type loader"""

    def __new__(cls, solid_handle: SolidHandle, input_name: str):
        return super(FromConfig, cls).__new__(
            cls,
            solid_handle=solid_handle,
            input_name=input_name,
        )

    def load_input_object(self, step_context: "StepExecutionContext") -> Any:
        with user_code_error_boundary(
            DagsterTypeLoadingError,
            msg_fn=lambda: (
                f'Error occurred while loading input "{self.input_name}" of '
                f'step "{step_context.step.key}":'
            ),
        ):
            dagster_type = self.get_input_def(step_context.pipeline_def).dagster_type

            solid_config = step_context.environment_config.solids.get(str(self.solid_handle))
            config_data = solid_config.inputs.get(self.input_name) if solid_config else None

            return dagster_type.loader.construct_from_config_value(step_context, config_data)

    def required_resource_keys(self, pipeline_def: PipelineDefinition) -> Set[str]:
        input_def = self.get_input_def(pipeline_def)
        return (
            input_def.dagster_type.loader.required_resource_keys()
            if input_def.dagster_type.loader
            else set()
        )

    def compute_version(
        self,
        step_versions: Dict[str, Optional[str]],
        pipeline_def: PipelineDefinition,
        environment_config: EnvironmentConfig,
    ) -> Optional[str]:
        solid_config = environment_config.solids.get(str(self.solid_handle))
        config_data = solid_config.inputs.get(self.input_name) if solid_config else None

        solid_def = pipeline_def.get_solid(self.solid_handle)
        dagster_type = solid_def.input_def_named(self.input_name).dagster_type
        return dagster_type.loader.compute_loaded_input_version(config_data)


@whitelist_for_serdes
class FromDefaultValue(
    NamedTuple(
        "_FromDefaultValue",
        [("solid_handle", SolidHandle), ("input_name", str)],
    ),
    StepInputSource,
):
    """This step input source is the default value declared on the InputDefinition"""

    def __new__(cls, solid_handle: SolidHandle, input_name: str):
        return super(FromDefaultValue, cls).__new__(cls, solid_handle, input_name)

    def _load_value(self, pipeline_def: PipelineDefinition):
        return pipeline_def.get_solid(self.solid_handle).definition.default_value_for_input(
            self.input_name
        )

    def load_input_object(self, step_context: "StepExecutionContext"):
        return self._load_value(step_context.pipeline_def)

    def compute_version(
        self,
        step_versions: Dict[str, Optional[str]],
        pipeline_def: PipelineDefinition,
        environment_config: EnvironmentConfig,
    ) -> Optional[str]:
        return join_and_hash(repr(self._load_value(pipeline_def)))


@whitelist_for_serdes
class FromMultipleSources(
    NamedTuple(
        "_FromMultipleSources",
        [
            ("solid_handle", SolidHandle),
            ("input_name", str),
            ("sources", List[StepInputSource]),
        ],
    ),
    StepInputSource,
):
    """This step input is fans-in multiple sources in to a single input. The input will receive a list."""

    def __new__(cls, solid_handle: SolidHandle, input_name: str, sources):
        check.list_param(sources, "sources", StepInputSource)
        for source in sources:
            check.invariant(
                not isinstance(source, FromMultipleSources),
                "Can not have multiple levels of FromMultipleSources StepInputSource",
            )
        return super(FromMultipleSources, cls).__new__(
            cls, solid_handle=solid_handle, input_name=input_name, sources=sources
        )

    @property
    def step_key_dependencies(self):
        keys = set()
        for source in self.sources:
            keys.update(source.step_key_dependencies)

        return keys

    @property
    def step_output_handle_dependencies(self):
        handles = []
        for source in self.sources:
            handles.extend(source.step_output_handle_dependencies)

        return handles

    def _step_output_handles_no_output(self, step_context):
        # FIXME https://github.com/dagster-io/dagster/issues/3511
        # this is a stopgap which asks the instance to check the event logs to find out step skipping
        step_output_handles_with_output = set()
        for event_record in step_context.instance.all_logs(step_context.run_id):
            if event_record.dagster_event and event_record.dagster_event.is_successful_output:
                step_output_handles_with_output.add(
                    event_record.dagster_event.event_specific_data.step_output_handle
                )
        return set(self.step_output_handle_dependencies).difference(step_output_handles_with_output)

    def load_input_object(self, step_context):
        from dagster.core.events import DagsterEvent

        values = []

        # some upstream steps may have skipped and we allow fan-in to continue in their absence
        source_handles_to_skip = self._step_output_handles_no_output(step_context)

        for inner_source in self.sources:
            if (
                inner_source.step_output_handle_dependencies
                and inner_source.step_output_handle in source_handles_to_skip
            ):
                continue

            for event_or_input_value in ensure_gen(inner_source.load_input_object(step_context)):
                if isinstance(event_or_input_value, DagsterEvent):
                    yield event_or_input_value
                else:
                    values.append(event_or_input_value)

        yield values

    def required_resource_keys(self, pipeline_def: PipelineDefinition) -> Set[str]:
        resource_keys: Set[str] = set()
        for source in self.sources:
            resource_keys = resource_keys.union(source.required_resource_keys(pipeline_def))
        return resource_keys

    def compute_version(self, step_versions, pipeline_def, environment_config) -> Optional[str]:
        return join_and_hash(
            *[
                inner_source.compute_version(step_versions, pipeline_def, environment_config)
                for inner_source in self.sources
            ]
        )

    def get_asset_lineage(self, step_context: "StepExecutionContext") -> List[AssetLineageInfo]:
        return [
            relation
            for source in self.sources
            for relation in source.get_asset_lineage(step_context)
        ]


def _load_input_with_input_manager(input_manager: "InputManager", context: "InputContext"):
    from dagster.core.execution.context.system import StepExecutionContext

    step_context = cast(StepExecutionContext, context.step_context)
    with user_code_error_boundary(
        DagsterExecutionLoadInputError,
        control_flow_exceptions=[Failure, RetryRequested],
        msg_fn=lambda: (
            f'Error occurred while loading input "{context.name}" of '
            f'step "{step_context.step.key}":'
        ),
        step_key=step_context.step.key,
        input_name=context.name,
    ):
        value = input_manager.load_input(context)
    # close user code boundary before returning value
    return value


@whitelist_for_serdes
class FromPendingDynamicStepOutput(
    NamedTuple(
        "_FromPendingDynamicStepOutput",
        [
            ("step_output_handle", StepOutputHandle),
            ("solid_handle", SolidHandle),
            ("input_name", str),
        ],
    ),
):
    """
    This step input source models being directly downstream of a step with dynamic output.
    Once that step completes successfully, this will resolve once per DynamicOutput.
    """

    def __new__(
        cls,
        step_output_handle: StepOutputHandle,
        solid_handle: SolidHandle,
        input_name: str,
    ):
        # Model the unknown mapping key from known execution step
        # using a StepOutputHandle with None mapping_key.
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        check.invariant(step_output_handle.mapping_key is None)

        return super(FromPendingDynamicStepOutput, cls).__new__(
            cls,
            step_output_handle=step_output_handle,
            solid_handle=check.inst_param(solid_handle, "solid_handle", SolidHandle),
            input_name=check.str_param(input_name, "input_name"),
        )

    @property
    def resolved_by_step_key(self) -> str:
        return self.step_output_handle.step_key

    @property
    def resolved_by_output_name(self) -> str:
        return self.step_output_handle.output_name

    def resolve(self, mapping_key) -> FromStepOutput:
        check.str_param(mapping_key, "mapping_key")
        return FromStepOutput(
            step_output_handle=StepOutputHandle(
                step_key=self.step_output_handle.step_key,
                output_name=self.step_output_handle.output_name,
                mapping_key=mapping_key,
            ),
            solid_handle=self.solid_handle,
            input_name=self.input_name,
            fan_in=False,
        )

    def get_step_output_handle_dep_with_placeholder(self) -> StepOutputHandle:
        # None mapping_key on StepOutputHandle acts as placeholder
        return self.step_output_handle

    def required_resource_keys(self, _pipeline_def: PipelineDefinition) -> Set[str]:
        return set()

    def get_input_def(self, pipeline_def: PipelineDefinition) -> InputDefinition:
        return pipeline_def.get_solid(self.solid_handle).input_def_named(self.input_name)


@whitelist_for_serdes
class FromUnresolvedStepOutput(
    NamedTuple(
        "_FromUnresolvedStepOutput",
        [
            ("unresolved_step_output_handle", UnresolvedStepOutputHandle),
            ("solid_handle", SolidHandle),
            ("input_name", str),
        ],
    ),
):
    """
    This step input source models being downstream of another unresolved step,
    for example indirectly downstream from a step with dynamic output.
    """

    def __new__(
        cls,
        unresolved_step_output_handle: UnresolvedStepOutputHandle,
        solid_handle: SolidHandle,
        input_name: str,
    ):
        return super(FromUnresolvedStepOutput, cls).__new__(
            cls,
            unresolved_step_output_handle=check.inst_param(
                unresolved_step_output_handle,
                "unresolved_step_output_handle",
                UnresolvedStepOutputHandle,
            ),
            solid_handle=check.inst_param(solid_handle, "solid_handle", SolidHandle),
            input_name=check.str_param(input_name, "input_name"),
        )

    @property
    def resolved_by_step_key(self) -> str:
        return self.unresolved_step_output_handle.resolved_by_step_key

    @property
    def resolved_by_output_name(self) -> str:
        return self.unresolved_step_output_handle.resolved_by_output_name

    def resolve(self, mapping_key: str) -> FromStepOutput:
        check.str_param(mapping_key, "mapping_key")
        return FromStepOutput(
            step_output_handle=self.unresolved_step_output_handle.resolve(mapping_key),
            solid_handle=self.solid_handle,
            input_name=self.input_name,
            fan_in=False,
        )

    def get_step_output_handle_dep_with_placeholder(self) -> StepOutputHandle:
        return self.unresolved_step_output_handle.get_step_output_handle_with_placeholder()

    def required_resource_keys(self, _pipeline_def: PipelineDefinition) -> Set[str]:
        return set()

    def get_input_def(self, pipeline_def: PipelineDefinition) -> InputDefinition:
        return pipeline_def.get_solid(self.solid_handle).input_def_named(self.input_name)


@whitelist_for_serdes
class FromDynamicCollect(
    NamedTuple(
        "_FromDynamicCollect",
        [
            ("source", Union[FromPendingDynamicStepOutput, FromUnresolvedStepOutput]),
            ("solid_handle", SolidHandle),
            ("input_name", str),
        ],
    ),
):
    @property
    def resolved_by_step_key(self) -> str:
        return self.source.resolved_by_step_key

    @property
    def resolved_by_output_name(self) -> str:
        return self.source.resolved_by_output_name

    def get_step_output_handle_dep_with_placeholder(self) -> StepOutputHandle:
        return self.source.get_step_output_handle_dep_with_placeholder()

    def get_input_def(self, pipeline_def: PipelineDefinition) -> InputDefinition:
        return pipeline_def.get_solid(self.solid_handle).input_def_named(self.input_name)

    def required_resource_keys(self, _pipeline_def: PipelineDefinition) -> Set[str]:
        return set()

    def resolve(self, mapping_keys):
        return FromMultipleSources(
            solid_handle=self.solid_handle,
            input_name=self.input_name,
            sources=[self.source.resolve(map_key) for map_key in mapping_keys],
        )


class UnresolvedMappedStepInput(NamedTuple):
    """Holds information for how to resolve a StepInput once the upstream mapping is done"""

    name: str
    dagster_type_key: str
    source: Union[FromPendingDynamicStepOutput, FromUnresolvedStepOutput]

    @property
    def resolved_by_step_key(self) -> str:
        return self.source.resolved_by_step_key

    @property
    def resolved_by_output_name(self) -> str:
        return self.source.resolved_by_output_name

    def resolve(self, map_key) -> StepInput:
        return StepInput(
            name=self.name,
            dagster_type_key=self.dagster_type_key,
            source=self.source.resolve(map_key),
        )

    def get_step_output_handle_deps_with_placeholders(self) -> List[StepOutputHandle]:
        """Return StepOutputHandles with placeholders, unresolved step keys and None mapping keys"""

        return [self.source.get_step_output_handle_dep_with_placeholder()]


class UnresolvedCollectStepInput(NamedTuple):
    """Holds information for how to resolve a StepInput once the upstream mapping is done"""

    name: str
    dagster_type_key: str
    source: FromDynamicCollect

    @property
    def resolved_by_step_key(self) -> str:
        return self.source.resolved_by_step_key

    @property
    def resolved_by_output_name(self) -> str:
        return self.source.resolved_by_output_name

    def resolve(self, mapping_keys: List[str]) -> StepInput:
        return StepInput(
            name=self.name,
            dagster_type_key=self.dagster_type_key,
            source=self.source.resolve(mapping_keys),
        )

    def get_step_output_handle_deps_with_placeholders(self) -> List[StepOutputHandle]:
        """Return StepOutputHandles with placeholders, unresolved step keys and None mapping keys"""

        return [self.source.get_step_output_handle_dep_with_placeholder()]


StepInputSourceTypes = (
    StepInputSource,
    FromDynamicCollect,
    FromUnresolvedStepOutput,
    FromPendingDynamicStepOutput,
)

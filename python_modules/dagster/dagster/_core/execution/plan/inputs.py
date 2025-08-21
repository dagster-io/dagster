import hashlib
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, AbstractSet, Optional, Union, cast  # noqa: UP035

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions import InputDefinition, JobDefinition, NodeHandle
from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY
from dagster._core.errors import (
    DagsterExecutionLoadInputError,
    DagsterTypeLoadingError,
    user_code_error_boundary,
)
from dagster._core.execution.plan.objects import TypeCheckData
from dagster._core.execution.plan.outputs import StepOutputHandle, UnresolvedStepOutputHandle
from dagster._core.execution.plan.utils import (
    build_resources_for_manager,
    op_execution_error_boundary,
)
from dagster._core.storage.io_manager import IOManager
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.execution.context.input import InputContext
    from dagster._core.execution.context.system import StepExecutionContext
    from dagster._core.storage.input_manager import InputManager

StepInputUnion: TypeAlias = Union[
    "StepInput", "UnresolvedMappedStepInput", "UnresolvedCollectStepInput"
]


@whitelist_for_serdes
@record
class StepInputData:
    """Serializable payload of information for the result of processing a step input."""

    input_name: str
    type_check_data: TypeCheckData


@record
class StepInput:
    """Holds information for how to prepare an input for an ExecutionStep."""

    name: str
    dagster_type_key: str
    source: "StepInputSource"

    @property
    def dependency_keys(self) -> AbstractSet[str]:
        return self.source.step_key_dependencies

    def get_step_output_handle_dependencies(self) -> Sequence[StepOutputHandle]:
        return self.source.step_output_handle_dependencies


def join_and_hash(*args: Optional[str]) -> Optional[str]:
    lst = [check.opt_str_param(elem, "elem") for elem in args]
    if None in lst:
        return None

    str_lst = cast("list[str]", lst)
    unhashed = "".join(sorted(str_lst))
    return hashlib.sha1(unhashed.encode("utf-8")).hexdigest()


class StepInputSource(ABC):
    """How to load the data for a step input."""

    @property
    def step_key_dependencies(self) -> set[str]:
        return set()

    @property
    def step_output_handle_dependencies(self) -> Sequence[StepOutputHandle]:
        return []

    @abstractmethod
    def load_input_object(
        self, step_context: "StepExecutionContext", input_def: InputDefinition
    ) -> Iterator[object]: ...

    def required_resource_keys(
        self, _job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> AbstractSet[str]:
        return set()


@whitelist_for_serdes(
    storage_name="FromSourceAsset", storage_field_names={"node_handle": "solid_handle"}
)
@record
class FromLoadableAsset(StepInputSource):
    """Load input value from an asset."""

    # deprecated, preserved for back-compat
    node_handle: NodeHandle = NodeHandle("", None)
    input_name: str = ""

    def load_input_object(
        self,
        step_context: "StepExecutionContext",
        input_def: InputDefinition,
    ) -> Iterator[object]:
        from dagster._core.events import DagsterEvent
        from dagster._core.execution.context.output import OutputContext

        asset_layer = step_context.job_def.asset_layer

        input_asset_key = input_def.hardcoded_asset_key or asset_layer.get_asset_key_for_node_input(
            step_context.node_handle, input_name=input_def.name
        )
        assert input_asset_key is not None

        input_manager_key = (
            input_def.input_manager_key
            if input_def.input_manager_key
            else asset_layer.get(input_asset_key).io_manager_key
        )

        op_config = step_context.resolved_run_config.ops.get(str(step_context.node_handle))
        config_data = op_config.inputs.get(input_def.name) if op_config else None

        loader = getattr(step_context.resources, input_manager_key)
        resources = build_resources_for_manager(input_manager_key, step_context)
        resource_config = step_context.resolved_run_config.resources[input_manager_key].config
        load_input_context = step_context.for_input_manager(
            input_def.name,
            config_data,
            definition_metadata=input_def.metadata,
            dagster_type=input_def.dagster_type,
            resource_config=resource_config,
            resources=resources,
            artificial_output_context=OutputContext(
                resources=resources,
                asset_key=input_asset_key,
                name=input_asset_key.path[-1],
                step_key="none",
                definition_metadata=asset_layer.get(input_asset_key).metadata,
                resource_config=resource_config,
                log_manager=step_context.log,
                step_context=step_context,
            ),
        )

        yield from _load_input_with_input_manager(loader, load_input_context)

        metadata = {
            **load_input_context.definition_metadata,
            **load_input_context.consume_logged_metadata(),
        }

        yield DagsterEvent.loaded_input(
            step_context,
            input_name=input_def.name,
            manager_key=input_manager_key,
            metadata=metadata,
        )

    def required_resource_keys(
        self, job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> set[str]:
        input_asset_key = job_def.asset_layer.get_asset_key_for_node_input(op_handle, op_input_name)
        if input_asset_key is None:
            check.failed(
                f"Must have an asset key associated with input {op_input_name} to load it"
                " using FromSourceAsset",
            )

        input_def = job_def.get_node(op_handle).input_def_named(op_input_name)
        if input_def.input_manager_key is not None:
            input_manager_key = input_def.input_manager_key
        else:
            input_manager_key = (
                job_def.asset_layer.get(input_asset_key).io_manager_key
                if job_def.asset_layer.has(input_asset_key)
                else DEFAULT_IO_MANAGER_KEY
            )

        if input_manager_key is None:
            check.failed(
                f"Must have an io_manager associated with asset {input_asset_key} to load it using"
                " FromSourceAsset"
            )
        return {input_manager_key}


@whitelist_for_serdes(
    storage_name="FromRootInputManager", storage_field_names={"node_handle": "solid_handle"}
)
@record
class FromInputManager(StepInputSource):
    """Load input value via a InputManager."""

    node_handle: NodeHandle
    input_name: str

    def load_input_object(
        self,
        step_context: "StepExecutionContext",
        input_def: InputDefinition,
    ) -> Iterator[object]:
        from dagster._core.events import DagsterEvent

        check.invariant(
            step_context.node_handle == self.node_handle and input_def.name == self.input_name,
            "InputManager source must be op input and not one along composition mapping. "
            f"Loading for op {step_context.node_handle}.{input_def.name} "
            f"but source is {self.node_handle}.{self.input_name}.",
        )

        input_def = step_context.op_def.input_def_named(input_def.name)

        op_config = step_context.resolved_run_config.ops.get(str(self.node_handle))
        config_data = op_config.inputs.get(self.input_name) if op_config else None

        input_manager_key = check.not_none(input_def.input_manager_key)

        loader = getattr(step_context.resources, input_manager_key)

        load_input_context = step_context.for_input_manager(
            input_def.name,
            config_data,
            definition_metadata=input_def.metadata,
            dagster_type=input_def.dagster_type,
            resource_config=step_context.resolved_run_config.resources[input_manager_key].config,
            resources=build_resources_for_manager(input_manager_key, step_context),
        )

        yield from _load_input_with_input_manager(loader, load_input_context)

        metadata = {
            **load_input_context.definition_metadata,
            **load_input_context.consume_logged_metadata(),
        }

        yield DagsterEvent.loaded_input(
            step_context,
            input_name=input_def.name,
            manager_key=input_manager_key,
            metadata=metadata,
        )

    def required_resource_keys(
        self, job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> set[str]:
        input_def = job_def.get_node(op_handle).input_def_named(op_input_name)

        input_manager_key: str = check.not_none(input_def.input_manager_key)

        return {input_manager_key}


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
@record_custom
class FromStepOutput(StepInputSource, IHaveNew):
    """This step input source is the output of a previous step.
    Source handle may refer to graph in case of input mapping.
    """

    step_output_handle: StepOutputHandle
    fan_in: bool

    # deprecated, preserved for back-compat
    node_handle: NodeHandle
    input_name: str

    def __new__(
        cls,
        step_output_handle: StepOutputHandle,
        fan_in: bool,
        # deprecated, preserved for back-compat
        node_handle: Optional[NodeHandle] = None,
        input_name: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            step_output_handle=step_output_handle,
            fan_in=fan_in,
            # add placeholder values for back-compat
            node_handle=node_handle or NodeHandle("", None),
            input_name=input_name or "",
        )

    @property
    def step_key_dependencies(self) -> set[str]:
        return {self.step_output_handle.step_key}

    @property
    def step_output_handle_dependencies(self) -> Sequence[StepOutputHandle]:
        return [self.step_output_handle]

    def get_load_context(
        self,
        step_context: "StepExecutionContext",
        input_def: InputDefinition,
        io_manager_key: Optional[str] = None,
    ) -> "InputContext":
        resolved_io_manager_key = (
            step_context.execution_plan.get_manager_key(
                self.step_output_handle, step_context.job_def
            )
            if io_manager_key is None
            else io_manager_key
        )

        resource_config = step_context.resolved_run_config.resources[resolved_io_manager_key].config
        resources = build_resources_for_manager(resolved_io_manager_key, step_context)

        solid_config = step_context.resolved_run_config.ops.get(str(step_context.node_handle))
        config_data = solid_config.inputs.get(input_def.name) if solid_config else None

        return step_context.for_input_manager(
            input_def.name,
            config_data,
            input_def.metadata,
            input_def.dagster_type,
            self.step_output_handle,
            resource_config,
            resources,
        )

    def load_input_object(
        self,
        step_context: "StepExecutionContext",
        input_def: InputDefinition,
    ) -> Iterator[object]:
        from dagster._core.events import DagsterEvent
        from dagster._core.storage.input_manager import InputManager

        source_handle = self.step_output_handle

        if input_def.input_manager_key is not None:
            manager_key = input_def.input_manager_key
            input_manager = getattr(step_context.resources, manager_key)
            check.invariant(
                isinstance(input_manager, InputManager),
                f'Input "{input_def.name}" for step "{step_context.step.key}" is depending on '
                f'the manager "{manager_key}" to load it, but it is not an InputManager. '
                "Please ensure that the resource returned for resource key "
                f'"{manager_key}" is an InputManager.',
            )
        else:
            manager_key = step_context.execution_plan.get_manager_key(
                source_handle, step_context.job_def
            )
            input_manager = step_context.get_io_manager(source_handle)
            check.invariant(
                isinstance(input_manager, IOManager),
                f'Input "{input_def.name}" for step "{step_context.step.key}" is depending on '
                f'the manager of upstream output "{source_handle.output_name}" from step '
                f'"{source_handle.step_key}" to load it, but that manager is not an IOManager. '
                "Please ensure that the resource returned for resource key "
                f'"{manager_key}" is an IOManager.',
            )
        load_input_context = self.get_load_context(
            step_context, input_def, io_manager_key=manager_key
        )
        yield from _load_input_with_input_manager(input_manager, load_input_context)

        metadata = {
            **load_input_context.definition_metadata,
            **load_input_context.consume_logged_metadata(),
        }

        yield DagsterEvent.loaded_input(
            step_context,
            input_name=input_def.name,
            manager_key=manager_key,
            upstream_output_name=source_handle.output_name,
            upstream_step_key=source_handle.step_key,
            metadata=metadata,
        )

    def required_resource_keys(
        self, _job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> set[str]:
        return set()


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
@record
class FromConfig(StepInputSource):
    """This step input source is configuration to be passed to a type loader.

    A None node_handle implies the inputs were provided at the root graph level.
    """

    node_handle: Optional[NodeHandle]
    input_name: str

    def get_associated_input_def(self, job_def: JobDefinition) -> InputDefinition:
        """Returns the InputDefinition along the potential composition InputMapping chain
        that the config was provided at.
        """
        if self.node_handle:
            return job_def.get_node(self.node_handle).input_def_named(self.input_name)
        else:
            return job_def.graph.input_def_named(self.input_name)

    def get_associated_config(self, resolved_run_config: ResolvedRunConfig):
        """Returns the config specified, potentially specified at any point along graph composition
        including the root.
        """
        if self.node_handle:
            op_config = resolved_run_config.ops.get(str(self.node_handle))
            return op_config.inputs.get(self.input_name) if op_config else None
        else:
            input_config = resolved_run_config.inputs
            return input_config.get(self.input_name) if input_config else None

    def load_input_object(
        self,
        step_context: "StepExecutionContext",
        input_def: InputDefinition,
    ) -> Iterator[object]:
        with user_code_error_boundary(
            DagsterTypeLoadingError,
            msg_fn=lambda: f'Error occurred while loading input "{self.input_name}" of step "{step_context.step.key}":',
            log_manager=step_context.log,
        ):
            dagster_type = self.get_associated_input_def(step_context.job_def).dagster_type
            config_data = self.get_associated_config(step_context.resolved_run_config)
            loader = check.not_none(dagster_type.loader)
            yield loader.construct_from_config_value(
                step_context.get_type_loader_context(), config_data
            )

    def required_resource_keys(
        self, job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> AbstractSet[str]:
        dagster_type = self.get_associated_input_def(job_def).dagster_type
        return dagster_type.loader.required_resource_keys() if dagster_type.loader else set()


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
@record
class FromDirectInputValue(
    StepInputSource,
):
    """This input source is for direct python values to be passed as inputs to ops."""

    input_name: str

    def load_input_object(
        self, step_context: "StepExecutionContext", input_def: InputDefinition
    ) -> Iterator[object]:
        job_def = step_context.job_def
        yield job_def.get_direct_input_value(self.input_name)

    def required_resource_keys(
        self, _job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> set[str]:
        return set()


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
@record
class FromDefaultValue(StepInputSource):
    """This step input source is the default value declared on an InputDefinition."""

    node_handle: NodeHandle
    input_name: str

    def _load_value(self, pipeline_def: JobDefinition):
        return pipeline_def.get_node(self.node_handle).definition.default_value_for_input(
            self.input_name
        )

    def load_input_object(
        self,
        step_context: "StepExecutionContext",
        input_def: InputDefinition,
    ) -> Iterator[object]:
        yield self._load_value(step_context.job_def)


class MultiStepInputSource(StepInputSource, ABC):
    sources: Sequence[StepInputSource]

    @property
    def step_key_dependencies(self) -> AbstractSet[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        keys = set()
        for source in self.sources:
            keys.update(source.step_key_dependencies)

        return keys

    @property
    def step_output_handle_dependencies(self) -> Sequence[StepOutputHandle]:
        handles: list[StepOutputHandle] = []
        for source in self.sources:
            handles.extend(source.step_output_handle_dependencies)

        return handles

    def required_resource_keys(
        self, job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> set[str]:
        resource_keys: set[str] = set()
        for source in self.sources:
            resource_keys = resource_keys.union(
                source.required_resource_keys(job_def, op_handle, op_input_name)
            )
        return resource_keys


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
@record_custom
class FromMultipleSources(MultiStepInputSource, IHaveNew):
    """This step input is fans-in multiple sources in to a single input. The input will receive a list."""

    sources: Sequence[StepInputSource]
    # deprecated, preserved for back-compat
    node_handle: NodeHandle
    input_name: str

    def __new__(
        cls,
        sources: Sequence[StepInputSource],
        # deprecated, preserved for back-compat
        node_handle: Optional[NodeHandle] = None,
        input_name: Optional[str] = None,
    ):
        check.sequence_param(sources, "sources", StepInputSource)
        for source in sources:
            check.invariant(
                not isinstance(source, MultiStepInputSource),
                "Can not have multiple levels of MultiStepInputSource StepInputSource",
            )
        return super().__new__(
            cls,
            sources=sources,
            # add placeholder values for back-compat
            node_handle=node_handle or NodeHandle("", None),
            input_name=input_name or "",
        )

    def load_input_object(
        self,
        step_context: "StepExecutionContext",
        input_def: InputDefinition,
    ) -> Iterator[object]:
        from dagster._core.events import DagsterEvent

        # some upstream steps may have skipped and we allow fan-in to continue in their absence
        source_handles_to_skip = list(
            filter(
                lambda x: not step_context.can_load(x),
                self.step_output_handle_dependencies,
            )
        )

        values = []

        for inner_source in self.sources:
            if (
                isinstance(inner_source, FromStepOutput)
                and inner_source.step_output_handle in source_handles_to_skip
            ):
                continue

            for event_or_input_value in inner_source.load_input_object(step_context, input_def):
                if isinstance(event_or_input_value, DagsterEvent):
                    yield event_or_input_value
                else:
                    values.append(event_or_input_value)

        yield values


@whitelist_for_serdes
@record_custom
class FromMultipleSourcesLoadSingleSource(MultiStepInputSource, IHaveNew):
    """This step input fans-in multiple sources in to a single input. The input will receive just
    the value from loading source_to_load_from.
    """

    sources: Sequence[StepInputSource]
    source_to_load_from: StepInputSource

    def __new__(cls, sources: Sequence[StepInputSource], source_to_load_from: StepInputSource):
        check.sequence_param(sources, "sources", StepInputSource)
        for source in sources:
            check.invariant(
                not isinstance(source, MultiStepInputSource),
                "Can not have multiple levels of MultiStepInputSource StepInputSource",
            )
        return super().__new__(
            cls,
            sources=sources,
            source_to_load_from=source_to_load_from,
        )

    def load_input_object(
        self,
        step_context: "StepExecutionContext",
        input_def: InputDefinition,
    ) -> Iterator[object]:
        yield from self.source_to_load_from.load_input_object(step_context, input_def)


def _load_input_with_input_manager(
    input_manager: "InputManager", context: "InputContext"
) -> Iterator[object]:
    step_context = cast("StepExecutionContext", context.step_context)
    with op_execution_error_boundary(
        DagsterExecutionLoadInputError,
        msg_fn=lambda: f'Error occurred while loading input "{context.name}" of step "{step_context.step.key}":',
        step_context=step_context,
        step_key=step_context.step.key,
        input_name=context.name,
    ):
        value = input_manager.load_input(context)
    # close user code boundary before returning value
    yield from context.consume_events()

    yield value


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
@record_custom
class FromPendingDynamicStepOutput(IHaveNew):
    """This step input source models being directly downstream of a step with dynamic output.
    Once that step completes successfully, this will resolve once per DynamicOutput.
    """

    step_output_handle: StepOutputHandle
    # deprecated, preserved for back-compat
    node_handle: NodeHandle
    input_name: str

    def __new__(
        cls,
        step_output_handle: StepOutputHandle,
        # deprecated, preserved for back-compat
        node_handle: Optional[NodeHandle] = None,
        input_name: Optional[str] = None,
    ):
        # Model the unknown mapping key from known execution step
        # using a StepOutputHandle with None mapping_key.
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        check.invariant(step_output_handle.mapping_key is None)

        return super().__new__(
            cls,
            step_output_handle=step_output_handle,
            # add placeholder values for back-compat
            node_handle=node_handle or NodeHandle("", None),
            input_name=input_name or "",
        )

    @property
    def resolved_by_step_key(self) -> str:
        return self.step_output_handle.step_key

    @property
    def resolved_by_output_name(self) -> str:
        return self.step_output_handle.output_name

    def resolve(self, mapping_key: str) -> FromStepOutput:
        check.str_param(mapping_key, "mapping_key")
        return FromStepOutput(
            step_output_handle=StepOutputHandle(
                step_key=self.step_output_handle.step_key,
                output_name=self.step_output_handle.output_name,
                mapping_key=mapping_key,
            ),
            fan_in=False,
        )

    def get_step_output_handle_dep_with_placeholder(self) -> StepOutputHandle:
        # None mapping_key on StepOutputHandle acts as placeholder
        return self.step_output_handle

    def required_resource_keys(
        self, _job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> set[str]:
        return set()


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
@record_custom
class FromUnresolvedStepOutput(IHaveNew):
    """This step input source models being downstream of another unresolved step,
    for example indirectly downstream from a step with dynamic output.
    """

    unresolved_step_output_handle: UnresolvedStepOutputHandle
    # deprecated, preserved for back-compat
    node_handle: NodeHandle
    input_name: str

    def __new__(
        cls,
        unresolved_step_output_handle: UnresolvedStepOutputHandle,
        # deprecated, preserved for back-compat
        node_handle: Optional[NodeHandle] = None,
        input_name: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            unresolved_step_output_handle=unresolved_step_output_handle,
            # add placeholder values for back-compat
            node_handle=node_handle or NodeHandle("", None),
            input_name=input_name or "",
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
            fan_in=False,
        )

    def get_step_output_handle_dep_with_placeholder(self) -> StepOutputHandle:
        return self.unresolved_step_output_handle.get_step_output_handle_with_placeholder()

    def required_resource_keys(
        self, _job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> set[str]:
        return set()


@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
@record_custom
class FromDynamicCollect(IHaveNew):
    source: Union[FromPendingDynamicStepOutput, FromUnresolvedStepOutput]
    # deprecated, preserved for back-compat
    node_handle: NodeHandle
    input_name: str

    def __new__(
        cls,
        source: Union[FromPendingDynamicStepOutput, FromUnresolvedStepOutput],
        # deprecated, preserved for back-compat
        node_handle: Optional[NodeHandle] = None,
        input_name: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            source=source,
            # add placeholder values for back-compat
            node_handle=node_handle or NodeHandle("", None),
            input_name=input_name or "",
        )

    @property
    def resolved_by_step_key(self) -> str:
        return self.source.resolved_by_step_key

    @property
    def resolved_by_output_name(self) -> str:
        return self.source.resolved_by_output_name

    def get_step_output_handle_dep_with_placeholder(self) -> StepOutputHandle:
        return self.source.get_step_output_handle_dep_with_placeholder()

    def required_resource_keys(
        self, _job_def: JobDefinition, op_handle: NodeHandle, op_input_name: str
    ) -> set[str]:
        return set()

    def resolve(self, mapping_keys: Optional[Sequence[str]]):
        if mapping_keys is None:
            # None means that the dynamic output was skipped, so create
            # a dependency on the dynamic output that will continue cascading the skip
            return FromStepOutput(
                step_output_handle=StepOutputHandle(
                    step_key=self.resolved_by_step_key,
                    output_name=self.resolved_by_output_name,
                ),
                fan_in=False,
            )
        return FromMultipleSources(
            sources=[self.source.resolve(map_key) for map_key in mapping_keys],
        )


@record
class UnresolvedMappedStepInput:
    """Holds information for how to resolve a StepInput once the upstream mapping is done."""

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

    def get_step_output_handle_deps_with_placeholders(self) -> Sequence[StepOutputHandle]:
        """Return StepOutputHandles with placeholders, unresolved step keys and None mapping keys."""
        return [self.source.get_step_output_handle_dep_with_placeholder()]


@record
class UnresolvedCollectStepInput:
    """Holds information for how to resolve a StepInput once the upstream mapping is done."""

    name: str
    dagster_type_key: str
    source: FromDynamicCollect

    @property
    def resolved_by_step_key(self) -> str:
        return self.source.resolved_by_step_key

    @property
    def resolved_by_output_name(self) -> str:
        return self.source.resolved_by_output_name

    def resolve(self, mapping_keys: Optional[Sequence[str]]) -> StepInput:
        return StepInput(
            name=self.name,
            dagster_type_key=self.dagster_type_key,
            source=self.source.resolve(mapping_keys),
        )

    def get_step_output_handle_deps_with_placeholders(self) -> Sequence[StepOutputHandle]:
        """Return StepOutputHandles with placeholders, unresolved step keys and None mapping keys."""
        return [self.source.get_step_output_handle_dep_with_placeholder()]


StepInputSourceUnion = Union[
    StepInputSource,
    FromDynamicCollect,
    FromUnresolvedStepOutput,
    FromPendingDynamicStepOutput,
]

StepInputSourceTypes = StepInputSourceUnion.__args__  # type: ignore

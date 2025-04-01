from abc import abstractmethod
from asyncio import AbstractEventLoop
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from typing import AbstractSet, Any, NamedTuple, Optional, Union, cast  # noqa: UP035

import dagster._check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.composition import PendingNodeInvocation
from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction
from dagster._core.definitions.dependency import Node, NodeHandle
from dagster._core.definitions.events import (
    AssetMaterialization,
    AssetObservation,
    ExpectationResult,
    UserEvent,
)
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.definitions.resource_definition import (
    IContainsGenerator,
    ResourceDefinition,
    Resources,
    ScopedResourcesBuilder,
)
from dagster._core.definitions.resource_requirement import ensure_requirements_satisfied
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    has_one_dimension_time_window_partitioning,
)
from dagster._core.errors import (
    DagsterInvalidInvocationError,
    DagsterInvalidPropertyError,
    DagsterInvariantViolationError,
)
from dagster._core.execution.build_resources import build_resources, wrap_resources_for_execution
from dagster._core.execution.context.compute import AssetExecutionContext, OpExecutionContext
from dagster._core.execution.context.system import StepExecutionContext, TypeCheckContext
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.forked_pdb import ForkedPdb
from dagster._utils.merger import merge_dicts


def _property_msg(prop_name: str, method_name: str) -> str:
    return f"The {prop_name} {method_name} is not set on the context when an asset or op is directly invoked."


class BaseDirectExecutionContext:
    """Base class for any direct invocation execution contexts. Each type of execution context
    (ex. OpExecutionContext, AssetExecutionContext) needs to have a variant for direct invocation.
    Those direct invocation contexts have some methods that are not available until the context
    is bound to a particular op/asset. The "bound" properties are held in PerInvocationProperties.
    There are also some properties that are specific to a particular execution of an op/asset, these
    properties are held in DirectExecutionProperties. Direct invocation contexts must
    be able to be bound and unbound from a particular op/asset. Additionally, there are some methods
    that all direct invocation contexts must implement so that the will be usable in the execution
    code path.
    """

    @abstractmethod
    def bind(
        self,
        op_def: OpDefinition,
        pending_invocation: Optional[PendingNodeInvocation[OpDefinition]],
        assets_def: Optional[AssetsDefinition],
        config_from_args: Optional[Mapping[str, Any]],
        resources_from_args: Optional[Mapping[str, Any]],
    ):
        """Subclasses of BaseDirectExecutionContext must implement bind."""

    @abstractmethod
    def unbind(self):
        """Subclasses of BaseDirectExecutionContext must implement unbind."""

    @property
    @abstractmethod
    def per_invocation_properties(self) -> "PerInvocationProperties":
        """Subclasses of BaseDirectExecutionContext must contain a PerInvocationProperties object."""

    @property
    @abstractmethod
    def execution_properties(self) -> "DirectExecutionProperties":
        """Subclasses of BaseDirectExecutionContext must contain a DirectExecutionProperties object."""

    @abstractmethod
    def for_type(self, dagster_type: DagsterType) -> TypeCheckContext:
        """Subclasses of BaseDirectExecutionContext must implement for_type."""
        pass

    @abstractmethod
    def observe_output(self, output_name: str, mapping_key: Optional[str] = None) -> None:
        """Subclasses of BaseDirectExecutionContext must implement observe_output."""
        pass


class PerInvocationProperties(
    NamedTuple(
        "_PerInvocationProperties",
        [
            ("op_def", OpDefinition),
            ("tags", Mapping[Any, Any]),
            ("hook_defs", Optional[AbstractSet[HookDefinition]]),
            ("alias", str),
            ("assets_def", Optional[AssetsDefinition]),
            ("resources", Resources),
            ("op_config", Any),
            ("step_description", str),
        ],
    )
):
    """Maintains properties that are only available once the context has been bound to a particular
    asset or op invocation. By splitting these out into a separate object, it is easier to ensure that
    all properties bound to an invocation are cleared once the execution is complete.
    """

    def __new__(
        cls,
        op_def: OpDefinition,
        tags: Mapping[Any, Any],
        hook_defs: Optional[AbstractSet[HookDefinition]],
        alias: str,
        assets_def: Optional[AssetsDefinition],
        resources: Resources,
        op_config: Any,
        step_description: str,
    ):
        return super().__new__(
            cls,
            op_def=check.inst_param(op_def, "op_def", OpDefinition),
            tags=check.dict_param(tags, "tags"),
            hook_defs=check.opt_set_param(hook_defs, "hook_defs", HookDefinition),
            alias=check.str_param(alias, "alias"),
            assets_def=check.opt_inst_param(assets_def, "assets_def", AssetsDefinition),
            resources=check.inst_param(resources, "resources", Resources),
            op_config=op_config,
            step_description=step_description,
        )


class DirectExecutionProperties:
    """Maintains information about the execution that can only be updated during execution (when
    the context is bound), but can be read after execution is complete. It needs to be cleared before
    the context is used for another execution.

    This is not implemented as a NamedTuple because the various attributes will be mutated during
    execution.
    """

    def __init__(self):
        self.user_events: list[UserEvent] = []
        self.seen_outputs: dict[str, Union[str, set[str]]] = {}
        self.output_metadata: dict[str, dict[str, Union[Any, Mapping[str, Any]]]] = {}
        self.requires_typed_event_stream: bool = False
        self.typed_event_stream_error_message: Optional[str] = None


class DirectOpExecutionContext(OpExecutionContext, BaseDirectExecutionContext):
    """The ``context`` object available as the first argument to an op's compute function when
    being invoked directly. Can also be used as a context manager.
    """

    def __init__(
        self,
        op_config: Any,
        resources_dict: Mapping[str, Any],
        resources_config: Mapping[str, Any],
        instance: Optional[DagsterInstance],
        partition_key: Optional[str],
        partition_key_range: Optional[PartitionKeyRange],
        mapping_key: Optional[str],
        run_tags: Mapping[str, str],
        event_loop: Optional[AbstractEventLoop],
    ):
        from dagster._core.execution.api import ephemeral_instance_if_missing
        from dagster._core.execution.context_creation_job import initialize_console_manager

        self._op_config = op_config
        self._mapping_key = mapping_key

        self._exit_stack = ExitStack()

        # Construct ephemeral instance if missing
        self._instance = self._exit_stack.enter_context(ephemeral_instance_if_missing(instance))

        self._resources_config = resources_config
        # Open resource context manager
        self._resources_contain_cm = False
        self._resource_defs = wrap_resources_for_execution(resources_dict)
        self._resources = self._exit_stack.enter_context(
            build_resources(
                resources=self._resource_defs,
                instance=self._instance,
                resource_config=resources_config,
                event_loop=event_loop,
            )
        )
        self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)

        self._log = initialize_console_manager(None)
        self._pdb: Optional[ForkedPdb] = None
        self._cm_scope_entered = False
        check.invariant(
            not (partition_key and partition_key_range),
            "Must supply at most one of partition_key or partition_key_range",
        )
        self._partition_key = partition_key
        self._partition_key_range = partition_key_range
        self._run_tags = run_tags
        self._event_loop = event_loop

        # Maintains the properties on the context that are bound to a particular invocation
        # of an op
        # @op
        # def my_op(context):
        #     # context._per_invocation_properties.alias is "my_op"
        #     ...
        # ctx = build_op_context() # ctx._per_invocation_properties is None
        # my_op(ctx)
        # ctx._per_invocation_properties is None # ctx is unbound at the end of invocation
        self._per_invocation_properties = None

        # Maintains the properties on the context that are modified during invocation
        # @op
        # def my_op(context):
        #     # context._execution_properties can be modified with output metadata etc.
        #     ...
        # ctx = build_op_context() # ctx._execution_properties is empty
        # my_op(ctx)
        # ctx._execution_properties.output_metadata # information is retained after invocation
        # my_op(ctx) # ctx._execution_properties is cleared at the beginning of the next invocation
        self._execution_properties = DirectExecutionProperties()

    def __enter__(self):
        self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        self._exit_stack.close()

    def __del__(self):
        self._exit_stack.close()

    def _check_bound_to_invocation(self, fn_name: str, fn_type: str) -> PerInvocationProperties:
        if self._per_invocation_properties is None:
            raise DagsterInvalidPropertyError(_property_msg(fn_name, fn_type))
        # return self._per_invocation_properties so that the calling function can access properties
        # of self._per_invocation_properties without causing pyright errors
        return self._per_invocation_properties

    def bind(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        op_def: OpDefinition,
        pending_invocation: Optional[PendingNodeInvocation[OpDefinition]],
        assets_def: Optional[AssetsDefinition],
        config_from_args: Optional[Mapping[str, Any]],
        resources_from_args: Optional[Mapping[str, Any]],
    ) -> "DirectOpExecutionContext":
        from dagster._core.definitions.resource_invocation import resolve_bound_config

        if self._per_invocation_properties is not None:
            raise DagsterInvalidInvocationError(
                f"This context is currently being used to execute {self.alias}. The context cannot be used to execute another op until {self.alias} has finished executing."
            )

        # reset execution_properties
        self._execution_properties = DirectExecutionProperties()

        # update the bound context with properties relevant to the invocation of the op
        invocation_tags = (
            pending_invocation.tags
            if isinstance(pending_invocation, PendingNodeInvocation)
            else None
        )
        tags = merge_dicts(op_def.tags, invocation_tags) if invocation_tags else op_def.tags

        hook_defs = (
            pending_invocation.hook_defs
            if isinstance(pending_invocation, PendingNodeInvocation)
            else None
        )
        invocation_alias = (
            pending_invocation.given_alias
            if isinstance(pending_invocation, PendingNodeInvocation)
            else None
        )
        alias = invocation_alias if invocation_alias else op_def.name

        if resources_from_args:
            if self._resource_defs:
                raise DagsterInvalidInvocationError(
                    "Cannot provide resources in both context and kwargs"
                )
            resource_defs = wrap_resources_for_execution(resources_from_args)
            # add new resources context to the stack to be cleared on exit
            resources = self._exit_stack.enter_context(
                build_resources(
                    resource_defs,
                    self.instance,
                    event_loop=self._event_loop,
                )
            )
        elif assets_def and assets_def.resource_defs:
            for key in sorted(list(assets_def.resource_defs.keys())):
                if key in self._resource_defs:
                    raise DagsterInvalidInvocationError(
                        f"Error when invoking {assets_def!s} resource '{key}' "
                        "provided on both the definition and invocation context. Please "
                        "provide on only one or the other."
                    )
            resource_defs = wrap_resources_for_execution(
                {**self._resource_defs, **assets_def.resource_defs}
            )
            # add new resources context to the stack to be cleared on exit
            resources = self._exit_stack.enter_context(
                build_resources(
                    resource_defs,
                    self.instance,
                    self._resources_config,
                    event_loop=self._event_loop,
                )
            )
        else:
            # this runs the check in resources() to ensure we are in a context manager if necessary
            resources = self.resources

            resource_defs = self._resource_defs

        _validate_resource_requirements(resource_defs, op_def)

        if self._op_config and config_from_args:
            raise DagsterInvalidInvocationError("Cannot provide config in both context and kwargs")
        op_config = resolve_bound_config(config_from_args or self._op_config, op_def)

        step_description = f'op "{op_def.name}"'

        self._per_invocation_properties = PerInvocationProperties(
            op_def=op_def,
            tags=tags,
            hook_defs=hook_defs,
            alias=alias,
            assets_def=assets_def,
            resources=resources,
            op_config=op_config,
            step_description=step_description,
        )

        return self

    def unbind(self):
        self._per_invocation_properties = None

    @property
    def is_bound(self) -> bool:
        return self._per_invocation_properties is not None

    @property
    def execution_properties(self) -> DirectExecutionProperties:
        return self._execution_properties

    @property
    def per_invocation_properties(self) -> PerInvocationProperties:
        return self._check_bound_to_invocation(
            fn_name="_per_invocation_properties", fn_type="property"
        )

    @property
    def op_config(self) -> Any:
        if self._per_invocation_properties is None:
            return self._op_config
        return self._per_invocation_properties.op_config

    @property
    def resource_keys(self) -> AbstractSet[str]:
        return self._resource_defs.keys()

    @property
    def resources(self) -> Resources:
        if self._per_invocation_properties is not None:
            return self._per_invocation_properties.resources
        if self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_op_context(...) as context:`"
            )
        return self._resources

    @property
    def dagster_run(self) -> DagsterRun:
        raise DagsterInvalidPropertyError(_property_msg("dagster_run", "property"))

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    @property
    def pdb(self) -> ForkedPdb:
        """dagster.utils.forked_pdb.ForkedPdb: Gives access to pdb debugging from within the solid.

        Example:
        .. code-block:: python

            @solid
            def debug_solid(context):
                context.pdb.set_trace()

        """
        if self._pdb is None:
            self._pdb = ForkedPdb()

        return self._pdb

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        raise DagsterInvalidPropertyError(_property_msg("step_launcher", "property"))

    @property
    def run_id(self) -> str:
        """str: Hard-coded value to indicate that we are directly invoking solid."""
        return "EPHEMERAL"

    @property
    def run_config(self) -> dict:
        per_invocation_properties = self._check_bound_to_invocation(
            fn_name="run_config", fn_type="property"
        )

        run_config: dict[str, object] = {}
        if self._op_config and per_invocation_properties.op_def:
            run_config["ops"] = {
                per_invocation_properties.op_def.name: {
                    "config": per_invocation_properties.op_config
                }
            }
        run_config["resources"] = self._resources_config
        return run_config

    @property
    def job_def(self) -> JobDefinition:
        raise DagsterInvalidPropertyError(_property_msg("job_def", "property"))

    @property
    def repository_def(self) -> RepositoryDefinition:
        raise DagsterInvalidPropertyError(_property_msg("repository_def", "property"))

    @property
    def job_name(self) -> str:
        raise DagsterInvalidPropertyError(_property_msg("job_name", "property"))

    @property
    def log(self) -> DagsterLogManager:
        """DagsterLogManager: A console manager constructed for this context."""
        return self._log

    @property
    def node_handle(self) -> NodeHandle:
        raise DagsterInvalidPropertyError(_property_msg("node_handle", "property"))

    @property
    def op(self) -> Node:
        raise DagsterInvalidPropertyError(_property_msg("op", "property"))

    @property
    def solid(self) -> Node:
        raise DagsterInvalidPropertyError(_property_msg("solid", "property"))

    @property
    def op_def(self) -> OpDefinition:
        per_invocation_properties = self._check_bound_to_invocation(
            fn_name="op_def", fn_type="property"
        )
        return cast(OpDefinition, per_invocation_properties.op_def)

    @property
    def has_assets_def(self) -> bool:
        per_invocation_properties = self._check_bound_to_invocation(
            fn_name="has_assets_def", fn_type="property"
        )
        return per_invocation_properties.assets_def is not None

    @property
    def assets_def(self) -> AssetsDefinition:
        per_invocation_properties = self._check_bound_to_invocation(
            fn_name="assets_def", fn_type="property"
        )

        if per_invocation_properties.assets_def is None:
            raise DagsterInvalidPropertyError(
                f"Op {self.op_def.name} does not have an assets definition."
            )
        return per_invocation_properties.assets_def

    @property
    def has_partition_key(self) -> bool:
        return self._partition_key is not None

    @property
    def partition_key(self) -> str:
        if self._partition_key:
            return self._partition_key
        check.failed("Tried to access partition_key for a non-partitioned run")

    @property
    def partition_keys(self) -> Sequence[str]:
        key_range = self.partition_key_range
        partitions_def = self.assets_def.partitions_def
        if partitions_def is None:
            raise DagsterInvariantViolationError(
                "Cannot access partition_keys for a non-partitioned run"
            )

        return partitions_def.get_partition_keys_in_range(
            key_range,
            dynamic_partitions_store=self.instance,
        )

    @property
    def partition_key_range(self) -> PartitionKeyRange:
        """The range of partition keys for the current run.

        If run is for a single partition key, return a `PartitionKeyRange` with the same start and
        end. Raises an error if the current run is not a partitioned run.
        """
        if self._partition_key_range:
            return self._partition_key_range
        elif self._partition_key:
            return PartitionKeyRange(self._partition_key, self._partition_key)
        else:
            check.failed("Tried to access partition_key range for a non-partitioned run")

    def asset_partition_key_for_output(self, output_name: str = "result") -> str:
        return self.partition_key

    def has_tag(self, key: str) -> bool:
        return key in self._run_tags

    def get_tag(self, key: str) -> Optional[str]:
        return self._run_tags.get(key)

    @property
    def run_tags(self) -> Mapping[str, str]:
        return self._run_tags

    @property
    def alias(self) -> str:
        per_invocation_properties = self._check_bound_to_invocation(
            fn_name="alias", fn_type="property"
        )
        return cast(str, per_invocation_properties.alias)

    def get_step_execution_context(self) -> StepExecutionContext:
        raise DagsterInvalidPropertyError(_property_msg("get_step_execution_context", "method"))

    def get_events(self) -> Sequence[UserEvent]:
        """Retrieve the list of user-generated events that were logged via the context.

        **Examples:**

        .. code-block:: python

            from dagster import op, build_op_context, AssetMaterialization, ExpectationResult

            @op
            def my_op(context):
                ...

            def test_my_op():
                context = build_op_context()
                my_op(context)
                all_user_events = context.get_events()
                materializations = [event for event in all_user_events if isinstance(event, AssetMaterialization)]
                expectation_results = [event for event in all_user_events if isinstance(event, ExpectationResult)]
                ...
        """
        return self._execution_properties.user_events

    def get_output_metadata(
        self, output_name: str, mapping_key: Optional[str] = None
    ) -> Optional[Mapping[str, Any]]:
        """Retrieve metadata that was logged for an output and mapping_key, if it exists.

        If metadata cannot be found for the particular output_name/mapping_key combination, None will be returned.

        Args:
            output_name (str): The name of the output to retrieve logged metadata for.
            mapping_key (Optional[str]): The mapping key to retrieve metadata for (only applies when using dynamic outputs).

        Returns:
            Optional[Mapping[str, Any]]: The metadata values present for the output_name/mapping_key combination, if present.
        """
        metadata = self._execution_properties.output_metadata.get(output_name)
        if mapping_key and metadata:
            return metadata.get(mapping_key)
        return metadata

    def get_mapping_key(self) -> Optional[str]:
        return self._mapping_key

    def for_type(self, dagster_type: DagsterType) -> TypeCheckContext:
        self._check_bound_to_invocation(fn_name="for_type", fn_type="method")
        resources = cast(NamedTuple, self.resources)
        return TypeCheckContext(
            self.run_id,
            self.log,
            ScopedResourcesBuilder(resources._asdict()),
            dagster_type,
        )

    def describe_op(self) -> str:
        per_invocation_properties = self._check_bound_to_invocation(
            fn_name="describe_op", fn_type="method"
        )
        return per_invocation_properties.step_description

    def log_event(self, event: UserEvent) -> None:
        self._check_bound_to_invocation(fn_name="log_event", fn_type="method")
        check.inst_param(
            event,
            "event",
            (AssetMaterialization, AssetObservation, ExpectationResult),
        )
        self._execution_properties.user_events.append(event)

    def observe_output(self, output_name: str, mapping_key: Optional[str] = None) -> None:
        self._check_bound_to_invocation(fn_name="observe_output", fn_type="method")
        if mapping_key:
            if output_name not in self._execution_properties.seen_outputs:
                self._execution_properties.seen_outputs[output_name] = set()
            cast(set[str], self._execution_properties.seen_outputs[output_name]).add(mapping_key)
        else:
            self._execution_properties.seen_outputs[output_name] = "seen"

    def has_seen_output(self, output_name: str, mapping_key: Optional[str] = None) -> bool:
        if mapping_key:
            return (
                output_name in self._execution_properties.seen_outputs
                and mapping_key in self._execution_properties.seen_outputs[output_name]
            )
        return output_name in self._execution_properties.seen_outputs

    def asset_partitions_time_window_for_output(self, output_name: str = "result") -> TimeWindow:
        self._check_bound_to_invocation(
            fn_name="asset_partitions_time_window_for_output", fn_type="method"
        )
        partitions_def = self.assets_def.partitions_def
        if partitions_def is None:
            check.failed("Tried to access partition_key for a non-partitioned asset")

        if not has_one_dimension_time_window_partitioning(partitions_def=partitions_def):
            raise DagsterInvariantViolationError(
                "Expected a TimeWindowPartitionsDefinition or MultiPartitionsDefinition with a"
                f" single time dimension, but instead found {type(partitions_def)}"
            )

        return cast(
            Union[MultiPartitionsDefinition, TimeWindowPartitionsDefinition], partitions_def
        ).time_window_for_partition_key(self.partition_key)

    @property
    def partition_time_window(self) -> TimeWindow:
        return self.asset_partitions_time_window_for_output()

    def add_output_metadata(
        self,
        metadata: Mapping[str, Any],
        output_name: Optional[str] = None,
        mapping_key: Optional[str] = None,
    ) -> None:
        """Add metadata to one of the outputs of an op.

        This can only be used once per output in the body of an op. Using this method with the same output_name more than once within an op will result in an error.

        Args:
            metadata (Mapping[str, Any]): The metadata to attach to the output
            output_name (Optional[str]): The name of the output to attach metadata to. If there is only one output on the op, then this argument does not need to be provided. The metadata will automatically be attached to the only output.

        **Examples:**

        .. code-block:: python

            from dagster import Out, op
            from typing import Tuple

            @op
            def add_metadata(context):
                context.add_output_metadata({"foo", "bar"})
                return 5 # Since the default output is called "result", metadata will be attached to the output "result".

            @op(out={"a": Out(), "b": Out()})
            def add_metadata_two_outputs(context) -> Tuple[str, int]:
                context.add_output_metadata({"foo": "bar"}, output_name="b")
                context.add_output_metadata({"baz": "bat"}, output_name="a")

                return ("dog", 5)

        """
        self._check_bound_to_invocation(fn_name="add_output_metadata", fn_type="method")
        metadata = check.mapping_param(metadata, "metadata", key_type=str)
        output_name = check.opt_str_param(output_name, "output_name")
        mapping_key = check.opt_str_param(mapping_key, "mapping_key")

        if output_name is None and len(self.op_def.output_defs) == 1:
            output_def = self.op_def.output_defs[0]
            output_name = output_def.name
        elif output_name is None:
            raise DagsterInvariantViolationError(
                "Attempted to log metadata without providing output_name, but multiple outputs"
                " exist. Please provide an output_name to the invocation of"
                " `context.add_output_metadata`."
            )
        else:
            output_def = self.op_def.output_def_named(output_name)

        if self.has_seen_output(output_name, mapping_key):
            output_desc = (
                f"output '{output_def.name}'"
                if not mapping_key
                else f"output '{output_def.name}' with mapping_key '{mapping_key}'"
            )
            raise DagsterInvariantViolationError(
                f"In {self.op_def.node_type_str} '{self.op_def.name}', attempted to log output"
                f" metadata for {output_desc} which has already been yielded. Metadata must be"
                " logged before the output is yielded."
            )
        if output_def.is_dynamic and not mapping_key:
            raise DagsterInvariantViolationError(
                f"In {self.op_def.node_type_str} '{self.op_def.name}', attempted to log metadata"
                f" for dynamic output '{output_def.name}' without providing a mapping key. When"
                " logging metadata for a dynamic output, it is necessary to provide a mapping key."
            )

        output_name = output_def.name
        if output_name in self._execution_properties.output_metadata:
            if (
                not mapping_key
                or mapping_key in self._execution_properties.output_metadata[output_name]
            ):
                raise DagsterInvariantViolationError(
                    f"In {self.op_def.node_type_str} '{self.op_def.name}', attempted to log"
                    f" metadata for output '{output_name}' more than once."
                )
        if mapping_key:
            if output_name not in self._execution_properties.output_metadata:
                self._execution_properties.output_metadata[output_name] = {}
            self._execution_properties.output_metadata[output_name][mapping_key] = metadata

        else:
            self._execution_properties.output_metadata[output_name] = metadata  # pyright: ignore[reportArgumentType]

    # In bound mode no conversion is done on returned values and missing but expected outputs are not
    # allowed.
    @property
    def requires_typed_event_stream(self) -> bool:
        self._check_bound_to_invocation(fn_name="requires_typed_event_stream", fn_type="property")
        return self._execution_properties.requires_typed_event_stream

    @property
    def typed_event_stream_error_message(self) -> Optional[str]:
        self._check_bound_to_invocation(
            fn_name="typed_event_stream_error_message", fn_type="property"
        )
        return self._execution_properties.typed_event_stream_error_message

    def set_requires_typed_event_stream(self, *, error_message: Optional[str]) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        self._check_bound_to_invocation(fn_name="set_requires_typed_event_stream", fn_type="method")
        self._execution_properties.requires_typed_event_stream = True
        self._execution_properties.typed_event_stream_error_message = error_message


class DirectAssetExecutionContext(AssetExecutionContext, BaseDirectExecutionContext):
    """The ``context`` object available as the first argument to an asset's compute function when
    being invoked directly. Can also be used as a context manager.
    """

    def __init__(self, op_execution_context: DirectOpExecutionContext):
        self._op_execution_context = op_execution_context

    def __enter__(self):
        self.op_execution_context._cm_scope_entered = True  # noqa: SLF001
        return self

    def __exit__(self, *exc):
        self.op_execution_context._exit_stack.close()  # noqa: SLF001

    def __del__(self):
        self.op_execution_context._exit_stack.close()  # noqa: SLF001

    def _check_bound_to_invocation(self, fn_name: str, fn_type: str):
        if not self._op_execution_context._per_invocation_properties:  # noqa: SLF001
            raise DagsterInvalidPropertyError(_property_msg(fn_name, fn_type))

    def bind(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        op_def: OpDefinition,
        pending_invocation: Optional[PendingNodeInvocation[OpDefinition]],
        assets_def: Optional[AssetsDefinition],
        config_from_args: Optional[Mapping[str, Any]],
        resources_from_args: Optional[Mapping[str, Any]],
    ) -> "DirectAssetExecutionContext":
        if assets_def is None:
            raise DagsterInvariantViolationError(
                "DirectAssetExecutionContext can only being used to invoke an asset."
            )
        if self._op_execution_context._per_invocation_properties is not None:  # noqa: SLF001
            raise DagsterInvalidInvocationError(
                f"This context is currently being used to execute {self.op_execution_context.alias}."
                " The context cannot be used to execute another asset until"
                f" {self.op_execution_context.alias} has finished executing."
            )

        self._op_execution_context = self._op_execution_context.bind(
            op_def=op_def,
            pending_invocation=pending_invocation,
            assets_def=assets_def,
            config_from_args=config_from_args,
            resources_from_args=resources_from_args,
        )

        return self

    def unbind(self):
        self._op_execution_context.unbind()

    @property
    def per_invocation_properties(self) -> PerInvocationProperties:
        return self.op_execution_context.per_invocation_properties

    @property
    def is_bound(self) -> bool:
        return self.op_execution_context.is_bound

    @property
    def execution_properties(self) -> DirectExecutionProperties:
        return self.op_execution_context.execution_properties

    @property
    def op_execution_context(self) -> DirectOpExecutionContext:
        return self._op_execution_context

    def for_type(self, dagster_type: DagsterType) -> TypeCheckContext:
        return self.op_execution_context.for_type(dagster_type)

    def observe_output(self, output_name: str, mapping_key: Optional[str] = None) -> None:
        self.op_execution_context.observe_output(output_name=output_name, mapping_key=mapping_key)


def _validate_resource_requirements(
    resource_defs: Mapping[str, ResourceDefinition], op_def: OpDefinition
) -> None:
    """Validate correctness of resources against required resource keys."""
    if cast(DecoratedOpFunction, op_def.compute_fn).has_context_arg():
        for requirement in op_def.get_resource_requirements(
            asset_layer=None,
            handle=None,
        ):
            if not requirement.is_io_manager_requirement:
                ensure_requirements_satisfied(resource_defs, [requirement])


def build_op_context(
    resources: Optional[Mapping[str, Any]] = None,
    op_config: Any = None,
    resources_config: Optional[Mapping[str, Any]] = None,
    instance: Optional[DagsterInstance] = None,
    config: Any = None,
    partition_key: Optional[str] = None,
    partition_key_range: Optional[PartitionKeyRange] = None,
    mapping_key: Optional[str] = None,
    run_tags: Optional[Mapping[str, str]] = None,
    event_loop: Optional[AbstractEventLoop] = None,
) -> DirectOpExecutionContext:
    """Builds op execution context from provided parameters.

    ``build_op_context`` can be used as either a function or context manager. If there is a
    provided resource that is a context manager, then ``build_op_context`` must be used as a
    context manager. This function can be used to provide the context argument when directly
    invoking a op.

    Args:
        resources (Optional[Dict[str, Any]]): The resources to provide to the context. These can be
            either values or resource definitions.
        op_config (Optional[Mapping[str, Any]]): The config to provide to the op.
        resources_config (Optional[Mapping[str, Any]]): The config to provide to the resources.
        instance (Optional[DagsterInstance]): The dagster instance configured for the context.
            Defaults to DagsterInstance.ephemeral().
        mapping_key (Optional[str]): A key representing the mapping key from an upstream dynamic
            output. Can be accessed using ``context.get_mapping_key()``.
        partition_key (Optional[str]): String value representing partition key to execute with.
        partition_key_range (Optional[PartitionKeyRange]): Partition key range to execute with.
        run_tags: Optional[Mapping[str, str]]: The tags for the executing run.
        event_loop: Optional[AbstractEventLoop]: An event loop for handling resources
            with async context managers.

    Examples:
        .. code-block:: python

            context = build_op_context()
            op_to_invoke(context)

            with build_op_context(resources={"foo": context_manager_resource}) as context:
                op_to_invoke(context)
    """
    if op_config and config:
        raise DagsterInvalidInvocationError(
            "Attempted to invoke ``build_op_context`` with both ``op_config``, and its "
            "legacy version, ``config``. Please provide one or the other."
        )

    op_config = op_config if op_config else config
    return DirectOpExecutionContext(
        resources_dict=check.opt_mapping_param(resources, "resources", key_type=str),
        resources_config=check.opt_mapping_param(
            resources_config, "resources_config", key_type=str
        ),
        op_config=op_config,
        instance=check.opt_inst_param(instance, "instance", DagsterInstance),
        partition_key=check.opt_str_param(partition_key, "partition_key"),
        partition_key_range=check.opt_inst_param(
            partition_key_range, "partition_key_range", PartitionKeyRange
        ),
        mapping_key=check.opt_str_param(mapping_key, "mapping_key"),
        run_tags=check.opt_mapping_param(run_tags, "run_tags", key_type=str),
        event_loop=event_loop,
    )


def build_asset_context(
    resources: Optional[Mapping[str, Any]] = None,
    resources_config: Optional[Mapping[str, Any]] = None,
    asset_config: Optional[Mapping[str, Any]] = None,
    instance: Optional[DagsterInstance] = None,
    partition_key: Optional[str] = None,
    partition_key_range: Optional[PartitionKeyRange] = None,
    run_tags: Optional[Mapping[str, str]] = None,
    event_loop: Optional[AbstractEventLoop] = None,
) -> DirectAssetExecutionContext:
    """Builds asset execution context from provided parameters.

    ``build_asset_context`` can be used as either a function or context manager. If there is a
    provided resource that is a context manager, then ``build_asset_context`` must be used as a
    context manager. This function can be used to provide the context argument when directly
    invoking an asset.

    Args:
        resources (Optional[Dict[str, Any]]): The resources to provide to the context. These can be
            either values or resource definitions.
        resources_config (Optional[Mapping[str, Any]]): The config to provide to the resources.
        asset_config (Optional[Mapping[str, Any]]): The config to provide to the asset.
        instance (Optional[DagsterInstance]): The dagster instance configured for the context.
            Defaults to DagsterInstance.ephemeral().
        partition_key (Optional[str]): String value representing partition key to execute with.
        partition_key_range (Optional[PartitionKeyRange]): Partition key range to execute with.
        run_tags: Optional[Mapping[str, str]]: The tags for the executing run.
        event_loop: Optional[AbstractEventLoop]: An event loop for handling resources
            with async context managers.


    Examples:
        .. code-block:: python

            context = build_asset_context()
            asset_to_invoke(context)

            with build_asset_context(resources={"foo": context_manager_resource}) as context:
                asset_to_invoke(context)
    """
    op_context = build_op_context(
        op_config=asset_config,
        resources=resources,
        resources_config=resources_config,
        partition_key=partition_key,
        partition_key_range=partition_key_range,
        instance=instance,
        run_tags=run_tags,
        event_loop=event_loop,
    )

    return DirectAssetExecutionContext(op_execution_context=op_context)

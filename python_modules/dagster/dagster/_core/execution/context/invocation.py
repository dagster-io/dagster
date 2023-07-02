from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    NoReturn,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

from typing_extensions import Self

import dagster._check as check
from dagster._annotations import public
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
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.forked_pdb import ForkedPdb

from .compute import OpExecutionContext
from .system import StepExecutionContext, TypeCheckContext


def _property_msg(prop_name: str, method_name: str) -> str:
    return (
        f"The {prop_name} {method_name} is not set on the context when a solid is directly invoked."
    )


class OpInvocationContext(OpExecutionContext):
    """The context passed to the compute function for direct asset/op invocation.

    This context is bound to a specific op definition, for which the resources and config have
    been validated.
    """

    _op_def: Optional[OpDefinition]
    _op_config: Any
    _resources: "Resources"
    _resource_defs: Mapping[str, ResourceDefinition]
    _resources_config: Mapping[str, Any]
    _resources_contain_cm: bool
    _instance: DagsterInstance
    _log: DagsterLogManager
    _pdb: Optional[ForkedPdb]
    _tags: Mapping[str, str]
    _hook_defs: Optional[AbstractSet[HookDefinition]]
    _alias: Optional[str]
    _user_events: List[UserEvent]
    _seen_outputs: Dict[str, Union[str, Set[str]]]
    _output_metadata: Dict[str, Any]
    _mapping_key: Optional[str]
    _partition_key: Optional[str]
    _partition_key_range: Optional[PartitionKeyRange]
    _assets_def: Optional[AssetsDefinition]

    def __init__(
        self,
        op_config: Any,
        resources_dict: Mapping[str, Any],
        resources_config: Mapping[str, Any],
        instance: Optional[DagsterInstance],
        partition_key: Optional[str],
        partition_key_range: Optional[PartitionKeyRange],
        mapping_key: Optional[str],
        assets_def: Optional[AssetsDefinition],
    ):
        from dagster._core.execution.api import ephemeral_instance_if_missing
        from dagster._core.execution.context_creation_job import initialize_console_manager

        self._op_config = op_config
        self._mapping_key = mapping_key

        self._instance_provided = (
            check.opt_inst_param(instance, "instance", DagsterInstance) is not None
        )
        # Construct ephemeral instance if missing
        self._instance_cm = ephemeral_instance_if_missing(instance)
        # Pylint can't infer that the ephemeral_instance context manager has an __enter__ method,
        # so ignore lint error
        self._instance = self._instance_cm.__enter__()

        self._resources_config = resources_config
        # Open resource context manager
        self._resources_contain_cm = False
        self._resource_defs = wrap_resources_for_execution(resources_dict)
        self._resources_cm = build_resources(
            resources=self._resource_defs,
            instance=instance,
            resource_config=resources_config,
        )
        self._resources = self._resources_cm.__enter__()
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
        self._user_events: List[UserEvent] = []
        self._output_metadata: Dict[str, Any] = {}

        self._assets_def = check.opt_inst_param(assets_def, "assets_def", AssetsDefinition)
        self._seen_outputs = {}
        self._output_metadata = {}

        # These attributes will be set when the property is bound
        self._op_def = None
        self._alias = None
        self._hook_defs = None
        self._tags = {}

    def __enter__(self):
        self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        self._resources_cm.__exit__(*exc)
        self._instance_cm.__exit__(*exc)

    def __del__(self):
        if self._resources_contain_cm and not self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)
        if not self._cm_scope_entered:
            self._instance_cm.__exit__(None, None, None)

    @public
    @property
    def op_config(self) -> Any:
        """The configuration provided at context construction."""
        return self._op_config

    @property
    def resource_keys(self) -> AbstractSet[str]:
        return self._resource_defs.keys()

    @property
    def resources(self) -> Resources:
        if self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_solid_context(...) as context:`"
            )
        return self._resources

    @property
    def dagster_run(self) -> DagsterRun:
        raise DagsterInvalidPropertyError(_property_msg("pipeline_run", "property"))

    @public
    @property
    def instance(self) -> DagsterInstance:
        """DagsterInstance: The instance provided at context construction."""
        return self._instance

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        raise DagsterInvalidPropertyError(_property_msg("step_launcher", "property"))

    @public
    @property
    def run_id(self) -> str:
        """str: Dummy value to indicate that we are in a direct invocation context. There is no run associated with invocation.
        """
        return "EPHEMERAL"

    @public
    @property
    def run_config(self) -> Mapping[str, object]:
        """Mapping[str, object]: A structure containing the op and resource
        config provided at context construction. Does not include all the
        fields that are normally present in run config, since op invocation
        does not take place in the context of a run.
        """
        run_config: Dict[str, object] = {}
        if self._op_config:
            run_config["ops"] = {self.op_def.name: {"config": self._op_config}}
        run_config["resources"] = self._resources_config
        return run_config

    @property
    def job_def(self) -> JobDefinition:
        raise DagsterInvalidPropertyError(_property_msg("job_def", "property"))

    @public
    @property
    def job_name(self) -> NoReturn:
        """NoReturn: There is no job associated with an op invocation. Accessing this property throws an error.
        """
        raise DagsterInvalidPropertyError(_property_msg("job_name", "property"))

    @public
    @property
    def retry_number(self) -> NoReturn:
        """NoReturn: Retries are not supported for op invocation."""
        raise DagsterInvalidPropertyError(_property_msg("retry_number", "property"))
        return self._step_execution_context.previous_attempt_count

    @public
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

    @public
    @property
    def op_def(self) -> OpDefinition:
        """OpDefinition: The definition of the op supplied to the context at binding time. Accessing this property before binding will throw an error.
        """
        self.validate_bound_property_access("op_def")
        assert self._op_def is not None
        return self._op_def

    @public
    @property
    def assets_def(self) -> AssetsDefinition:
        """AssetsDefinition: The definition of the asset supplied to the context at binding time. Accessing this property before binding, or if a plain op was bound instead of an asset, will throw an error.
        """
        self.validate_bound_property_access("op_def")
        if self._assets_def is None:
            raise DagsterInvalidPropertyError(
                f"Op {self.op_def.name} does not have an assets definition."
            )
        return self._assets_def

    @property
    def alias(self) -> str:
        self.validate_bound_property_access("alias")
        return self._alias or self.op_def.name

    @property
    def hook_defs(self) -> Optional[AbstractSet[HookDefinition]]:
        self.validate_bound_property_access("hook_defs")
        return self._hook_defs

    @public
    def has_tag(self, key: str) -> bool:
        """Check if a tag is set. Calling this method before binding will throw an error.

        Args:
            key (str): The tag to check.

        Returns:
            bool: Whether the tag is set.
        """
        self.validate_bound_property_access("tags")
        return key in self._tags

    @public
    def get_tag(self, key: str) -> Optional[str]:
        """Get a tag. Calling this method before binding will throw an error.

        Args:
            key (tag): The tag to get.

        Returns:
            Optional[str]: The value of the tag, if present.
        """
        self.validate_bound_property_access("tags")
        return self._tags.get(key)

    @public
    @property
    def has_partition_key(self) -> bool:
        """Returns `True` if a partition key was provided at context construction."""
        return self._partition_key is not None

    @public
    @property
    def partition_key(self) -> str:
        """The partition key provided for at context construction. Raises an
        error if no partition key was provided.
        """
        if self._partition_key:
            return self._partition_key
        check.failed("Tried to access partition_key but no partition key was set.")

    @public
    @property
    def partition_key_range(self) -> PartitionKeyRange:
        """The range of partition keys provided at context construction.

        If only a single partition key was provided, return a `PartitionKeyRange` with the same start and
        end. Raises an error if no key or range was provided.
        """
        if self._partition_key_range:
            return self._partition_key_range
        elif self._partition_key:
            return PartitionKeyRange(self._partition_key, self._partition_key)
        else:
            check.failed("Tried to access partition_key range for a non-partitioned run")

    @public
    def asset_partition_key_for_output(self, output_name: str = "result") -> str:
        """Returns the asset partition key for the given output."""
        return self.partition_key

    @public
    def asset_partitions_time_window_for_output(self, output_name: str = "result") -> TimeWindow:
        """The time window for the partitions of the output asset.

        Raises an error if either of the following are true:
        - The output asset has no partitioning.
        - The output asset is not partitioned with a TimeWindowPartitionsDefinition or a
        MultiPartitionsDefinition with one time-partitioned dimension.
        """
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

    def get_step_execution_context(self) -> StepExecutionContext:
        raise DagsterInvalidPropertyError(_property_msg("get_step_execution_context", "methods"))

    def for_type(self, dagster_type: DagsterType) -> TypeCheckContext:
        resources = cast(NamedTuple, self.resources)
        return TypeCheckContext(
            self.run_id,
            self.log,
            ScopedResourcesBuilder(resources._asdict()),
            dagster_type,
        )

    def get_mapping_key(self) -> Optional[str]:
        return self._mapping_key

    def describe_op(self) -> str:
        return f'op "{self.op_def.name}"'

    @public
    @property
    def is_bound(self) -> bool:
        """bool: Returns `True` if the context has been bound to an op."""
        return self._op_def is not None

    def validate_bound_property_access(self, property_name: str) -> None:
        if not self.is_bound:
            raise DagsterInvalidPropertyError(
                f"Attempted to access {property_name} property of OpInvocationContext before "
                "context was bound."
            )

    def bind(
        self,
        op_def_or_invocation: Union[OpDefinition, PendingNodeInvocation[OpDefinition]],
    ) -> Self:
        from dagster._core.definitions.resource_invocation import resolve_bound_config

        if isinstance(op_def_or_invocation, PendingNodeInvocation):
            self._op_def = op_def_or_invocation.node_def
            self._alias = op_def_or_invocation.given_alias
            self._hook_defs = op_def_or_invocation.hook_defs
        else:
            self._op_def = op_def_or_invocation
            self._alias = None
            self._hook_defs = None
        self._tags = op_def_or_invocation.tags or {}

        _validate_resource_requirements(self._resource_defs, self._op_def)
        self._op_config = resolve_bound_config(self.op_config, self._op_def)
        return self

    @public
    def log_event(self, event: UserEvent) -> None:
        """Log an AssetMaterialization, AssetObservation, or ExpectationResult.

        Events logged with this method are available on the context after invocation.
        """
        check.inst_param(
            event,
            "event",
            (AssetMaterialization, AssetObservation, ExpectationResult),
        )
        self._user_events.append(event)

    def observe_output(self, output_name: str, mapping_key: Optional[str] = None) -> None:
        if mapping_key:
            if output_name not in self._seen_outputs:
                self._seen_outputs[output_name] = set()
            cast(Set[str], self._seen_outputs[output_name]).add(mapping_key)
        else:
            self._seen_outputs[output_name] = "seen"

    def has_seen_output(self, output_name: str, mapping_key: Optional[str] = None) -> bool:
        if mapping_key:
            return (
                output_name in self._seen_outputs and mapping_key in self._seen_outputs[output_name]
            )
        return output_name in self._seen_outputs

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
        return self._user_events

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
        metadata = self._output_metadata.get(output_name)
        if mapping_key and metadata:
            return metadata.get(mapping_key)
        return metadata

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
        if output_name in self._output_metadata:
            if not mapping_key or mapping_key in self._output_metadata[output_name]:
                raise DagsterInvariantViolationError(
                    f"In {self.op_def.node_type_str} '{self.op_def.name}', attempted to log"
                    f" metadata for output '{output_name}' more than once."
                )
        if mapping_key:
            if output_name not in self._output_metadata:
                self._output_metadata[output_name] = {}
            self._output_metadata[output_name][mapping_key] = metadata

        else:
            self._output_metadata[output_name] = metadata

    def _copy(self, **kwargs) -> Self:
        if self.is_bound:
            raise DagsterInvariantViolationError("Can not copy OpInvocationContext after binding.")
        constructor_kwargs = {
            **dict(
                op_config=self._op_config,
                resources_dict=self._resource_defs,
                resources_config=self._resources_config,
                instance=self._instance,
                partition_key=self._partition_key,
                partition_key_range=self._partition_key_range,
                mapping_key=self._mapping_key,
                assets_def=self._assets_def,
            ),
            **kwargs,
        }
        return OpInvocationContext(**constructor_kwargs)

    def replace_resources(self, resources_dict: Mapping[str, Any]) -> "OpInvocationContext":
        """Replace the resources of this context.

        Args:
            resources (Mapping[str, Any]): The resources to add to the context.
        """
        return self._copy(resources_dict=resources_dict)

    def replace_config(self, op_config: Mapping[str, Any]) -> "OpInvocationContext":
        return self._copy(op_config=op_config)


def _validate_resource_requirements(
    resource_defs: Mapping[str, ResourceDefinition], op_def: OpDefinition
) -> None:
    """Validate correctness of resources against required resource keys."""
    if cast(DecoratedOpFunction, op_def.compute_fn).has_context_arg():
        for requirement in op_def.get_resource_requirements():
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
    _assets_def: Optional[AssetsDefinition] = None,
) -> OpInvocationContext:
    """Builds op invocation context from provided parameters.

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
        partition_key (Optional[str]): String value representing partition key to execute with.
        partition_key_range (Optional[PartitionKeyRange]): Partition key range to execute with.
        mapping_key (Optional[str]): A key representing the mapping key from an upstream dynamic
            output. Can be accessed using ``context.get_mapping_key()``.
        _assets_def (Optional[AssetsDefinition]): Internal argument that populates the op's assets
            definition, not meant to be populated by users.

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
    return OpInvocationContext(
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
        assets_def=check.opt_inst_param(_assets_def, "_assets_def", AssetsDefinition),
    )


def build_asset_context(
    resources: Optional[Mapping[str, Any]] = None,
    resources_config: Optional[Mapping[str, Any]] = None,
    asset_config: Optional[Mapping[str, Any]] = None,
    instance: Optional[DagsterInstance] = None,
    partition_key: Optional[str] = None,
    partition_key_range: Optional[PartitionKeyRange] = None,
):
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

    Examples:
        .. code-block:: python

            context = build_asset_context()
            asset_to_invoke(context)

            with build_asset_context(resources={"foo": context_manager_resource}) as context:
                asset_to_invoke(context)
    """
    return build_op_context(
        op_config=asset_config,
        resources=resources,
        resources_config=resources_config,
        partition_key=partition_key,
        partition_key_range=partition_key_range,
        instance=instance,
    )

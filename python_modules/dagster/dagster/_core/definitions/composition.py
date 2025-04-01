import warnings
from collections import defaultdict, namedtuple
from collections.abc import Mapping, Sequence
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Generic,
    NamedTuple,
    NoReturn,
    Optional,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.dependency import (
    DependencyDefinition,
    DependencyMapping,
    DynamicCollectDependencyDefinition,
    IDependencyDefinition,
    MultiDependencyDefinition,
    NodeInvocation,
)
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.inference import infer_output_props
from dagster._core.definitions.input import InputDefinition, InputMapping
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.output import OutputDefinition, OutputMapping
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.utils import check_valid_name
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster._utils import is_named_tuple_instance
from dagster._utils.tags import normalize_tags
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.executor_definition import ExecutorDefinition
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.partition import PartitionedConfig, PartitionsDefinition
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster._core.instance import DagsterInstance


_composition_stack: list["InProgressCompositionContext"] = []


class MappedInputPlaceholder:
    """Marker for holding places in fan-in lists where input mappings will feed."""


class InvokedNodeOutputHandle:
    """The return value for an output when invoking a node in a composition function."""

    node_name: str
    output_name: str
    node_type: str

    def __init__(self, node_name: str, output_name: str, node_type: str):
        self.node_name = check.str_param(node_name, "node_name")
        self.output_name = check.str_param(output_name, "output_name")
        self.node_type = check.str_param(node_type, "node_type")

    def __iter__(self) -> NoReturn:
        raise DagsterInvariantViolationError(
            f'Attempted to iterate over an {self.__class__.__name__}. This object represents the output "{self.output_name}" '
            f'from the op/graph "{self.node_name}". Consider defining multiple Outs if you seek to pass '
            "different parts of this output to different op/graph."
        )

    def __getitem__(self, idx: object) -> NoReturn:
        raise DagsterInvariantViolationError(
            f'Attempted to index in to an {self.__class__.__name__}. This object represents the output "{self.output_name}" '
            f"from the {self.describe_node()}. Consider defining multiple Outs if you seek to pass "
            f"different parts of this output to different {self.node_type}s."
        )

    def describe_node(self) -> str:
        return f"{self.node_type} '{self.node_name}'"

    def alias(self, _) -> NoReturn:
        raise DagsterInvariantViolationError(
            f"In {current_context().source} {current_context().name}, attempted to call alias method for {self.__class__.__name__}. This object "
            f'represents the output "{self.output_name}" from the already invoked {self.describe_node()}. Consider '
            "checking the location of parentheses."
        )

    def with_hooks(self, _) -> NoReturn:
        raise DagsterInvariantViolationError(
            f"In {current_context().source} {current_context().name}, attempted to call hook method for {self.__class__.__name__}. This object "
            f'represents the output "{self.output_name}" from the already invoked {self.describe_node()}. Consider '
            "checking the location of parentheses."
        )


class InputMappingNode(NamedTuple):
    input_def: InputDefinition


class DynamicFanIn(NamedTuple):
    """Type to signify collecting over a dynamic output, output by collect() on a
    InvokedNodeDynamicOutputWrapper.
    """

    node_name: str
    output_name: str


InputSource: TypeAlias = Union[
    InvokedNodeOutputHandle,
    InputMappingNode,
    DynamicFanIn,
    "AssetsDefinition",
    list[Union[InvokedNodeOutputHandle, InputMappingNode]],
]


def _not_invoked_warning(
    node: "PendingNodeInvocation",
    context_source: str,
    context_name: str,
) -> None:
    warning_message = (
        "While in {context} context '{name}', received an uninvoked {node_type} '{node_name}'.\n"
    )
    if node.given_alias:
        warning_message += "'{node_name}' was aliased as '{given_alias}'.\n"
    if node.tags:
        warning_message += "Provided tags: {tags}.\n"
    if node.hook_defs:
        warning_message += "Provided hook definitions: {hooks}.\n"

    warning_message = warning_message.format(
        context=context_source,
        name=context_name,
        node_name=node.node_def.name,
        given_alias=node.given_alias,
        tags=node.tags,
        hooks=[hook.name for hook in node.hook_defs],
        node_type=node.node_def.node_type_str,
    )

    warnings.warn(warning_message.strip())


def enter_composition(name: str, source: str) -> None:
    _composition_stack.append(InProgressCompositionContext(name, source))


def exit_composition(
    output: Optional[Mapping[str, OutputMapping]] = None,
) -> "CompleteCompositionContext":
    return _composition_stack.pop().complete(output)


def current_context() -> "InProgressCompositionContext":
    return _composition_stack[-1]


def is_in_composition() -> bool:
    return bool(_composition_stack)


def assert_in_composition(name: str, node_def: NodeDefinition) -> None:
    if len(_composition_stack) < 1:
        node_label = node_def.node_type_str
        correction = (
            f"Invoking {node_label}s is only valid in a function decorated with @job or @graph."
        )
        raise DagsterInvariantViolationError(
            f"Attempted to call {node_label} '{name}' outside of a composition function."
            f" {correction}"
        )


class InProgressCompositionContext:
    """This context captures invocations of nodes within a
    composition function such as @job or @graph.
    """

    name: str
    source: str
    _invocations: dict[str, "InvokedNode"]
    _collisions: dict[str, int]
    _pending_invocations: dict[str, "PendingNodeInvocation"]

    def __init__(self, name: str, source: str):
        self.name = check.str_param(name, "name")
        self.source = check.str_param(source, "source")
        self._invocations = {}
        self._collisions = {}
        self._pending_invocations = {}

    def observe_invocation(
        self,
        given_alias: Optional[str],
        node_def: NodeDefinition,
        input_bindings: Mapping[str, InputSource],
        tags: Optional[Mapping[str, str]],
        hook_defs: Optional[AbstractSet[HookDefinition]],
        retry_policy: Optional[RetryPolicy],
    ) -> str:
        if given_alias is None:
            node_name = node_def.name
            self._pending_invocations.pop(node_name, None)
            if self._collisions.get(node_name):
                self._collisions[node_name] += 1
                node_name = f"{node_name}_{self._collisions[node_name]}"
            else:
                self._collisions[node_name] = 1
        else:
            node_name = given_alias
            self._pending_invocations.pop(node_name, None)

        if self._invocations.get(node_name):
            raise DagsterInvalidDefinitionError(
                f"{self.source} {self.name} invoked the same node ({node_name}) twice without aliasing."
            )

        self._invocations[node_name] = InvokedNode(
            node_name, node_def, input_bindings, tags, hook_defs, retry_policy
        )
        return node_name

    def add_pending_invocation(self, node: "PendingNodeInvocation") -> None:
        node_name = node.given_alias if node.given_alias else node.node_def.name
        self._pending_invocations[node_name] = node

    def complete(
        self, output: Optional[Mapping[str, OutputMapping]]
    ) -> "CompleteCompositionContext":
        return CompleteCompositionContext.create(
            self.name,
            self.source,
            self._invocations,
            check.opt_mapping_param(output, "output"),
            self._pending_invocations,
        )


class CompleteCompositionContext(NamedTuple):
    """The processed information from capturing node invocations during a composition function."""

    name: str
    node_defs: Sequence[NodeDefinition]
    dependencies: DependencyMapping[NodeInvocation]
    input_mappings: Sequence[InputMapping]
    output_mapping_dict: Mapping[str, OutputMapping]
    node_input_assets: Mapping[str, Mapping[str, "AssetsDefinition"]]

    @staticmethod
    def create(
        name: str,
        source: str,
        invocations: Mapping[str, "InvokedNode"],
        output_mapping_dict: Mapping[str, OutputMapping],
        pending_invocations: Mapping[str, "PendingNodeInvocation"],
    ) -> "CompleteCompositionContext":
        from dagster._core.definitions.assets import AssetsDefinition

        dep_dict: dict[NodeInvocation, dict[str, IDependencyDefinition]] = {}
        node_def_dict: dict[str, NodeDefinition] = {}
        input_mappings = []
        node_input_assets: dict[str, dict[str, AssetsDefinition]] = defaultdict(dict)

        for node in pending_invocations.values():
            _not_invoked_warning(node, source, name)

        for invocation in invocations.values():
            def_name = invocation.node_def.name
            if def_name in node_def_dict and node_def_dict[def_name] is not invocation.node_def:
                raise DagsterInvalidDefinitionError(
                    f'Detected conflicting node definitions with the same name "{def_name}"'
                )
            node_def_dict[def_name] = invocation.node_def

            deps: dict[str, IDependencyDefinition] = {}
            for input_name, node in invocation.input_bindings.items():
                if isinstance(node, InvokedNodeOutputHandle):
                    deps[input_name] = DependencyDefinition(node.node_name, node.output_name)
                elif isinstance(node, InputMappingNode):
                    input_mappings.append(
                        node.input_def.mapping_to(invocation.node_name, input_name)
                    )
                elif isinstance(node, AssetsDefinition):
                    node_input_assets[invocation.node_name][input_name] = node
                elif isinstance(node, list):
                    entries: list[Union[DependencyDefinition, type[MappedInputPlaceholder]]] = []
                    for idx, fanned_in_node in enumerate(node):
                        if isinstance(fanned_in_node, InvokedNodeOutputHandle):
                            entries.append(
                                DependencyDefinition(
                                    fanned_in_node.node_name, fanned_in_node.output_name
                                )
                            )
                        elif isinstance(fanned_in_node, InputMappingNode):
                            entries.append(MappedInputPlaceholder)
                            input_mappings.append(
                                fanned_in_node.input_def.mapping_to(
                                    invocation.node_name, input_name, idx
                                )
                            )
                        else:
                            check.invariant("Unexpected fanned in node received")

                    deps[input_name] = MultiDependencyDefinition(entries)
                elif isinstance(node, DynamicFanIn):
                    deps[input_name] = DynamicCollectDependencyDefinition(
                        node.node_name, node.output_name
                    )
                else:
                    check.failed(f"Unexpected input binding - got {node}")

            dep_dict[
                NodeInvocation(
                    invocation.node_def.name,
                    invocation.node_name,
                    tags=invocation.tags,
                    hook_defs=invocation.hook_defs,
                    retry_policy=invocation.retry_policy,
                )
            ] = deps

        return CompleteCompositionContext(
            name,
            list(node_def_dict.values()),
            dep_dict,
            input_mappings,
            output_mapping_dict,
            node_input_assets=node_input_assets,
        )


T_NodeDefinition = TypeVar("T_NodeDefinition", bound=NodeDefinition)


class PendingNodeInvocation(Generic[T_NodeDefinition]):
    """An intermediate object in composition that allows binding additional information before invoking.

    Users should not invoke this object directly.

    Examples:
        ..code-block:: python

            from dagster import graph, op

            @op
            def some_op():
                ...

            @graph
            def the_graph():
                # renamed_op is a PendingNodeInvocation object with an added
                # name attribute
                renamed_op = some_op.alias("new_name")
                renamed_op()

    """

    node_def: T_NodeDefinition
    given_alias: Optional[str]
    tags: Optional[Mapping[str, str]]
    hook_defs: AbstractSet[HookDefinition]
    retry_policy: Optional[RetryPolicy]

    def __init__(
        self,
        node_def: T_NodeDefinition,
        given_alias: Optional[str],
        tags: Optional[Mapping[str, str]],
        hook_defs: Optional[AbstractSet[HookDefinition]],
        retry_policy: Optional[RetryPolicy],
    ):
        self.node_def = check.inst_param(node_def, "node_def", NodeDefinition)
        self.given_alias = check.opt_str_param(given_alias, "given_alias")
        self.tags = check.opt_mapping_param(tags, "tags", key_type=str, value_type=str)
        self.hook_defs = check.opt_set_param(hook_defs, "hook_defs", HookDefinition)
        self.retry_policy = check.opt_inst_param(retry_policy, "retry_policy", RetryPolicy)

        if self.given_alias is not None:
            check_valid_name(self.given_alias)

        if is_in_composition():
            current_context().add_pending_invocation(self)

    def __call__(self, *args, **kwargs) -> Any:
        from dagster._core.definitions.op_invocation import direct_invocation_result

        node_name = self.given_alias if self.given_alias else self.node_def.name

        # If PendingNodeInvocation is not within composition context, and underlying NodeDefinition
        # is an OpDefinition, then permit it to be invoked and executed like an OpDefinition.
        if not is_in_composition() and isinstance(self.node_def, OpDefinition):
            return direct_invocation_result(
                cast(PendingNodeInvocation[OpDefinition], self), *args, **kwargs
            )

        assert_in_composition(node_name, self.node_def)
        input_bindings: dict[str, InputSource] = {}

        # handle *args
        for idx, output_node in enumerate(args):
            if idx >= len(self.node_def.input_defs):
                raise DagsterInvalidDefinitionError(
                    f"In {current_context().source} {current_context().name}, received too many inputs for "
                    f"invocation {node_name}. Only {len(self.node_def.input_defs)} defined, received {len(args)}"
                )

            input_name = self.node_def.resolve_input_name_at_position(idx)
            if input_name is None:
                raise DagsterInvalidDefinitionError(
                    f"In {current_context().source} {current_context().name}, could not resolve input based on position at "
                    f"index {idx} for invocation {node_name}. Use keyword args instead, "
                    f"available inputs are: {list(map(lambda inp: inp.name, self.node_def.input_defs))}"
                )

            self._process_argument_node(
                node_name,
                output_node,
                input_name,
                input_bindings,
                f"(at position {idx})",
            )

        # then **kwargs
        for input_name, output_node in kwargs.items():
            self._process_argument_node(
                node_name,
                output_node,
                input_name,
                input_bindings,
                "(passed by keyword)",
            )

        # the node name is potentially reassigned for aliasing
        resolved_node_name = current_context().observe_invocation(
            self.given_alias,
            self.node_def,
            input_bindings,
            self.tags,
            self.hook_defs,
            self.retry_policy,
        )

        if len(self.node_def.output_defs) == 0:
            return None

        if len(self.node_def.output_defs) == 1:
            output_def = self.node_def.output_defs[0]
            output_name = output_def.name
            if output_def.is_dynamic:
                return InvokedNodeDynamicOutputWrapper(
                    resolved_node_name, output_name, self.node_def.node_type_str
                )
            else:
                return InvokedNodeOutputHandle(
                    resolved_node_name, output_name, self.node_def.node_type_str
                )

        outputs = [output_def for output_def in self.node_def.output_defs]
        invoked_output_handles: dict[
            str, Union[InvokedNodeDynamicOutputWrapper, InvokedNodeOutputHandle]
        ] = {}
        for output_def in outputs:
            if output_def.is_dynamic:
                invoked_output_handles[output_def.name] = InvokedNodeDynamicOutputWrapper(
                    resolved_node_name, output_def.name, self.node_def.node_type_str
                )
            else:
                invoked_output_handles[output_def.name] = InvokedNodeOutputHandle(
                    resolved_node_name, output_def.name, self.node_def.node_type_str
                )

        return namedtuple(
            f"_{self.node_def.name}_outputs",
            " ".join([output_def.name for output_def in outputs]),
        )(**invoked_output_handles)

    def describe_node(self) -> str:
        node_name = self.given_alias if self.given_alias else self.node_def.name
        return f"{self.node_def.node_type_str} '{node_name}'"

    def _process_argument_node(
        self, node_name: str, output_node, input_name: str, input_bindings, arg_desc: str
    ) -> None:
        from dagster._core.definitions.asset_spec import AssetSpec
        from dagster._core.definitions.assets import AssetsDefinition
        from dagster._core.definitions.external_asset import create_external_asset_from_source_asset
        from dagster._core.definitions.source_asset import SourceAsset

        # already set - conflict between kwargs and args
        if input_bindings.get(input_name):
            raise DagsterInvalidInvocationError(
                f"{self.node_def.node_type_str} {node_name} got multiple values for"
                f" argument '{input_name}'"
            )

        if isinstance(output_node, SourceAsset):
            input_bindings[input_name] = create_external_asset_from_source_asset(output_node)
        elif isinstance(output_node, AssetSpec):
            with disable_dagster_warnings():
                input_bindings[input_name] = AssetsDefinition(specs=[output_node])
        elif isinstance(
            output_node, (AssetsDefinition, InvokedNodeOutputHandle, InputMappingNode, DynamicFanIn)
        ):
            input_bindings[input_name] = output_node

        elif isinstance(output_node, list):
            input_bindings[input_name] = []
            for idx, fanned_in_node in enumerate(output_node):
                if isinstance(fanned_in_node, (InvokedNodeOutputHandle, InputMappingNode)):
                    input_bindings[input_name].append(fanned_in_node)
                else:
                    raise DagsterInvalidDefinitionError(
                        f"In {current_context().source} {current_context().name}, received a list containing an invalid type "
                        f'at index {idx} for input "{input_name}" {arg_desc} in '
                        f"{self.node_def.node_type_str} invocation {node_name}. Lists can only contain the "
                        "output from previous op invocations or input mappings, "
                        f"received {type(output_node)}"
                    )

        elif is_named_tuple_instance(output_node) and all(
            map(lambda item: isinstance(item, InvokedNodeOutputHandle), output_node)
        ):
            raise DagsterInvalidDefinitionError(
                f"In {current_context().source} {current_context().name}, received a tuple of multiple outputs for "
                f'input "{input_name}" {arg_desc} in {self.node_def.node_type_str} invocation {node_name}. '
                f"Must pass individual output, available from tuple: {output_node._fields}"
            )
        elif isinstance(output_node, InvokedNodeDynamicOutputWrapper):
            raise DagsterInvalidDefinitionError(
                f"In {current_context().source} {current_context().name}, received the dynamic"
                f" output {output_node.output_name} from {output_node.describe_node()} directly."
                " Dynamic output must be unpacked by invoking map or collect."
            )

        elif isinstance(output_node, (NodeDefinition, PendingNodeInvocation)):
            raise DagsterInvalidDefinitionError(
                f"In {current_context().source} {current_context().name}, received an un-invoked {output_node.describe_node()} "
                " for input "
                f'"{input_name}" {arg_desc} in {output_node.describe_node()} invocation "{node_name}". '
                "Did you forget parentheses?"
            )
        else:
            raise DagsterInvalidDefinitionError(
                f"In {current_context().source} {current_context().name}, received invalid type {type(output_node)} for input "
                f'"{input_name}" {arg_desc} in {self.node_def.node_type_str} invocation "{node_name}". '
                "Must pass the output from previous node invocations or inputs to the "
                "composition function as inputs when invoking nodes during composition."
            )

    @public
    def alias(self, name: str) -> "PendingNodeInvocation[T_NodeDefinition]":
        return PendingNodeInvocation(
            node_def=self.node_def,
            given_alias=name,
            tags=self.tags,
            hook_defs=self.hook_defs,
            retry_policy=self.retry_policy,
        )

    @public
    def tag(self, tags: Optional[Mapping[str, str]]) -> "PendingNodeInvocation[T_NodeDefinition]":
        tags = normalize_tags(tags)
        return PendingNodeInvocation(
            node_def=self.node_def,
            given_alias=self.given_alias,
            tags={**(self.tags or {}), **tags},
            hook_defs=self.hook_defs,
            retry_policy=self.retry_policy,
        )

    @public
    def with_hooks(
        self, hook_defs: AbstractSet[HookDefinition]
    ) -> "PendingNodeInvocation[T_NodeDefinition]":
        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        return PendingNodeInvocation(
            node_def=self.node_def,
            given_alias=self.given_alias,
            tags=self.tags,
            hook_defs=set(hook_defs).union(self.hook_defs),
            retry_policy=self.retry_policy,
        )

    @public
    def with_retry_policy(
        self, retry_policy: RetryPolicy
    ) -> "PendingNodeInvocation[T_NodeDefinition]":
        return PendingNodeInvocation(
            node_def=self.node_def,
            given_alias=self.given_alias,
            tags=self.tags,
            hook_defs=self.hook_defs,
            retry_policy=retry_policy,
        )

    @public
    def to_job(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        config: Optional[Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig"]] = None,
        tags: Optional[Mapping[str, Any]] = None,
        logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        executor_def: Optional["ExecutorDefinition"] = None,
        hooks: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
        partitions_def: Optional["PartitionsDefinition"] = None,
        input_values: Optional[Mapping[str, object]] = None,
    ) -> "JobDefinition":
        if not isinstance(self.node_def, GraphDefinition):
            raise DagsterInvalidInvocationError(
                "Attemped to call `to_job` on a non-graph.  Only graphs "
                "constructed using the `@graph` decorator support this method."
            )

        tags = normalize_tags(tags)
        hooks = check.opt_set_param(hooks, "hooks", HookDefinition)
        input_values = check.opt_mapping_param(input_values, "input_values")
        op_retry_policy = check.opt_inst_param(op_retry_policy, "op_retry_policy", RetryPolicy)
        job_hooks: set[HookDefinition] = set()
        job_hooks.update(check.opt_set_param(hooks, "hooks", HookDefinition))
        job_hooks.update(self.hook_defs)
        return self.node_def.to_job(
            name=name or self.given_alias,
            description=description,
            resource_defs=resource_defs,
            config=config,
            tags=normalize_tags({**(self.tags or {}), **(tags or {})}),
            logger_defs=logger_defs,
            executor_def=executor_def,
            hooks=job_hooks,
            op_retry_policy=op_retry_policy,
            partitions_def=partitions_def,
            input_values=input_values,
        )

    @public
    def execute_in_process(
        self,
        run_config: Optional[Any] = None,
        instance: Optional["DagsterInstance"] = None,
        resources: Optional[Mapping[str, Any]] = None,
        raise_on_error: bool = True,
        run_id: Optional[str] = None,
        input_values: Optional[Mapping[str, object]] = None,
    ) -> "ExecuteInProcessResult":
        if not isinstance(self.node_def, GraphDefinition):
            raise DagsterInvalidInvocationError(
                "Attemped to call `execute_in_process` on a non-graph.  Only graphs "
                "constructed using the `@graph` decorator support this method."
            )

        from dagster._core.definitions.executor_definition import execute_in_process_executor
        from dagster._core.definitions.job_definition import JobDefinition
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        input_values = check.opt_mapping_param(input_values, "input_values")

        ephemeral_job = JobDefinition(
            name=self.given_alias,
            graph_def=self.node_def,
            executor_def=execute_in_process_executor,
            resource_defs=wrap_resources_for_execution(resources),
            tags=self.tags,
            hook_defs=self.hook_defs,
            op_retry_policy=self.retry_policy,
            input_values=input_values,
        )

        return ephemeral_job.execute_in_process(
            run_config=run_config,
            instance=instance,
            raise_on_error=raise_on_error,
            run_id=run_id,
        )


class InvokedNode(NamedTuple):
    """The metadata about a node invocation saved by the current composition context."""

    node_name: str
    node_def: NodeDefinition
    input_bindings: Mapping[str, InputSource]
    tags: Optional[Mapping[str, str]]
    hook_defs: Optional[AbstractSet[HookDefinition]]
    retry_policy: Optional[RetryPolicy]


class InvokedNodeDynamicOutputWrapper:
    """The return value for a dynamic output when invoking a node in a composition function.
    Must be unwrapped by invoking map or collect.
    """

    def __init__(self, node_name: str, output_name: str, node_type: str):
        self.node_name = check.str_param(node_name, "node_name")
        self.output_name = check.str_param(output_name, "output_name")
        self.node_type = check.str_param(node_type, "node_type")

    def describe_node(self) -> str:
        return f"{self.node_type} '{self.node_name}'"

    def map(
        self, fn: Callable
    ) -> Union[
        "InvokedNodeDynamicOutputWrapper", tuple["InvokedNodeDynamicOutputWrapper", ...], None
    ]:
        check.is_callable(fn)
        result = fn(InvokedNodeOutputHandle(self.node_name, self.output_name, self.node_type))

        if isinstance(result, InvokedNodeOutputHandle):
            return InvokedNodeDynamicOutputWrapper(
                result.node_name, result.output_name, result.node_type
            )
        elif isinstance(result, tuple) and all(
            map(lambda item: isinstance(item, InvokedNodeOutputHandle), result)
        ):
            return tuple(
                map(
                    lambda item: InvokedNodeDynamicOutputWrapper(
                        item.node_name, item.output_name, item.node_type
                    ),
                    result,
                )
            )
        elif result is None:
            return None
        elif isinstance(result, InvokedNodeDynamicOutputWrapper):
            return result
        else:
            check.failed(
                "Could not handle output from map function invoked on "
                f"{self.node_name}:{self.output_name}, received {result}"
            )

    def collect(self) -> DynamicFanIn:
        return DynamicFanIn(self.node_name, self.output_name)

    def unwrap_for_composite_mapping(self) -> InvokedNodeOutputHandle:
        return InvokedNodeOutputHandle(self.node_name, self.output_name, self.node_type)

    def __iter__(self) -> NoReturn:
        raise DagsterInvariantViolationError(
            f'Attempted to iterate over an {self.__class__.__name__}. This object represents the dynamic output "{self.output_name}" '
            f'from the {self.describe_node()}. Use the "map" method on this object to create '
            "downstream dependencies that will be cloned for each DynamicOut "
            "that is resolved at runtime."
        )

    def __getitem__(self, idx) -> NoReturn:
        raise DagsterInvariantViolationError(
            f'Attempted to index in to an {self.__class__.__name__}. This object represents the dynamic out "{self.output_name}" '
            f'from the {self.describe_node()}. Use the "map" method on this object to create '
            "downstream dependencies that will be cloned for each DynamicOut "
            "that is resolved at runtime."
        )

    def alias(self, _) -> NoReturn:
        raise DagsterInvariantViolationError(
            f"In {current_context().source} {current_context().name}, attempted to call alias method for {self.__class__.__name__}. This object represents"
            f' the dynamic out "{self.output_name}" from the already invoked {self.describe_node()}. Consider checking'
            " the location of parentheses."
        )

    def with_hooks(self, _) -> NoReturn:
        raise DagsterInvariantViolationError(
            f"In {current_context().source} {current_context().name}, attempted to call hook method for {self.__class__.__name__}. This object represents"
            f' the dynamic out "{self.output_name}" from the already invoked {self.describe_node()}. Consider checking'
            " the location of parentheses."
        )


def composite_mapping_from_output(
    output: Any,
    output_defs: Sequence[OutputDefinition],
    node_name: str,
    decorator_name: str,
) -> Optional[Mapping[str, OutputMapping]]:
    # single output
    if isinstance(output, InvokedNodeOutputHandle):
        if len(output_defs) == 1:
            defn = output_defs[0]
            return {defn.name: defn.mapping_from(output.node_name, output.output_name)}
        else:
            raise DagsterInvalidDefinitionError(
                f"Returned a single output ({output.node_name}.{output.output_name}) in "
                f"{decorator_name} '{node_name}' but {len(output_defs)} outputs are defined. "
                "Return a dict to map defined outputs."
            )

    elif isinstance(output, InvokedNodeDynamicOutputWrapper):
        if len(output_defs) == 1:
            defn = output_defs[0]
            return {
                defn.name: defn.mapping_from(
                    output.node_name, output.output_name, from_dynamic_mapping=True
                )
            }
        else:
            raise DagsterInvalidDefinitionError(
                f"Returned a single output ({output.node_name}.{output.output_name}) in "
                f"{decorator_name} '{node_name}' but {len(output_defs)} outputs are defined. "
                "Return a dict to map defined outputs."
            )

    output_mapping_dict = {}
    output_def_dict = {output_def.name: output_def for output_def in output_defs}

    # tuple returned directly
    if isinstance(output, tuple) and all(
        map(lambda item: isinstance(item, InvokedNodeOutputHandle), output)
    ):
        for i, output_name in enumerate(output_def_dict.keys()):
            handle = output[i]
            # map output defined on graph to the actual output defined on the op
            output_mapping_dict[output_name] = output_def_dict[output_name].mapping_from(
                handle.node_name, handle.output_name
            )

        return output_mapping_dict

    # mapping dict
    if isinstance(output, dict):
        for name, handle in output.items():
            if name not in output_def_dict:
                raise DagsterInvalidDefinitionError(
                    f"{decorator_name} '{node_name}' referenced key {name} which does not match any"
                    f" defined outputs. Valid options are: {list(output_def_dict.keys())}"
                )

            if isinstance(handle, InvokedNodeOutputHandle):
                output_mapping_dict[name] = output_def_dict[name].mapping_from(
                    handle.node_name, handle.output_name
                )
            elif isinstance(handle, InvokedNodeDynamicOutputWrapper):
                output_mapping_dict[name] = output_def_dict[name].mapping_from(
                    handle.node_name, handle.output_name, from_dynamic_mapping=True
                )
            else:
                raise DagsterInvalidDefinitionError(
                    f"{decorator_name} '{node_name}' returned problematic dict entry under "
                    f"key {name} of type {type(handle)}. Dict values must be outputs of "
                    "invoked nodes"
                )

        return output_mapping_dict

    # error
    if output is not None:
        raise DagsterInvalidDefinitionError(
            f"{decorator_name} '{node_name}' returned problematic value "
            f"of type {type(output)}. Expected return value from invoked node or dict mapping "
            "output name to return values from invoked nodes"
        )

    return None


def do_composition(
    decorator_name: str,
    graph_name: str,
    fn: Callable[..., Any],
    provided_input_defs: Sequence[InputDefinition],
    provided_output_defs: Optional[Sequence[OutputDefinition]],
    config_mapping: Optional[ConfigMapping],
    ignore_output_from_composition_fn: bool,
) -> tuple[
    Sequence[InputMapping],
    Sequence[OutputMapping],
    DependencyMapping[NodeInvocation],
    Sequence[NodeDefinition],
    Optional[ConfigMapping],
    Sequence[str],
    Mapping[str, Mapping[str, "AssetsDefinition"]],
]:
    """This a function used by both @job and @graph to implement their composition
    function which is our DSL for constructing a dependency graph.

    Args:
        decorator_name (str): Name of the calling decorator. e.g. "@graph" or "@job"
        graph_name (str): User-defined name of the definition being constructed
        fn (Callable): The composition function to be called.
        provided_input_defs(List[InputDefinition]): List of input definitions
            explicitly provided to the decorator by the user.
        provided_output_defs(List[OutputDefinition]): List of output definitions
            explicitly provided to the decorator by the user.
        config_mapping (Any): Config mapping provided to decorator by user. In
            job/graph case, this would have been constructed from a user-provided
            config_schema and config_fn.
        ignore_output_from_composite_fn(Bool): Because of backwards compatibility
            issues, jobs ignore the return value out of the mapping if
            the user has not explicitly provided the output definitions.
            This should be removed in 0.11.0.
    """
    from dagster._core.definitions.decorators.op_decorator import (
        NoContextDecoratedOpFunction,
        resolve_checked_op_fn_inputs,
    )

    actual_output_defs: Sequence[OutputDefinition]
    if provided_output_defs is None:
        outputs_are_explicit = False
        actual_output_defs = [OutputDefinition.create_from_inferred(infer_output_props(fn))]
    elif len(provided_output_defs) == 1:
        outputs_are_explicit = True
        actual_output_defs = [provided_output_defs[0].combine_with_inferred(infer_output_props(fn))]
    else:
        outputs_are_explicit = True
        actual_output_defs = provided_output_defs

    compute_fn = NoContextDecoratedOpFunction(fn)

    actual_input_defs = resolve_checked_op_fn_inputs(
        decorator_name=decorator_name,
        fn_name=graph_name,
        compute_fn=compute_fn,
        explicit_input_defs=provided_input_defs,
        exclude_nothing=False,
    )

    kwargs = {input_def.name: InputMappingNode(input_def) for input_def in actual_input_defs}

    output = None
    returned_mapping = None
    enter_composition(graph_name, decorator_name)
    try:
        output = fn(**kwargs)
        if ignore_output_from_composition_fn:
            output = None

        returned_mapping = composite_mapping_from_output(
            output, actual_output_defs, graph_name, decorator_name
        )
    finally:
        context = exit_composition(returned_mapping)

    check.invariant(
        context.name == graph_name,
        "Composition context stack desync: received context for "
        f'"{context.name}" expected "{graph_name}"',
    )

    # line up mappings in definition order
    input_mappings = []
    for defn in actual_input_defs:
        mappings = [
            mapping for mapping in context.input_mappings if mapping.graph_input_name == defn.name
        ]

        if len(mappings) == 0:
            raise DagsterInvalidDefinitionError(
                f"{decorator_name} '{graph_name}' has unmapped input '{defn.name}'. "
                "Remove it or pass it to the appropriate op/graph invocation."
            )

        input_mappings += mappings

    output_mappings = []
    for defn in actual_output_defs:
        mapping = context.output_mapping_dict.get(defn.name)
        if mapping is None:
            # if we inferred output_defs we will be flexible and either take a mapping or not
            if not outputs_are_explicit:
                continue

            # if we are ignoring the output, disregard this unsatisfied mapping
            if ignore_output_from_composition_fn:
                continue

            raise DagsterInvalidDefinitionError(
                f"{decorator_name} '{graph_name}' has unmapped output '{defn.name}'. "
                "Remove it or return a value from the appropriate op/graph invocation."
            )
        output_mappings.append(mapping)

    return (
        input_mappings,
        output_mappings,
        context.dependencies,
        context.node_defs,
        config_mapping,
        compute_fn.positional_inputs(),
        context.node_input_assets,
    )


def get_validated_config_mapping(
    name: str,
    config_schema: Any,
    config_fn: Optional[Callable[[Any], Any]],
    decorator_name: str,
) -> Optional[ConfigMapping]:
    if config_fn is None and config_schema is None:
        return None
    elif config_fn is not None:
        return ConfigMapping(config_fn=config_fn, config_schema=config_schema)
    else:
        raise DagsterInvalidDefinitionError(
            f"{decorator_name} '{name}' defines a configuration schema but does not "
            "define a configuration function."
        )

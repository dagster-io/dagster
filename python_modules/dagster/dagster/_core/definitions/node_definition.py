from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

import dagster._check as check
from dagster._core.definitions.configurable import NamedConfigurableDefinition
from dagster._core.definitions.policy import RetryPolicy
from dagster._utils import frozendict, frozenlist

from .hook_definition import HookDefinition
from .utils import check_valid_name, validate_tags

if TYPE_CHECKING:
    from dagster._core.types.dagster_type import DagsterType

    from .asset_layer import AssetLayer
    from .composition import PendingNodeInvocation
    from .dependency import NodeHandle
    from .graph_definition import GraphDefinition
    from .input import InputDefinition
    from .output import OutputDefinition
    from .solid_definition import SolidDefinition

# base class for SolidDefinition and GraphDefinition
# represents that this is embedable within a graph
class NodeDefinition(NamedConfigurableDefinition):

    _name: str
    _description: Optional[str]
    _tags: Mapping[str, str]
    _input_defs: Sequence["InputDefinition"]
    _input_dict: Mapping[str, "InputDefinition"]
    _output_defs: Sequence["OutputDefinition"]
    _output_dict: Mapping[str, "OutputDefinition"]
    _positional_inputs: Sequence[str]

    def __init__(
        self,
        name: str,
        input_defs: Sequence["InputDefinition"],
        output_defs: Sequence["OutputDefinition"],
        description: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        positional_inputs: Optional[Sequence[str]] = None,
    ):
        self._name = check_valid_name(name)
        self._description = check.opt_str_param(description, "description")
        self._tags = validate_tags(tags)
        self._input_defs = frozenlist(input_defs)
        self._input_dict = frozendict({input_def.name: input_def for input_def in input_defs})
        check.invariant(len(self._input_defs) == len(self._input_dict), "Duplicate input def names")
        self._output_defs = frozenlist(output_defs)
        self._output_dict = frozendict({output_def.name: output_def for output_def in output_defs})
        check.invariant(
            len(self._output_defs) == len(self._output_dict), "Duplicate output def names"
        )
        check.opt_sequence_param(positional_inputs, "positional_inputs", str)
        self._positional_inputs = (
            positional_inputs
            if positional_inputs is not None
            else [inp.name for inp in self._input_defs]
        )

    @property
    @abstractmethod
    def node_type_str(self) -> str:
        ...

    @property
    @abstractmethod
    def is_graph_job_op_node(self) -> bool:
        ...

    @abstractmethod
    def all_dagster_types(self) -> Iterable["DagsterType"]:
        ...

    @property
    def name(self) -> str:
        return self._name

    def describe_node(self) -> str:
        return f"{self.node_type_str} '{self.name}'"

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def tags(self) -> Mapping[str, str]:
        return self._tags

    @property
    def positional_inputs(self) -> Sequence[str]:
        return self._positional_inputs

    @property
    def input_defs(self) -> Sequence["InputDefinition"]:
        return self._input_defs

    @property
    def input_dict(self) -> Mapping[str, "InputDefinition"]:
        return self._input_dict

    def resolve_input_name_at_position(self, idx: int) -> Optional[str]:
        if idx >= len(self._positional_inputs):
            if not (
                len(self._input_defs) - len(self._positional_inputs) == 1
                and idx == len(self._input_defs) - 1
            ):
                return None

            # handle special case where there is only 1 non-positional arg that we could resolve to
            names = [
                inp.name for inp in self._input_defs if inp.name not in self._positional_inputs
            ]
            check.invariant(len(names) == 1, "if check above should prevent this")
            return names[0]

        return self._positional_inputs[idx]

    @property
    def output_defs(self) -> Sequence["OutputDefinition"]:
        return self._output_defs

    @property
    def output_dict(self) -> Mapping[str, "OutputDefinition"]:
        return self._output_dict

    def has_input(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._input_dict

    def input_def_named(self, name: str) -> "InputDefinition":
        check.str_param(name, "name")
        return self._input_dict[name]

    def has_output(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._output_dict

    def output_def_named(self, name: str) -> "OutputDefinition":
        check.str_param(name, "name")
        return self._output_dict[name]

    @abstractmethod
    def iterate_node_defs(self) -> Iterable["NodeDefinition"]:
        ...

    @abstractmethod
    def iterate_solid_defs(self) -> Iterable["SolidDefinition"]:
        ...

    @abstractmethod
    def resolve_output_to_origin(
        self,
        output_name: str,
        handle: Optional["NodeHandle"],
    ) -> Tuple["OutputDefinition", Optional["NodeHandle"]]:
        ...

    @abstractmethod
    def resolve_output_to_origin_op_def(self, output_name: str) -> "SolidDefinition":
        ...

    @abstractmethod
    def input_has_default(self, input_name: str) -> bool:
        ...

    @abstractmethod
    def default_value_for_input(self, input_name: str) -> object:
        ...

    @abstractmethod
    def input_supports_dynamic_output_dep(self, input_name: str) -> bool:
        ...

    def all_input_output_types(self) -> Iterator["DagsterType"]:
        for input_def in self._input_defs:
            yield input_def.dagster_type
            yield from input_def.dagster_type.inner_types

        for output_def in self._output_defs:
            yield output_def.dagster_type
            yield from output_def.dagster_type.inner_types

    def __call__(self, *args: object, **kwargs: object) -> object:
        from .composition import PendingNodeInvocation

        return PendingNodeInvocation(
            node_def=self,
            given_alias=None,
            tags=None,
            hook_defs=None,
            retry_policy=None,
        )(*args, **kwargs)

    def alias(self, name: str) -> "PendingNodeInvocation":
        from .composition import PendingNodeInvocation

        check.str_param(name, "name")

        return PendingNodeInvocation(
            node_def=self,
            given_alias=name,
            tags=None,
            hook_defs=None,
            retry_policy=None,
        )

    def tag(self, tags: Optional[Mapping[str, str]]) -> "PendingNodeInvocation":
        from .composition import PendingNodeInvocation

        return PendingNodeInvocation(
            node_def=self,
            given_alias=None,
            tags=validate_tags(tags),
            hook_defs=None,
            retry_policy=None,
        )

    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "PendingNodeInvocation":
        from .composition import PendingNodeInvocation

        hook_defs = frozenset(check.set_param(hook_defs, "hook_defs", of_type=HookDefinition))

        return PendingNodeInvocation(
            node_def=self,
            given_alias=None,
            tags=None,
            hook_defs=hook_defs,
            retry_policy=None,
        )

    def with_retry_policy(self, retry_policy: RetryPolicy) -> "PendingNodeInvocation":
        from .composition import PendingNodeInvocation

        return PendingNodeInvocation(
            node_def=self,
            given_alias=None,
            tags=None,
            hook_defs=None,
            retry_policy=retry_policy,
        )

    def ensure_graph_def(self) -> "GraphDefinition":
        from .graph_definition import GraphDefinition

        if isinstance(self, GraphDefinition):
            return self

        check.failed(f"{self.name} is not a GraphDefinition")

    def ensure_solid_def(self) -> "SolidDefinition":
        from .solid_definition import SolidDefinition

        if isinstance(self, SolidDefinition):
            return self

        check.failed(f"{self.name} is not a SolidDefinition")

    @abstractmethod
    def get_inputs_must_be_resolved_top_level(
        self, asset_layer: "AssetLayer", handle: Optional["NodeHandle"] = None
    ) -> Sequence["InputDefinition"]:
        ...

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

from typing_extensions import TypeAlias, TypeVar

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._serdes.serdes import (
    whitelist_for_serdes,
)
from dagster._utils import hash_collection

from .hook_definition import HookDefinition
from .input import FanInInputPointer, InputDefinition, InputMapping, InputPointer
from .output import OutputDefinition
from .utils import DEFAULT_OUTPUT, struct_to_string, validate_tags

if TYPE_CHECKING:
    from dagster._core.definitions.op_definition import OpDefinition

    from .asset_layer import AssetLayer
    from .composition import MappedInputPlaceholder
    from .graph_definition import GraphDefinition
    from .node_definition import NodeDefinition
    from .resource_requirement import ResourceRequirement

T_DependencyKey = TypeVar("T_DependencyKey", str, "NodeInvocation")
DependencyMapping: TypeAlias = Mapping[T_DependencyKey, Mapping[str, "IDependencyDefinition"]]


class NodeInvocation(
    NamedTuple(
        "Node",
        [
            ("name", PublicAttr[str]),
            ("alias", PublicAttr[Optional[str]]),
            ("tags", PublicAttr[Mapping[str, Any]]),
            ("hook_defs", PublicAttr[AbstractSet[HookDefinition]]),
            ("retry_policy", PublicAttr[Optional[RetryPolicy]]),
        ],
    )
):
    """Identifies an instance of a node in a graph dependency structure.

    Args:
        name (str): Name of the node of which this is an instance.
        alias (Optional[str]): Name specific to this instance of the node. Necessary when there are
            multiple instances of the same node.
        tags (Optional[Dict[str, Any]]): Optional tags values to extend or override those
            set on the node definition.
        hook_defs (Optional[AbstractSet[HookDefinition]]): A set of hook definitions applied to the
            node instance.

    Examples:
    In general, users should prefer not to construct this class directly or use the
    :py:class:`JobDefinition` API that requires instances of this class. Instead, use the
    :py:func:`@job <job>` API:

    .. code-block:: python

        from dagster import job

        @job
        def my_job():
            other_name = some_op.alias('other_name')
            some_graph(other_name(some_op))

    """

    def __new__(
        cls,
        name: str,
        alias: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        return super().__new__(
            cls,
            name=check.str_param(name, "name"),
            alias=check.opt_str_param(alias, "alias"),
            tags=check.opt_mapping_param(tags, "tags", value_type=str, key_type=str),
            hook_defs=check.opt_set_param(hook_defs, "hook_defs", of_type=HookDefinition),
            retry_policy=check.opt_inst_param(retry_policy, "retry_policy", RetryPolicy),
        )

    # Needs to be hashable because this class is used as a key in dependencies dicts
    def __hash__(self) -> int:
        if not hasattr(self, "_hash"):
            self._hash = hash_collection(self)
        return self._hash


class Node(ABC):
    """Node invocation within a graph. Identified by its name inside the graph."""

    name: str
    definition: "NodeDefinition"
    graph_definition: "GraphDefinition"
    _additional_tags: Mapping[str, str]
    _hook_defs: AbstractSet[HookDefinition]
    _retry_policy: Optional[RetryPolicy]
    _inputs: Mapping[str, "NodeInput"]
    _outputs: Mapping[str, "NodeOutput"]

    def __init__(
        self,
        name: str,
        definition: "NodeDefinition",
        graph_definition: "GraphDefinition",
        tags: Optional[Mapping[str, str]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        from .graph_definition import GraphDefinition
        from .node_definition import NodeDefinition

        self.name = check.str_param(name, "name")
        self.definition = check.inst_param(definition, "definition", NodeDefinition)
        self.graph_definition = check.inst_param(
            graph_definition,
            "graph_definition",
            GraphDefinition,
        )
        self._additional_tags = validate_tags(tags)
        self._hook_defs = check.opt_set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        self._retry_policy = check.opt_inst_param(retry_policy, "retry_policy", RetryPolicy)

        self._inputs = {
            name: NodeInput(self, input_def)
            for name, input_def in self.definition.input_dict.items()
        }
        self._outputs = {
            name: NodeOutput(self, output_def)
            for name, output_def in self.definition.output_dict.items()
        }

    def inputs(self) -> Iterable["NodeInput"]:
        return self._inputs.values()

    def outputs(self) -> Iterable["NodeOutput"]:
        return self._outputs.values()

    def get_input(self, name: str) -> "NodeInput":
        check.str_param(name, "name")
        return self._inputs[name]

    def get_output(self, name: str) -> "NodeOutput":
        check.str_param(name, "name")
        return self._outputs[name]

    def has_input(self, name: str) -> bool:
        return self.definition.has_input(name)

    def input_def_named(self, name: str) -> InputDefinition:
        return self.definition.input_def_named(name)

    def has_output(self, name: str) -> bool:
        return self.definition.has_output(name)

    def output_def_named(self, name: str) -> OutputDefinition:
        return self.definition.output_def_named(name)

    @property
    def input_dict(self) -> Mapping[str, InputDefinition]:
        return self.definition.input_dict

    @property
    def output_dict(self) -> Mapping[str, OutputDefinition]:
        return self.definition.output_dict

    @property
    def tags(self) -> Mapping[str, str]:
        return {**self.definition.tags, **self._additional_tags}

    def container_maps_input(self, input_name: str) -> bool:
        return (
            self.graph_definition.input_mapping_for_pointer(InputPointer(self.name, input_name))
            is not None
        )

    def container_mapped_input(self, input_name: str) -> InputMapping:
        mapping = self.graph_definition.input_mapping_for_pointer(
            InputPointer(self.name, input_name)
        )
        if mapping is None:
            check.failed(
                f"container does not map input {input_name}, check container_maps_input first"
            )
        return mapping

    def container_maps_fan_in_input(self, input_name: str, fan_in_index: int) -> bool:
        return (
            self.graph_definition.input_mapping_for_pointer(
                FanInInputPointer(self.name, input_name, fan_in_index)
            )
            is not None
        )

    def container_mapped_fan_in_input(self, input_name: str, fan_in_index: int) -> InputMapping:
        mapping = self.graph_definition.input_mapping_for_pointer(
            FanInInputPointer(self.name, input_name, fan_in_index)
        )
        if mapping is None:
            check.failed(
                f"container does not map fan-in {input_name} idx {fan_in_index}, check "
                "container_maps_fan_in_input first"
            )

        return mapping

    @property
    def hook_defs(self) -> AbstractSet[HookDefinition]:
        return self._hook_defs

    @property
    def retry_policy(self) -> Optional[RetryPolicy]:
        return self._retry_policy

    @abstractmethod
    def describe_node(self) -> str: ...

    @abstractmethod
    def get_resource_requirements(
        self,
        outer_container: "GraphDefinition",
        parent_handle: Optional["NodeHandle"] = None,
        asset_layer: Optional["AssetLayer"] = None,
    ) -> Iterator["ResourceRequirement"]: ...


class GraphNode(Node):
    definition: "GraphDefinition"

    def __init__(
        self,
        name: str,
        definition: "GraphDefinition",
        graph_definition: "GraphDefinition",
        tags: Optional[Mapping[str, str]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        from .graph_definition import GraphDefinition

        check.inst_param(definition, "definition", GraphDefinition)
        super().__init__(name, definition, graph_definition, tags, hook_defs, retry_policy)

    def get_resource_requirements(
        self,
        outer_container: "GraphDefinition",
        parent_handle: Optional["NodeHandle"] = None,
        asset_layer: Optional["AssetLayer"] = None,
    ) -> Iterator["ResourceRequirement"]:
        cur_node_handle = NodeHandle(self.name, parent_handle)

        for node in self.definition.node_dict.values():
            yield from node.get_resource_requirements(
                asset_layer=asset_layer,
                outer_container=self.definition,
                parent_handle=cur_node_handle,
            )

    def describe_node(self) -> str:
        return f"graph '{self.name}'"


class OpNode(Node):
    definition: "OpDefinition"

    def __init__(
        self,
        name: str,
        definition: "OpDefinition",
        graph_definition: "GraphDefinition",
        tags: Optional[Mapping[str, str]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        from .op_definition import OpDefinition

        check.inst_param(definition, "definition", OpDefinition)
        super().__init__(name, definition, graph_definition, tags, hook_defs, retry_policy)

    def get_resource_requirements(
        self,
        outer_container: "GraphDefinition",
        parent_handle: Optional["NodeHandle"] = None,
        asset_layer: Optional["AssetLayer"] = None,
    ) -> Iterator["ResourceRequirement"]:
        from .resource_requirement import InputManagerRequirement

        cur_node_handle = NodeHandle(self.name, parent_handle)

        for requirement in self.definition.get_resource_requirements(
            (cur_node_handle, asset_layer)
        ):
            # If requirement is a root input manager requirement, but the corresponding node has an upstream output, then ignore the requirement.
            if (
                isinstance(requirement, InputManagerRequirement)
                and outer_container.dependency_structure.has_deps(
                    NodeInput(self, self.definition.input_def_named(requirement.input_name))
                )
                and requirement.root_input
            ):
                continue
            yield requirement
        for hook_def in self.hook_defs:
            yield from hook_def.get_resource_requirements(self.describe_node())

    def describe_node(self) -> str:
        return f"op '{self.name}'"


@whitelist_for_serdes(storage_name="SolidHandle")
class NodeHandle(NamedTuple("_NodeHandle", [("name", str), ("parent", Optional["NodeHandle"])])):
    """A structured object to identify nodes in the potentially recursive graph structure."""

    def __new__(cls, name: str, parent: Optional["NodeHandle"]):
        return super(NodeHandle, cls).__new__(
            cls,
            check.str_param(name, "name"),
            check.opt_inst_param(parent, "parent", NodeHandle),
        )

    def __str__(self):
        return self.to_string()

    @property
    def root(self):
        if self.parent:
            return self.parent.root
        else:
            return self

    @property
    def path(self) -> Sequence[str]:
        """Return a list representation of the handle.

        Inverse of NodeHandle.from_path.

        Returns:
            List[str]:
        """
        path: List[str] = []
        cur = self
        while cur:
            path.append(cur.name)
            cur = cur.parent
        path.reverse()
        return path

    def to_string(self) -> str:
        """Return a unique string representation of the handle.

        Inverse of NodeHandle.from_string.
        """
        return self.parent.to_string() + "." + self.name if self.parent else self.name

    def is_or_descends_from(self, handle: "NodeHandle") -> bool:
        """Check if the handle is or descends from another handle.

        Args:
            handle (NodeHandle): The handle to check against.

        Returns:
            bool:
        """
        check.inst_param(handle, "handle", NodeHandle)

        for idx in range(len(handle.path)):
            if idx >= len(self.path):
                return False
            if self.path[idx] != handle.path[idx]:
                return False
        return True

    def pop(self, ancestor: "NodeHandle") -> Optional["NodeHandle"]:
        """Return a copy of the handle with some of its ancestors pruned.

        Args:
            ancestor (NodeHandle): Handle to an ancestor of the current handle.

        Returns:
            NodeHandle:

        Example:
        .. code-block:: python

            handle = NodeHandle('baz', NodeHandle('bar', NodeHandle('foo', None)))
            ancestor = NodeHandle('bar', NodeHandle('foo', None))
            assert handle.pop(ancestor) == NodeHandle('baz', None)
        """
        check.inst_param(ancestor, "ancestor", NodeHandle)
        check.invariant(
            self.is_or_descends_from(ancestor),
            f"Handle {self.to_string()} does not descend from {ancestor.to_string()}",
        )

        return NodeHandle.from_path(self.path[len(ancestor.path) :])

    def with_ancestor(self, ancestor: Optional["NodeHandle"]) -> "NodeHandle":
        """Returns a copy of the handle with an ancestor grafted on.

        Args:
            ancestor (NodeHandle): Handle to the new ancestor.

        Returns:
            NodeHandle:

        Example:
        .. code-block:: python

            handle = NodeHandle('baz', NodeHandle('bar', NodeHandle('foo', None)))
            ancestor = NodeHandle('quux' None)
            assert handle.with_ancestor(ancestor) == NodeHandle(
                'baz', NodeHandle('bar', NodeHandle('foo', NodeHandle('quux', None)))
            )
        """
        check.opt_inst_param(ancestor, "ancestor", NodeHandle)

        return NodeHandle.from_path([*(ancestor.path if ancestor else []), *self.path])

    @staticmethod
    def from_path(path: Sequence[str]) -> "NodeHandle":
        check.sequence_param(path, "path", of_type=str)

        cur: Optional["NodeHandle"] = None
        _path = list(path)
        while len(_path) > 0:
            cur = NodeHandle(name=_path.pop(0), parent=cur)

        if cur is None:
            check.failed(f"Invalid handle path {path}")

        return cur

    @staticmethod
    def from_string(handle_str: str) -> "NodeHandle":
        check.str_param(handle_str, "handle_str")

        path = handle_str.split(".")
        return NodeHandle.from_path(path)

    @classmethod
    def from_dict(cls, dict_repr: Mapping[str, Any]) -> "NodeHandle":
        """This method makes it possible to load a potentially nested NodeHandle after a
        roundtrip through json.loads(json.dumps(NodeHandle._asdict())).
        """
        check.dict_param(dict_repr, "dict_repr", key_type=str)
        check.invariant(
            "name" in dict_repr, "Dict representation of NodeHandle must have a 'name' key"
        )
        check.invariant(
            "parent" in dict_repr, "Dict representation of NodeHandle must have a 'parent' key"
        )

        if isinstance(dict_repr["parent"], (list, tuple)):
            parent = NodeHandle.from_dict(
                {
                    "name": dict_repr["parent"][0],
                    "parent": dict_repr["parent"][1],
                }
            )
        else:
            parent = dict_repr["parent"]

        return NodeHandle(name=dict_repr["name"], parent=parent)


class NodeInputHandle(
    NamedTuple("_NodeInputHandle", [("node_handle", NodeHandle), ("input_name", str)])
):
    """A structured object to uniquely identify inputs in the potentially recursive graph structure."""


class NodeOutputHandle(
    NamedTuple("_NodeOutputHandle", [("node_handle", NodeHandle), ("output_name", str)])
):
    """A structured object to uniquely identify outputs in the potentially recursive graph structure."""


class NodeInput(NamedTuple("_NodeInput", [("node", Node), ("input_def", InputDefinition)])):
    def __new__(cls, node: Node, input_def: InputDefinition):
        return super(NodeInput, cls).__new__(
            cls,
            check.inst_param(node, "node", Node),
            check.inst_param(input_def, "input_def", InputDefinition),
        )

    def _inner_str(self) -> str:
        return struct_to_string(
            "NodeInput",
            node_name=self.node.name,
            input_name=self.input_def.name,
        )

    def __str__(self):
        return self._inner_str()

    def __repr__(self):
        return self._inner_str()

    def __hash__(self):
        return hash((self.node.name, self.input_def.name))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, NodeInput)
            and self.node.name == other.node.name
            and self.input_def.name == other.input_def.name
        )

    @property
    def node_name(self) -> str:
        return self.node.name

    @property
    def input_name(self) -> str:
        return self.input_def.name


class NodeOutput(NamedTuple("_NodeOutput", [("node", Node), ("output_def", OutputDefinition)])):
    def __new__(cls, node: Node, output_def: OutputDefinition):
        return super(NodeOutput, cls).__new__(
            cls,
            check.inst_param(node, "node", Node),
            check.inst_param(output_def, "output_def", OutputDefinition),
        )

    def _inner_str(self) -> str:
        return struct_to_string(
            "NodeOutput",
            node_name=self.node.name,
            output_name=self.output_def.name,
        )

    def __str__(self):
        return self._inner_str()

    def __repr__(self):
        return self._inner_str()

    def __hash__(self) -> int:
        return hash((self.node.name, self.output_def.name))

    def __eq__(self, other: Any) -> bool:
        return self.node.name == other.node.name and self.output_def.name == other.output_def.name

    def describe(self) -> str:
        return f"{self.node_name}:{self.output_def.name}"

    @property
    def node_name(self) -> str:
        return self.node.name

    @property
    def is_dynamic(self) -> bool:
        return self.output_def.is_dynamic

    @property
    def output_name(self) -> str:
        return self.output_def.name


class DependencyType(Enum):
    DIRECT = "DIRECT"
    FAN_IN = "FAN_IN"
    DYNAMIC_COLLECT = "DYNAMIC_COLLECT"


class IDependencyDefinition(ABC):
    @abstractmethod
    def get_node_dependencies(self) -> Sequence["DependencyDefinition"]:
        pass

    @abstractmethod
    def is_fan_in(self) -> bool:
        """The result passed to the corresponding input will be a List made from different node outputs."""


class DependencyDefinition(
    NamedTuple(
        "_DependencyDefinition", [("node", str), ("output", str), ("description", Optional[str])]
    ),
    IDependencyDefinition,
):
    """Represents an edge in the DAG of nodes (ops or graphs) forming a job.

    This object is used at the leaves of a dictionary structure that represents the complete
    dependency structure of a job whose keys represent the dependent node and dependent
    input, so this object only contains information about the dependee.

    Concretely, if the input named 'input' of op_b depends on the output named 'result' of
    op_a, and the output named 'other_result' of graph_a, the structure will look as follows:

    .. code-block:: python

        dependency_structure = {
            'my_downstream_op': {
                'input': DependencyDefinition('my_upstream_op', 'result')
            }
            'my_downstream_op': {
                'input': DependencyDefinition('my_upstream_graph', 'result')
            }
        }

    In general, users should prefer not to construct this class directly or use the
    :py:class:`JobDefinition` API that requires instances of this class. Instead, use the
    :py:func:`@job <job>` API:

    .. code-block:: python

        @job
        def the_job():
            node_b(node_a())


    Args:
        node (str): The name of the node (op or graph) that is depended on, that is, from which the value
            passed between the two nodes originates.
        output (Optional[str]): The name of the output that is depended on. (default: "result")
        description (Optional[str]): Human-readable description of this dependency.
    """

    def __new__(
        cls,
        node: str,
        output: str = DEFAULT_OUTPUT,
        description: Optional[str] = None,
    ):
        return super(DependencyDefinition, cls).__new__(
            cls,
            check.str_param(node, "node"),
            check.str_param(output, "output"),
            check.opt_str_param(description, "description"),
        )

    def get_node_dependencies(self) -> Sequence["DependencyDefinition"]:
        return [self]

    @public
    def is_fan_in(self) -> bool:
        """Return True if the dependency is fan-in (always False for DependencyDefinition)."""
        return False

    def get_op_dependencies(self) -> Sequence["DependencyDefinition"]:
        return [self]


class MultiDependencyDefinition(
    NamedTuple(
        "_MultiDependencyDefinition",
        [
            (
                "dependencies",
                PublicAttr[Sequence[Union[DependencyDefinition, Type["MappedInputPlaceholder"]]]],
            )
        ],
    ),
    IDependencyDefinition,
):
    """Represents a fan-in edge in the DAG of op instances forming a job.

    This object is used only when an input of type ``List[T]`` is assembled by fanning-in multiple
    upstream outputs of type ``T``.

    This object is used at the leaves of a dictionary structure that represents the complete
    dependency structure of a job whose keys represent the dependent ops or graphs and dependent
    input, so this object only contains information about the dependee.

    Concretely, if the input named 'input' of op_c depends on the outputs named 'result' of
    op_a and op_b, this structure will look as follows:

    .. code-block:: python

        dependency_structure = {
            'op_c': {
                'input': MultiDependencyDefinition(
                    [
                        DependencyDefinition('op_a', 'result'),
                        DependencyDefinition('op_b', 'result')
                    ]
                )
            }
        }

    In general, users should prefer not to construct this class directly or use the
    :py:class:`JobDefinition` API that requires instances of this class. Instead, use the
    :py:func:`@job <job>` API:

    .. code-block:: python

        @job
        def the_job():
            op_c(op_a(), op_b())

    Args:
        dependencies (List[Union[DependencyDefinition, Type[MappedInputPlaceHolder]]]): List of
            upstream dependencies fanned in to this input.
    """

    def __new__(
        cls,
        dependencies: Sequence[Union[DependencyDefinition, Type["MappedInputPlaceholder"]]],
    ):
        from .composition import MappedInputPlaceholder

        deps = check.sequence_param(dependencies, "dependencies")
        seen = {}
        for dep in deps:
            if isinstance(dep, DependencyDefinition):
                key = dep.node + ":" + dep.output
                if key in seen:
                    raise DagsterInvalidDefinitionError(
                        f'Duplicate dependencies on node "{dep.node}" output "{dep.output}" '
                        "used in the same MultiDependencyDefinition."
                    )
                seen[key] = True
            elif dep is MappedInputPlaceholder:
                pass
            else:
                check.failed(f"Unexpected dependencies entry {dep}")

        return super(MultiDependencyDefinition, cls).__new__(cls, deps)

    @public
    def get_node_dependencies(self) -> Sequence[DependencyDefinition]:
        """Return the list of :py:class:`DependencyDefinition` contained by this object."""
        return [dep for dep in self.dependencies if isinstance(dep, DependencyDefinition)]

    @public
    def is_fan_in(self) -> bool:
        """Return `True` if the dependency is fan-in (always True for MultiDependencyDefinition)."""
        return True

    @public
    def get_dependencies_and_mappings(
        self,
    ) -> Sequence[Union[DependencyDefinition, Type["MappedInputPlaceholder"]]]:
        """Return the combined list of dependencies contained by this object, inculding of :py:class:`DependencyDefinition` and :py:class:`MappedInputPlaceholder` objects."""
        return self.dependencies


class BlockingAssetChecksDependencyDefinition(
    IDependencyDefinition,
    NamedTuple(
        "_BlockingAssetChecksDependencyDefinition",
        [
            (
                "asset_check_dependencies",
                Sequence[DependencyDefinition],
            ),
            ("other_dependency", Optional[DependencyDefinition]),
        ],
    ),
):
    """An input that depends on a set of outputs that correspond to upstream asset checks, and also
    optionally depends on a single upstream output that does not correspond to an asset check.

    We model this with a different kind of DependencyDefinition than MultiDependencyDefinition,
    because we treat the value that's passed to the input parameter differently: we ignore the asset
    check dependencies and only pass a single value, instead of a fanned-in list.
    """

    @public
    def get_node_dependencies(self) -> Sequence[DependencyDefinition]:
        """Return the list of :py:class:`DependencyDefinition` contained by this object."""
        if self.other_dependency:
            return [*self.asset_check_dependencies, self.other_dependency]
        else:
            return self.asset_check_dependencies

    @public
    def is_fan_in(self) -> bool:
        return False

    @public
    def get_dependencies_and_mappings(
        self,
    ) -> Sequence[Union[DependencyDefinition, Type["MappedInputPlaceholder"]]]:
        return self.get_node_dependencies()


class DynamicCollectDependencyDefinition(
    NamedTuple("_DynamicCollectDependencyDefinition", [("node_name", str), ("output_name", str)]),
    IDependencyDefinition,
):
    def get_node_dependencies(self) -> Sequence[DependencyDefinition]:
        return [DependencyDefinition(self.node_name, self.output_name)]

    def is_fan_in(self) -> bool:
        return True


DepTypeAndOutputs: TypeAlias = Tuple[
    DependencyType,
    Union[NodeOutput, List[Union[NodeOutput, Type["MappedInputPlaceholder"]]]],
]

InputToOutputMap: TypeAlias = Dict[NodeInput, DepTypeAndOutputs]


def _create_handle_dict(
    node_dict: Mapping[str, Node],
    dep_dict: DependencyMapping[str],
) -> InputToOutputMap:
    from .composition import MappedInputPlaceholder

    check.mapping_param(node_dict, "node_dict", key_type=str, value_type=Node)
    check.two_dim_mapping_param(dep_dict, "dep_dict", value_type=IDependencyDefinition)

    handle_dict: InputToOutputMap = {}

    for node_name, input_dict in dep_dict.items():
        from_node = node_dict[node_name]
        for input_name, dep_def in input_dict.items():
            if isinstance(
                dep_def, (MultiDependencyDefinition, BlockingAssetChecksDependencyDefinition)
            ):
                handles: List[Union[NodeOutput, Type[MappedInputPlaceholder]]] = []
                for inner_dep in dep_def.get_dependencies_and_mappings():
                    if isinstance(inner_dep, DependencyDefinition):
                        handles.append(node_dict[inner_dep.node].get_output(inner_dep.output))
                    elif inner_dep is MappedInputPlaceholder:
                        handles.append(inner_dep)
                    else:
                        check.failed(
                            f"Unexpected MultiDependencyDefinition dependencies type {inner_dep}"
                        )

                handle_dict[from_node.get_input(input_name)] = (DependencyType.FAN_IN, handles)

            elif isinstance(dep_def, DependencyDefinition):
                handle_dict[from_node.get_input(input_name)] = (
                    DependencyType.DIRECT,
                    node_dict[dep_def.node].get_output(dep_def.output),
                )
            elif isinstance(dep_def, DynamicCollectDependencyDefinition):
                handle_dict[from_node.get_input(input_name)] = (
                    DependencyType.DYNAMIC_COLLECT,
                    node_dict[dep_def.node_name].get_output(dep_def.output_name),
                )

            else:
                check.failed(f"Unknown dependency type {dep_def}")

    return handle_dict


class DependencyStructure:
    @staticmethod
    def from_definitions(
        nodes: Mapping[str, Node], dep_dict: DependencyMapping[str]
    ) -> "DependencyStructure":
        return DependencyStructure(
            list(dep_dict.keys()),
            _create_handle_dict(nodes, dep_dict),
            dep_dict,
        )

    _node_input_index: DefaultDict[str, Dict[NodeInput, List[NodeOutput]]]
    _node_output_index: Dict[str, DefaultDict[NodeOutput, List[NodeInput]]]
    _dynamic_fan_out_index: Dict[str, NodeOutput]
    _collect_index: Dict[str, Set[NodeOutput]]
    _deps_by_node_name: DependencyMapping[str]

    def __init__(
        self,
        node_names: Sequence[str],
        input_to_output_map: InputToOutputMap,
        deps_by_node_name: DependencyMapping[str],
    ):
        self._node_names = node_names
        self._input_to_output_map = input_to_output_map
        self._deps_by_node_name = deps_by_node_name

        # Building up a couple indexes here so that one can look up all the upstream output handles
        # or downstream input handles in O(1). Without this, this can become O(N^2) where N is node
        # count during the GraphQL query in particular

        # node_name => input_handle => list[output_handle]
        self._node_input_index = defaultdict(dict)

        # node_name => output_handle => list[input_handle]
        self._node_output_index = defaultdict(lambda: defaultdict(list))

        # node_name => dynamic output_handle that this node will dupe for
        self._dynamic_fan_out_index = {}

        # node_name => set of dynamic output_handle this collects over
        self._collect_index = defaultdict(set)

        for node_input, (dep_type, node_output_or_list) in self._input_to_output_map.items():
            if dep_type == DependencyType.FAN_IN:
                node_output_list: List[NodeOutput] = []
                for node_output in node_output_or_list:
                    if not isinstance(node_output, NodeOutput):
                        continue

                    if node_output.is_dynamic:
                        raise DagsterInvalidDefinitionError(
                            "Currently, items in a fan-in dependency cannot be downstream of"
                            " dynamic outputs. Problematic dependency on dynamic output"
                            f' "{node_output.describe()}".'
                        )
                    if self._dynamic_fan_out_index.get(node_output.node_name):
                        raise DagsterInvalidDefinitionError(
                            "Currently, items in a fan-in dependency cannot be downstream of"
                            " dynamic outputs. Problematic dependency on output"
                            f' "{node_output.describe()}", downstream of'
                            f' "{self._dynamic_fan_out_index[node_output.node_name].describe()}".'
                        )

                    node_output_list.append(node_output)
            elif dep_type == DependencyType.DIRECT:
                node_output = cast(NodeOutput, node_output_or_list)

                if node_output.is_dynamic:
                    self._validate_and_set_fan_out(node_input, node_output)

                if self._dynamic_fan_out_index.get(node_output.node_name):
                    self._validate_and_set_fan_out(
                        node_input, self._dynamic_fan_out_index[node_output.node_name]
                    )

                node_output_list = [node_output]
            elif dep_type == DependencyType.DYNAMIC_COLLECT:
                node_output = cast(NodeOutput, node_output_or_list)

                if node_output.is_dynamic:
                    self._validate_and_set_collect(node_input, node_output)

                elif self._dynamic_fan_out_index.get(node_output.node_name):
                    self._validate_and_set_collect(
                        node_input,
                        self._dynamic_fan_out_index[node_output.node_name],
                    )
                else:
                    check.failed(
                        f"Unexpected dynamic fan in dep created {node_output} -> {node_input}"
                    )

                node_output_list = [node_output]
            else:
                check.failed(f"Unexpected dep type {dep_type}")

            self._node_input_index[node_input.node.name][node_input] = node_output_list
            for node_output in node_output_list:
                self._node_output_index[node_output.node.name][node_output].append(node_input)

    def _validate_and_set_fan_out(self, node_input: NodeInput, node_output: NodeOutput) -> None:
        """Helper function for populating _dynamic_fan_out_index."""
        if not node_input.node.definition.input_supports_dynamic_output_dep(node_input.input_name):
            raise DagsterInvalidDefinitionError(
                f"{node_input.node.describe_node()} cannot be downstream of dynamic output"
                f' "{node_output.describe()}" since input "{node_input.input_name}" maps to a'
                " node that is already downstream of another dynamic output. Nodes cannot be"
                " downstream of more than one dynamic output"
            )

        if self._collect_index.get(node_input.node_name):
            raise DagsterInvalidDefinitionError(
                f"{node_input.node.describe_node()} cannot be both downstream of dynamic output "
                f"{node_output.describe()} and collect over dynamic output "
                f"{next(iter(self._collect_index[node_input.node_name])).describe()}."
            )

        if self._dynamic_fan_out_index.get(node_input.node_name) is None:
            self._dynamic_fan_out_index[node_input.node_name] = node_output
            return

        if self._dynamic_fan_out_index[node_input.node_name] != node_output:
            raise DagsterInvalidDefinitionError(
                f"{node_input.node.describe_node()} cannot be downstream of more than one dynamic"
                f' output. It is downstream of both "{node_output.describe()}" and'
                f' "{self._dynamic_fan_out_index[node_input.node_name].describe()}"'
            )

    def _validate_and_set_collect(
        self,
        node_input: NodeInput,
        node_output: NodeOutput,
    ) -> None:
        if self._dynamic_fan_out_index.get(node_input.node_name):
            raise DagsterInvalidDefinitionError(
                f"{node_input.node.describe_node()} cannot both collect over dynamic output "
                f"{node_output.describe()} and be downstream of the dynamic output "
                f"{self._dynamic_fan_out_index[node_input.node_name].describe()}."
            )

        self._collect_index[node_input.node_name].add(node_output)

        # if the output is already fanned out
        if self._dynamic_fan_out_index.get(node_output.node_name):
            raise DagsterInvalidDefinitionError(
                f"{node_input.node.describe_node()} cannot be downstream of more than one dynamic"
                f' output. It is downstream of both "{node_output.describe()}" and'
                f' "{self._dynamic_fan_out_index[node_output.node_name].describe()}"'
            )

    def all_upstream_outputs_from_node(self, node_name: str) -> Sequence[NodeOutput]:
        check.str_param(node_name, "node_name")

        # flatten out all outputs that feed into the inputs of this node
        return [
            output_handle
            for output_handle_list in self._node_input_index[node_name].values()
            for output_handle in output_handle_list
        ]

    def input_to_upstream_outputs_for_node(
        self, node_name: str
    ) -> Mapping[NodeInput, Sequence[NodeOutput]]:
        """Returns a Dict[NodeInput, List[NodeOutput]] that encodes
        where all the the inputs are sourced from upstream. Usually the
        List[NodeOutput] will be a list of one, except for the
        multi-dependency case.
        """
        check.str_param(node_name, "node_name")
        return self._node_input_index[node_name]

    def output_to_downstream_inputs_for_node(
        self, node_name: str
    ) -> Mapping[NodeOutput, Sequence[NodeInput]]:
        """Returns a Dict[NodeOutput, List[NodeInput]] that
        represents all the downstream inputs for each output in the
        dictionary.
        """
        check.str_param(node_name, "node_name")
        return self._node_output_index[node_name]

    def has_direct_dep(self, node_input: NodeInput) -> bool:
        check.inst_param(node_input, "node_input", NodeInput)
        if node_input not in self._input_to_output_map:
            return False
        dep_type, _ = self._input_to_output_map[node_input]
        return dep_type == DependencyType.DIRECT

    def get_direct_dep(self, node_input: NodeInput) -> NodeOutput:
        check.inst_param(node_input, "node_input", NodeInput)
        dep_type, dep = self._input_to_output_map[node_input]
        check.invariant(
            dep_type == DependencyType.DIRECT,
            f"Cannot call get_direct_dep when dep is not singular, got {dep_type}",
        )
        return cast(NodeOutput, dep)

    def get_dependency_definition(self, node_input: NodeInput) -> Optional[IDependencyDefinition]:
        return self._deps_by_node_name[node_input.node_name].get(node_input.input_name)

    def has_fan_in_deps(self, node_input: NodeInput) -> bool:
        check.inst_param(node_input, "node_input", NodeInput)
        if node_input not in self._input_to_output_map:
            return False
        dep_type, _ = self._input_to_output_map[node_input]
        return dep_type == DependencyType.FAN_IN

    def get_fan_in_deps(
        self, node_input: NodeInput
    ) -> Sequence[Union[NodeOutput, Type["MappedInputPlaceholder"]]]:
        check.inst_param(node_input, "node_input", NodeInput)
        dep_type, deps = self._input_to_output_map[node_input]
        check.invariant(
            dep_type == DependencyType.FAN_IN,
            f"Cannot call get_multi_dep when dep is not fan in, got {dep_type}",
        )
        return cast(List[Union[NodeOutput, Type["MappedInputPlaceholder"]]], deps)

    def has_dynamic_fan_in_dep(self, node_input: NodeInput) -> bool:
        check.inst_param(node_input, "node_input", NodeInput)
        if node_input not in self._input_to_output_map:
            return False
        dep_type, _ = self._input_to_output_map[node_input]
        return dep_type == DependencyType.DYNAMIC_COLLECT

    def get_dynamic_fan_in_dep(self, node_input: NodeInput) -> NodeOutput:
        check.inst_param(node_input, "node_input", NodeInput)
        dep_type, dep = self._input_to_output_map[node_input]
        check.invariant(
            dep_type == DependencyType.DYNAMIC_COLLECT,
            f"Cannot call get_dynamic_fan_in_dep when dep is not, got {dep_type}",
        )
        return cast(NodeOutput, dep)

    def has_deps(self, node_input: NodeInput) -> bool:
        check.inst_param(node_input, "node_input", NodeInput)
        return node_input in self._input_to_output_map

    def get_deps_list(self, node_input: NodeInput) -> Sequence[NodeOutput]:
        check.inst_param(node_input, "node_input", NodeInput)
        check.invariant(self.has_deps(node_input))
        dep_type, handle_or_list = self._input_to_output_map[node_input]
        if dep_type == DependencyType.DIRECT:
            return [cast(NodeOutput, handle_or_list)]
        elif dep_type == DependencyType.DYNAMIC_COLLECT:
            return [cast(NodeOutput, handle_or_list)]
        elif dep_type == DependencyType.FAN_IN:
            return [handle for handle in handle_or_list if isinstance(handle, NodeOutput)]
        else:
            check.failed(f"Unexpected dep type {dep_type}")

    def inputs(self) -> Sequence[NodeInput]:
        return list(self._input_to_output_map.keys())

    def get_upstream_dynamic_output_for_node(self, node_name: str) -> Optional[NodeOutput]:
        return self._dynamic_fan_out_index.get(node_name)

    def get_dependency_type(self, node_input: NodeInput) -> Optional[DependencyType]:
        result = self._input_to_output_map.get(node_input)
        if result is None:
            return None
        dep_type, _ = result
        return dep_type

    def is_dynamic_mapped(self, node_name: str) -> bool:
        return node_name in self._dynamic_fan_out_index

    def has_dynamic_downstreams(self, node_name: str) -> bool:
        for node_output in self._dynamic_fan_out_index.values():
            if node_output.node_name == node_name:
                return True

        return False

import inspect
from collections.abc import Mapping
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, TypeVar, Union

import dagster._check as check
from dagster._annotations import PublicAttr, deprecated_param, superseded
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.inference import InferredInputProps
from dagster._core.definitions.metadata import (
    ArbitraryMetadataMapping,
    MetadataValue,
    RawMetadataValue,
    normalize_metadata,
)
from dagster._core.definitions.utils import NoValueSentinel, check_valid_name
from dagster._core.errors import DagsterError, DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import (  # BuiltinScalarDagsterType,
    DagsterType,
    resolve_dagster_type,
)

if TYPE_CHECKING:
    from dagster._core.execution.context.input import InputContext

T = TypeVar("T")


# unfortunately since type_check functions need TypeCheckContext which is only available
# at runtime, we can only check basic types before runtime
def _check_default_value(input_name: str, dagster_type: DagsterType, default_value: T) -> T:
    from dagster._core.types.dagster_type import BuiltinScalarDagsterType

    if default_value is not NoValueSentinel:
        if dagster_type.is_nothing:
            raise DagsterInvalidDefinitionError(
                "Setting a default_value is invalid on InputDefinitions of type Nothing"
            )

        if isinstance(dagster_type, BuiltinScalarDagsterType):
            type_check = dagster_type.type_check_scalar_value(default_value)
            if not type_check.success:
                raise DagsterInvalidDefinitionError(
                    "Type check failed for the default_value of InputDefinition "
                    f"{input_name} of type {dagster_type.display_name}. "
                    f"Received value {default_value} of type {type(default_value)}",
                )

    return default_value  # type: ignore  # (pyright bug)


@superseded(additional_warn_text="Use `In` instead", emit_runtime_warning=False)
class InputDefinition:
    """Defines an argument to an op's compute function.

    Inputs may flow from previous op outputs, or be stubbed using config. They may optionally
    be typed using the Dagster type system.

    Args:
        name (str): Name of the input.
        dagster_type (Optional[Union[Type, DagsterType]]]): The type of this input.
            Users should provide the Python type of the objects that they expect to be passed for
            this input, or a :py:class:`DagsterType` that defines a runtime check that they want
            to be run on this input. Defaults to :py:class:`Any`.
        description (Optional[str]): Human-readable description of the input.
        default_value (Optional[Any]): The default value to use if no input is provided.
        metadata (Optional[Dict[str, Any]]): A dict of metadata for the input.
        asset_key (Optional[Union[AssetKey, InputContext -> AssetKey]]): An AssetKey
            (or function that produces an AssetKey from the InputContext) which should be associated
            with this InputDefinition. Used for tracking lineage information through Dagster.
        asset_partitions (Optional[Union[AbstractSet[str], InputContext -> AbstractSet[str]]]): A
            set of partitions of the given asset_key (or a function that produces this list of
            partitions from the InputContext) which should be associated with this InputDefinition.
        input_manager_key (Optional[str]): The resource key for the
            :py:class:`InputManager` used for loading this input when it is not connected to an
            upstream output.
    """

    _name: str
    _type_not_set: bool
    _dagster_type: DagsterType
    _description: Optional[str]
    _default_value: Any
    _input_manager_key: Optional[str]
    _raw_metadata: ArbitraryMetadataMapping
    _metadata: Mapping[str, MetadataValue]
    _asset_key: Optional[Union[AssetKey, Callable[["InputContext"], AssetKey]]]
    _asset_partitions_fn: Optional[Callable[["InputContext"], set[str]]]

    def __init__(
        self,
        name: str,
        dagster_type: object = None,
        description: Optional[str] = None,
        default_value: object = NoValueSentinel,
        metadata: Optional[ArbitraryMetadataMapping] = None,
        asset_key: Optional[Union[AssetKey, Callable[["InputContext"], AssetKey]]] = None,
        asset_partitions: Optional[Union[set[str], Callable[["InputContext"], set[str]]]] = None,
        input_manager_key: Optional[str] = None,
        # when adding new params, make sure to update combine_with_inferred and with_dagster_type below
    ):
        self._name = check_valid_name(name, allow_list=["config"])

        self._type_not_set = dagster_type is None
        self._dagster_type = resolve_dagster_type(dagster_type)

        self._description = check.opt_str_param(description, "description")

        self._default_value = _check_default_value(self._name, self._dagster_type, default_value)

        self._input_manager_key = check.opt_str_param(input_manager_key, "input_manager_key")

        self._raw_metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        self._metadata = normalize_metadata(self._raw_metadata, allow_invalid=True)

        if not callable(asset_key):
            check.opt_inst_param(asset_key, "asset_key", AssetKey)

        self._asset_key = asset_key

        if asset_partitions:
            check.param_invariant(
                asset_key is not None,
                "asset_partitions",
                'Cannot specify "asset_partitions" argument without also specifying "asset_key"',
            )
        if callable(asset_partitions):
            self._asset_partitions_fn = asset_partitions
        elif asset_partitions is not None:
            _asset_partitions = check.set_param(asset_partitions, "asset_partitions", of_type=str)
            self._asset_partitions_fn = lambda _: _asset_partitions
        else:
            self._asset_partitions_fn = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def dagster_type(self) -> DagsterType:
        return self._dagster_type

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def has_default_value(self) -> bool:
        return self._default_value is not NoValueSentinel

    @property
    def default_value(self) -> Any:
        check.invariant(self.has_default_value, "Can only fetch default_value if has_default_value")
        return self._default_value

    @property
    def input_manager_key(self) -> Optional[str]:
        return self._input_manager_key

    @property
    def metadata(self) -> ArbitraryMetadataMapping:
        return self._raw_metadata

    @property
    def is_asset(self) -> bool:
        return self._asset_key is not None

    @property
    def hardcoded_asset_key(self) -> Optional[AssetKey]:
        if not callable(self._asset_key):
            return self._asset_key
        else:
            return None

    def get_asset_key(self, context: "InputContext") -> Optional[AssetKey]:
        """Get the AssetKey associated with this InputDefinition for the given
        :py:class:`InputContext` (if any).

        Args:
            context (InputContext): The InputContext that this InputDefinition is being evaluated
                in
        """
        if callable(self._asset_key):
            return self._asset_key(context)
        else:
            return self.hardcoded_asset_key

    def get_asset_partitions(self, context: "InputContext") -> Optional[set[str]]:
        """Get the set of partitions that this op will read from this InputDefinition for the given
        :py:class:`InputContext` (if any).

        Args:
            context (InputContext): The InputContext that this InputDefinition is being evaluated
                in
        """
        if self._asset_partitions_fn is None:
            return None

        return self._asset_partitions_fn(context)

    def mapping_to(
        self, node_name: str, input_name: str, fan_in_index: Optional[int] = None
    ) -> "InputMapping":
        """Create an input mapping to an input of a child node.

        In a GraphDefinition, you can use this helper function to construct
        an :py:class:`InputMapping` to the input of a child node.

        Args:
            node_name (str): The name of the child node to which to map this input.
            input_name (str): The name of the child node' input to which to map this input.
            fan_in_index (Optional[int]): The index in to a fanned in input, else None

        Examples:
            .. code-block:: python

                input_mapping = InputDefinition('composite_input', Int).mapping_to(
                    'child_node', 'int_input'
                )
        """
        check.str_param(node_name, "node_name")
        check.str_param(input_name, "input_name")
        check.opt_int_param(fan_in_index, "fan_in_index")

        return InputMapping(
            graph_input_name=self.name,
            mapped_node_name=node_name,
            mapped_node_input_name=input_name,
            fan_in_index=fan_in_index,
            graph_input_description=self.description,
            dagster_type=self.dagster_type,
        )

    @staticmethod
    def create_from_inferred(inferred: InferredInputProps) -> "InputDefinition":
        return InputDefinition(
            name=inferred.name,
            dagster_type=_checked_inferred_type(inferred),
            description=inferred.description,
            default_value=inferred.default_value,
        )

    def combine_with_inferred(self, inferred: InferredInputProps) -> "InputDefinition":
        """Return a new InputDefinition that merges this ones properties with those inferred from type signature.
        This can update: dagster_type, description, and default_value if they are not set.
        """
        check.invariant(
            self.name == inferred.name,
            f"InferredInputProps name {inferred.name} did not align with InputDefinition name"
            f" {self.name}",
        )

        dagster_type = self._dagster_type
        if self._type_not_set:
            dagster_type = _checked_inferred_type(inferred)

        description = self._description
        if description is None and inferred.description is not None:
            description = inferred.description

        default_value = self._default_value
        if not self.has_default_value:
            default_value = inferred.default_value

        return InputDefinition(
            name=self.name,
            dagster_type=dagster_type,
            description=description,
            default_value=default_value,
            metadata=self.metadata,
            asset_key=self._asset_key,
            asset_partitions=self._asset_partitions_fn,
            input_manager_key=self._input_manager_key,
        )

    def with_dagster_type(self, dagster_type: DagsterType) -> "InputDefinition":
        return InputDefinition(
            name=self.name,
            dagster_type=dagster_type,
            description=self.description,
            default_value=self.default_value if self.has_default_value else NoValueSentinel,
            metadata=self.metadata,
            asset_key=self._asset_key,
            asset_partitions=self._asset_partitions_fn,
            input_manager_key=self._input_manager_key,
        )


def _checked_inferred_type(inferred: InferredInputProps) -> DagsterType:
    try:
        if inferred.annotation == inspect.Parameter.empty:
            resolved_type = resolve_dagster_type(None)
        elif inferred.annotation is None:
            # When inferred.annotation is None, it means someone explicitly put "None" as the
            # annotation, so want to map it to a DagsterType that checks for the None type
            resolved_type = resolve_dagster_type(type(None))
        else:
            resolved_type = resolve_dagster_type(inferred.annotation)

    except DagsterError as e:
        raise DagsterInvalidDefinitionError(
            f"Problem using type '{inferred.annotation}' from type annotation for argument "
            f"'{inferred.name}', correct the issue or explicitly set the dagster_type "
            "via In()."
        ) from e

    return resolved_type


class InputPointer(NamedTuple("_InputPointer", [("node_name", str), ("input_name", str)])):
    def __new__(cls, node_name: str, input_name: str):
        return super().__new__(
            cls,
            check.str_param(node_name, "node_name"),
            check.str_param(input_name, "input_name"),
        )


class FanInInputPointer(
    NamedTuple(
        "_FanInInputPointer", [("node_name", str), ("input_name", str), ("fan_in_index", int)]
    )
):
    def __new__(cls, node_name: str, input_name: str, fan_in_index: int):
        return super().__new__(
            cls,
            check.str_param(node_name, "node_name"),
            check.str_param(input_name, "input_name"),
            check.int_param(fan_in_index, "fan_in_index"),
        )


@deprecated_param(
    param="dagster_type",
    breaking_version="2.0",
    additional_warn_text="Any defined `dagster_type` should come from the upstream op `Output`.",
    # Disabling warning here since we're passing this internally and I'm not sure whether it is
    # actually used or discarded.
    emit_runtime_warning=False,
)
class InputMapping(NamedTuple):
    """Defines an input mapping for a graph.

    Args:
        graph_input_name (str): Name of the input in the graph being mapped from.
        mapped_node_name (str): Named of the node (op/graph) that the input is being mapped to.
        mapped_node_input_name (str): Name of the input in the node (op/graph) that is being mapped to.
        fan_in_index (Optional[int]): The index in to a fanned input, otherwise None.
        graph_input_description (Optional[str]): A description of the input in the graph being mapped from.
        dagster_type (Optional[DagsterType]): The dagster type of the graph's input
            being mapped from.

    Examples:
        .. code-block:: python

            from dagster import InputMapping, GraphDefinition, op, graph

            @op
            def needs_input(x):
                return x + 1

            # The following two graph definitions are equivalent
            GraphDefinition(
                name="the_graph",
                node_defs=[needs_input],
                input_mappings=[
                    InputMapping(
                        graph_input_name="maps_x", mapped_node_name="needs_input",
                        mapped_node_input_name="x"
                    )
                ]
            )

            @graph
            def the_graph(maps_x):
                needs_input(maps_x)
    """

    graph_input_name: str
    mapped_node_name: str
    mapped_node_input_name: str
    fan_in_index: Optional[int] = None
    graph_input_description: Optional[str] = None
    dagster_type: Optional[DagsterType] = None

    @property
    def maps_to(self) -> Union[InputPointer, FanInInputPointer]:
        if self.fan_in_index is not None:
            return FanInInputPointer(
                self.mapped_node_name, self.mapped_node_input_name, self.fan_in_index
            )
        return InputPointer(self.mapped_node_name, self.mapped_node_input_name)

    @property
    def maps_to_fan_in(self) -> bool:
        return isinstance(self.maps_to, FanInInputPointer)

    def describe(self) -> str:
        idx = self.maps_to.fan_in_index if isinstance(self.maps_to, FanInInputPointer) else ""
        return f"{self.graph_input_name} -> {self.maps_to.node_name}:{self.maps_to.input_name}{idx}"

    def get_definition(self) -> "InputDefinition":
        return InputDefinition(
            name=self.graph_input_name,
            description=self.graph_input_description,
            dagster_type=self.dagster_type,
        )


class In(
    NamedTuple(
        "_In",
        [
            ("dagster_type", PublicAttr[Union[DagsterType, type[NoValueSentinel]]]),
            ("description", PublicAttr[Optional[str]]),
            ("default_value", PublicAttr[Any]),
            ("metadata", PublicAttr[Optional[Mapping[str, Any]]]),
            (
                "asset_key",
                PublicAttr[Optional[Union[AssetKey, Callable[["InputContext"], AssetKey]]]],
            ),
            (
                "asset_partitions",
                PublicAttr[Optional[Union[set[str], Callable[["InputContext"], set[str]]]]],
            ),
            ("input_manager_key", PublicAttr[Optional[str]]),
        ],
    )
):
    """Defines an argument to an op's compute function.

    Inputs may flow from previous op's outputs, or be stubbed using config. They may optionally
    be typed using the Dagster type system.

    Args:
        dagster_type (Optional[Union[Type, DagsterType]]]):
            The type of this input. Should only be set if the correct type can not
            be inferred directly from the type signature of the decorated function.
        description (Optional[str]): Human-readable description of the input.
        default_value (Optional[Any]): The default value to use if no input is provided.
        metadata (Optional[Dict[str, RawMetadataValue]]): A dict of metadata for the input.
        asset_key (Optional[Union[AssetKey, InputContext -> AssetKey]]): An AssetKey
            (or function that produces an AssetKey from the InputContext) which should be associated
            with this In. Used for tracking lineage information through Dagster.
        asset_partitions (Optional[Union[Set[str], InputContext -> Set[str]]]): A
            set of partitions of the given asset_key (or a function that produces this list of
            partitions from the InputContext) which should be associated with this In.
        input_manager_key (Optional[str]): The resource key for the
            :py:class:`InputManager` used for loading this input when it is not connected to an
            upstream output.
    """

    def __new__(
        cls,
        dagster_type: Union[type, DagsterType] = NoValueSentinel,
        description: Optional[str] = None,
        default_value: Any = NoValueSentinel,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        asset_key: Optional[Union[AssetKey, Callable[["InputContext"], AssetKey]]] = None,
        asset_partitions: Optional[Union[set[str], Callable[["InputContext"], set[str]]]] = None,
        input_manager_key: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            dagster_type=(
                NoValueSentinel
                if dagster_type is NoValueSentinel
                else resolve_dagster_type(dagster_type)
            ),
            description=check.opt_str_param(description, "description"),
            default_value=default_value,
            metadata=check.opt_mapping_param(metadata, "metadata", key_type=str),
            asset_key=check.opt_inst_param(asset_key, "asset_key", (AssetKey, FunctionType)),
            asset_partitions=asset_partitions,
            input_manager_key=check.opt_str_param(input_manager_key, "input_manager_key"),
        )

    @staticmethod
    def from_definition(input_def: InputDefinition) -> "In":
        return In(
            dagster_type=input_def.dagster_type,
            description=input_def.description,
            default_value=input_def._default_value,  # noqa: SLF001
            metadata=input_def.metadata,
            asset_key=input_def._asset_key,  # noqa: SLF001
            asset_partitions=input_def._asset_partitions_fn,  # noqa: SLF001
            input_manager_key=input_def.input_manager_key,
        )

    def to_definition(self, name: str) -> InputDefinition:
        dagster_type = self.dagster_type if self.dagster_type is not NoValueSentinel else None
        return InputDefinition(
            name=name,
            dagster_type=dagster_type,
            description=self.description,
            default_value=self.default_value,
            metadata=self.metadata,
            asset_key=self.asset_key,
            asset_partitions=self.asset_partitions,
            input_manager_key=self.input_manager_key,
        )


class GraphIn(NamedTuple("_GraphIn", [("description", PublicAttr[Optional[str]])])):
    """Represents information about an input that a graph maps.

    Args:
        description (Optional[str]): Human-readable description of the input.
    """

    def __new__(cls, description: Optional[str] = None):
        return super().__new__(cls, description=description)

    def to_definition(self, name: str) -> InputDefinition:
        return InputDefinition(name=name, description=self.description)

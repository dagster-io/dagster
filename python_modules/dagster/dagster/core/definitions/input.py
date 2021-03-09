from collections import namedtuple
from typing import Optional, Set

from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import (
    BuiltinScalarDagsterType,
    DagsterType,
    resolve_dagster_type,
)
from dagster.utils.backcompat import experimental_arg_warning

from .utils import check_valid_name


class _NoValueSentinel:
    pass


# unfortunately since type_check functions need TypeCheckContext which is only available
# at runtime, we can only check basic types before runtime
def _check_default_value(input_name, dagster_type, default_value):
    if default_value is not _NoValueSentinel:
        if dagster_type.is_nothing:
            raise DagsterInvalidDefinitionError(
                "Setting a default_value is invalid on InputDefinitions of type Nothing"
            )

        if isinstance(dagster_type, BuiltinScalarDagsterType):
            type_check = dagster_type.type_check_scalar_value(default_value)
            if not type_check.success:
                raise DagsterInvalidDefinitionError(
                    (
                        "Type check failed for the default_value of InputDefinition "
                        "{input_name} of type {dagster_type}. "
                        "Received value {value} of type {type}"
                    ).format(
                        input_name=input_name,
                        dagster_type=dagster_type.display_name,
                        value=default_value,
                        type=type(default_value),
                    ),
                )

    return default_value


class InputDefinition:
    """Defines an argument to a solid's compute function.

    Inputs may flow from previous solids' outputs, or be stubbed using config. They may optionally
    be typed using the Dagster type system.

    Args:
        name (str): Name of the input.
        dagster_type (Optional[Any]):  The type of this input. Users should provide one of the
            :ref:`built-in types <builtin>`, a dagster type explicitly constructed with
            :py:func:`as_dagster_type`, :py:func:`@usable_as_dagster_type <dagster_type`, or
            :py:func:`PythonObjectDagsterType`, or a Python type. Defaults to :py:class:`Any`.
        description (Optional[str]): Human-readable description of the input.
        default_value (Optional[Any]): The default value to use if no input is provided.
        root_manager_key (Optional[str]): (Experimental) The resource key for the
            :py:class:`RootInputManager` used for loading this input when it is not connected to an
            upstream output.
        metadata (Optional[Dict[str, Any]]): (Experimental) A dict of metadata for the input.
        asset_key (Optional[Union[AssetKey, InputContext -> AssetKey]]): (Experimental) An AssetKey
            (or function that produces an AssetKey from the InputContext) which should be associated
            with this InputDefinition. Used for tracking lineage information through Dagster.
        asset_partitions (Optional[Union[Set[str], InputContext -> Set[str]]]): (Experimental) A
            set of partitions of the given asset_key (or a function that produces this list of
            partitions from the InputContext) which should be associated with this InputDefinition.
    """

    def __init__(
        self,
        name,
        dagster_type=None,
        description=None,
        default_value=_NoValueSentinel,
        root_manager_key=None,
        metadata=None,
        asset_key=None,
        asset_partitions=None,
    ):
        self._name = check_valid_name(name)

        self._dagster_type = check.inst(resolve_dagster_type(dagster_type), DagsterType)

        self._description = check.opt_str_param(description, "description")

        self._default_value = _check_default_value(self._name, self._dagster_type, default_value)

        if root_manager_key:
            experimental_arg_warning("root_manager_key", "InputDefinition.__init__")

        self._root_manager_key = check.opt_str_param(root_manager_key, "root_manager_key")

        if metadata:
            experimental_arg_warning("metadata", "InputDefinition.__init__")

        self._metadata = check.opt_dict_param(metadata, "metadata", key_type=str)

        if asset_key:
            experimental_arg_warning("asset_key", "InputDefinition.__init__")

        self._is_asset = asset_key is not None

        if callable(asset_key):
            self._asset_key_fn = asset_key
        else:
            asset_key = check.opt_inst_param(asset_key, "asset_key", AssetKey)
            self._asset_key_fn = lambda _: asset_key

        if asset_partitions:
            experimental_arg_warning("asset_partitions", "InputDefinition.__init__")
            check.param_invariant(
                asset_key is not None,
                "asset_partitions",
                'Cannot specify "asset_partitions" argument without also specifying "asset_key"',
            )
        if callable(asset_partitions):
            self._asset_partitions_fn = asset_partitions
        else:
            asset_partitions = check.opt_set_param(asset_partitions, "asset_partitions", str)
            self._asset_partitions_fn = lambda _: asset_partitions

    @property
    def name(self):
        return self._name

    @property
    def dagster_type(self):
        return self._dagster_type

    @property
    def description(self):
        return self._description

    @property
    def has_default_value(self):
        return self._default_value is not _NoValueSentinel

    @property
    def default_value(self):
        check.invariant(self.has_default_value, "Can only fetch default_value if has_default_value")
        return self._default_value

    @property
    def root_manager_key(self):
        return self._root_manager_key

    @property
    def metadata(self):
        return self._metadata

    @property
    def is_asset(self):
        return self._is_asset

    def get_asset_key(self, context) -> Optional[AssetKey]:
        """Get the AssetKey associated with this InputDefinition for the given
        :py:class:`InputContext` (if any).

        Args:
            context (InputContext): The InputContext that this OutputDefinition is being evaluated
                in
        """
        return self._asset_key_fn(context)

    def get_asset_partitions(self, context) -> Optional[Set[str]]:
        """Get the set of partitions that this solid will read from this InputDefinition for the given
        :py:class:`InputContext` (if any).

        Args:
            context (InputContext): The InputContext that this InputDefinition is being evaluated
                in
        """
        return self._asset_partitions_fn(context)

    def mapping_to(self, solid_name, input_name, fan_in_index=None):
        """Create an input mapping to an input of a child solid.

        In a CompositeSolidDefinition, you can use this helper function to construct
        an :py:class:`InputMapping` to the input of a child solid.

        Args:
            solid_name (str): The name of the child solid to which to map this input.
            input_name (str): The name of the child solid' input to which to map this input.
            fan_in_index (Optional[int]): The index in to a fanned in input, else None

        Examples:

            .. code-block:: python

                input_mapping = InputDefinition('composite_input', Int).mapping_to(
                    'child_solid', 'int_input'
                )
        """
        check.str_param(solid_name, "solid_name")
        check.str_param(input_name, "input_name")
        check.opt_int_param(fan_in_index, "fan_in_index")

        if fan_in_index is not None:
            maps_to = FanInInputPointer(solid_name, input_name, fan_in_index)
        else:
            maps_to = InputPointer(solid_name, input_name)
        return InputMapping(self, maps_to)


class InputPointer(namedtuple("_InputPointer", "solid_name input_name")):
    def __new__(cls, solid_name, input_name):
        return super(InputPointer, cls).__new__(
            cls,
            check.str_param(solid_name, "solid_name"),
            check.str_param(input_name, "input_name"),
        )


class FanInInputPointer(namedtuple("_FanInInputPointer", "solid_name input_name fan_in_index")):
    def __new__(cls, solid_name, input_name, fan_in_index):
        return super(FanInInputPointer, cls).__new__(
            cls,
            check.str_param(solid_name, "solid_name"),
            check.str_param(input_name, "input_name"),
            check.int_param(fan_in_index, "fan_in_index"),
        )


class InputMapping(namedtuple("_InputMapping", "definition maps_to")):
    """Defines an input mapping for a composite solid.

    Args:
        definition (InputDefinition): Defines the input to the composite solid.
        solid_name (str): The name of the child solid onto which to map the input.
        input_name (str): The name of the input to the child solid onto which to map the input.
    """

    def __new__(cls, definition, maps_to):
        return super(InputMapping, cls).__new__(
            cls,
            check.inst_param(definition, "definition", InputDefinition),
            check.inst_param(maps_to, "maps_to", (InputPointer, FanInInputPointer)),
        )

    @property
    def maps_to_fan_in(self):
        return isinstance(self.maps_to, FanInInputPointer)

from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import (
    BuiltinScalarDagsterType,
    DagsterType,
    resolve_dagster_type,
)

from .utils import check_valid_name


class _NoValueSentinel(object):
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
                        dagster_type=dagster_type.name,
                        value=default_value,
                        type=type(default_value),
                    ),
                )

    return default_value


class InputDefinition(object):
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
    """

    def __init__(self, name, dagster_type=None, description=None, default_value=_NoValueSentinel):
        ""
        self._name = check_valid_name(name)

        self._dagster_type = check.inst(resolve_dagster_type(dagster_type), DagsterType)

        self._description = check.opt_str_param(description, "description")

        self._default_value = _check_default_value(self._name, self._dagster_type, default_value)

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

    def mapping_to(self, solid_name, input_name):
        """Create an input mapping to an input of a child solid.

        In a CompositeSolidDefinition, you can use this helper function to construct
        an :py:class:`InputMapping` to the input of a child solid.

        Args:
            solid_name (str): The name of the child solid to which to map this input.
            input_name (str): The name of the child solid' input to which to map this input.

        Examples:

            .. code-block:: python

                input_mapping = InputDefinition('composite_input', Int).mapping_to(
                    'child_solid', 'int_input'
                )
        """
        return InputMapping(self, solid_name, input_name)


class InputMapping(namedtuple("_InputMapping", "definition solid_name input_name")):
    """Defines an input mapping for a composite solid.

    Args:
        definition (InputDefinition): Defines the input to the composite solid.
        solid_name (str): The name of the child solid onto which to map the input.
        input_name (str): The name of the input to the child solid onto which to map the input.
    """

    def __new__(cls, definition, solid_name, input_name):
        return super(InputMapping, cls).__new__(
            cls,
            check.inst_param(definition, "definition", InputDefinition),
            check.str_param(solid_name, "solid_name"),
            check.str_param(input_name, "input_name"),
        )

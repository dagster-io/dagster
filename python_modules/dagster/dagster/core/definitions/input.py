from collections import namedtuple

from dagster import check
from dagster.core.types.dagster_type import DagsterType, resolve_dagster_type

from .utils import check_valid_name


class InputDefinition(object):
    '''Defines an argument to a solid's compute function.
    
    Inputs may flow from previous solids' outputs, or be stubbed using config. They may optionally
    be typed using the Dagster type system.

    Args:
        name (str): Name of the input.
        dagster_type (Optional[Any]):  The type of this input. Users should provide one of the
            :ref:`built-in types <builtin>`, a dagster type explicitly constructed with
            :py:func:`as_dagster_type`, :py:func:`@usable_as_dagster_type <dagster_type`, or
            :py:func:`PythonObjectDagsterType`, or a Python type. Defaults to :py:class:`Any`.
        description (Optional[str]): Human-readable description of the input.
    '''

    def __init__(self, name, dagster_type=None, description=None):
        ''
        self._name = check_valid_name(name)

        self._runtime_type = check.inst(resolve_dagster_type(dagster_type), DagsterType)

        self._description = check.opt_str_param(description, 'description')

    @property
    def name(self):
        return self._name

    @property
    def runtime_type(self):
        return self._runtime_type

    @property
    def description(self):
        return self._description

    def mapping_to(self, solid_name, input_name):
        '''Create an input mapping to an input of a child solid.

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
        '''
        return InputMapping(self, solid_name, input_name)


class InputMapping(namedtuple('_InputMapping', 'definition solid_name input_name')):
    '''Defines an input mapping for a composite solid.

    Args:
        definition (InputDefinition): Defines the input to the composite solid.
        solid_name (str): The name of the child solid onto which to map the input.
        input_name (str): The name of the input to the child solid onto which to map the input.
    '''

    def __new__(cls, definition, solid_name, input_name):
        return super(InputMapping, cls).__new__(
            cls,
            check.inst_param(definition, 'definition', InputDefinition),
            check.str_param(solid_name, 'solid_name'),
            check.str_param(input_name, 'input_name'),
        )

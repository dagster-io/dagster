from collections import namedtuple

from dagster import check
from dagster.core.types.dagster_type import resolve_dagster_type

from .utils import DEFAULT_OUTPUT, check_valid_name


class OutputDefinition(object):
    '''Defines an output from a solid's compute function.
    
    Solids can have multiple outputs, in which case outputs cannot be anonymous.
    
    Many solids have only one output, in which case the user can provide a single output definition
    that will be given the default name, "result".

    Output definitions may be typed using the Dagster type system.

    Args:
        dagster_type (Optional[Any]): The type of this output. Users should provide one of the
            :ref:`built-in types <builtin>`, a dagster type explicitly constructed with
            :py:func:`as_dagster_type`, :py:func:`@usable_as_dagster_type <dagster_type`, or
            :py:func:`PythonObjectDagsterType`, or a Python type. Defaults to :py:class:`Any`. 
        name (Optional[str]): Name of the output. (default: "result")
        description (Optional[str]): Human-readable description of the output.
        is_optional (Optional[bool]): Set if this output is optional. (default: False)
    '''

    def __init__(self, dagster_type=None, name=None, description=None, is_optional=False):
        self._name = check_valid_name(check.opt_str_param(name, 'name', DEFAULT_OUTPUT))
        self._runtime_type = resolve_dagster_type(dagster_type)
        self._description = check.opt_str_param(description, 'description')
        self._optional = check.bool_param(is_optional, 'is_optional')

    @property
    def name(self):
        return self._name

    @property
    def runtime_type(self):
        return self._runtime_type

    @property
    def description(self):
        return self._description

    @property
    def optional(self):
        return self._optional

    def mapping_from(self, solid_name, output_name=None):
        '''Create an output mapping from an output of a child solid.

        In a CompositeSolidDefinition, you can use this helper function to construct
        an :py:class:`OutputMapping` from the output of a child solid.

        Args:
            solid_name (str): The name of the child solid from which to map this output.
            input_name (str): The name of the child solid's output from which to map this output.

        Examples:

            .. code-block:: python

                output_mapping = OutputDefinition(Int).mapping_from('child_solid')
        '''
        return OutputMapping(self, solid_name, output_name)


class OutputMapping(namedtuple('_OutputMapping', 'definition solid_name output_name')):
    '''Defines an output mapping for a composite solid.

    Args:
        definition (OutputDefinition): Defines the output of the composite solid.
        solid_name (str): The name of the child solid from which to map the output.
        output_name (str): The name of the child solid's output from which to map the output.
    '''

    def __new__(cls, definition, solid_name, output_name=None):
        return super(OutputMapping, cls).__new__(
            cls,
            check.inst_param(definition, 'definition', OutputDefinition),
            check.str_param(solid_name, 'solid_name'),
            check.opt_str_param(output_name, 'output_name', DEFAULT_OUTPUT),
        )

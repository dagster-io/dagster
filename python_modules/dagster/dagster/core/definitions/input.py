from collections import namedtuple
from dagster import check

from dagster.core.types.runtime import RuntimeType, resolve_to_runtime_type

from .utils import check_valid_name


class InputDefinition(object):
    '''An InputDefinition instance represents an argument to a compute function defined within
    a solid. Inputs are values within the dagster type system that are created from previous
    solids.

    Args:
        name (str): Name of the input.
        dagster_type (DagsterType):
            Type of the input. Defaults to :py:class:`Any` . Basic python types will be
            mapped to the appropriate DagsterType.
        description (str): Description of the input. Optional.
    '''

    def __init__(self, name, dagster_type=None, description=None):
        ''
        self._name = check_valid_name(name)

        self._runtime_type = check.inst(resolve_to_runtime_type(dagster_type), RuntimeType)

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

    @property
    def descriptive_key(self):
        return 'output'

    def mapping_to(self, solid_name, input_name):
        return InputMapping(self, solid_name, input_name)


class InputMapping(namedtuple('_InputMapping', 'definition solid_name input_name')):
    def __new__(cls, definition, solid_name, input_name):
        return super(InputMapping, cls).__new__(
            cls,
            check.inst_param(definition, 'definition', InputDefinition),
            check.str_param(solid_name, 'solid_name'),
            check.str_param(input_name, 'input_name'),
        )

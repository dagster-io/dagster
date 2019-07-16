from collections import namedtuple
from dagster import check
from dagster.core.types.runtime import RuntimeType, resolve_to_runtime_type

from .utils import check_valid_name, DEFAULT_OUTPUT


class OutputDefinition(object):
    '''An OutputDefinition represents an output from a solid. Solids can have multiple
    outputs. In those cases the outputs must be named. Frequently solids have only one
    output, and so the user can construct a single OutputDefinition that will have
    the default name of "result".

    Args:
        dagster_type (DagsterType):
            Type of the output. Defaults to :py:class:`Any` . Basic python types will be
            mapped to the appropriate DagsterType.
        name (Optional[str]): Name of the output. Defaults to "result".
        expectations List[IOExpectationDefinition]:
            **Deprecated**: Expectations for this output.

            Prefer yielding :py:class:`ExpectationResult` directly from solid compute function.
        description (str): Description of the output. Optional.
        is_optional (bool): If this output is optional. Optional, defaults to false.
    '''

    def __init__(self, dagster_type=None, name=None, description=None, is_optional=False):
        self._name = check_valid_name(check.opt_str_param(name, 'name', DEFAULT_OUTPUT))

        self._runtime_type = check.inst(resolve_to_runtime_type(dagster_type), RuntimeType)

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

    @property
    def descriptive_key(self):
        return 'output'

    def mapping_from(self, solid_name, output_name=None):
        return OutputMapping(self, solid_name, output_name)


class OutputMapping(namedtuple('_OutputMapping', 'definition solid_name output_name')):
    def __new__(cls, definition, solid_name, output_name=None):
        return super(OutputMapping, cls).__new__(
            cls,
            check.inst_param(definition, 'definition', OutputDefinition),
            check.str_param(solid_name, 'solid_name'),
            check.opt_str_param(output_name, 'output_name', DEFAULT_OUTPUT),
        )

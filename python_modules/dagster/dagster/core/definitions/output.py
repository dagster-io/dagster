from dagster import check
from dagster.core.types.runtime import RuntimeType, resolve_to_runtime_type

from .expectation import ExpectationDefinition
from .utils import check_valid_name, DEFAULT_OUTPUT


class OutputDefinition(object):
    '''An OutputDefinition represents an output from a solid. Solids can have multiple
    outputs. In those cases the outputs must be named. Frequently solids have only one
    output, and so the user can construct a single OutputDefinition that will have
    the default name of "result".

    Attributes:
        runtime_type (DagsterType): Type of the output. Defaults to types.Any.
        name (str): Name of the output. Defaults to "result".
        expectations List[ExpectationDefinition]: Expectations for this output.
        description (str): Description of the output. Optional.
        is_optional (bool): If this output is optional. Optional, defaults to false.
    '''

    def __init__(
        self, dagster_type=None, name=None, expectations=None, description=None, is_optional=False
    ):
        self.name = check_valid_name(check.opt_str_param(name, 'name', DEFAULT_OUTPUT))

        self.runtime_type = check.inst(resolve_to_runtime_type(dagster_type), RuntimeType)

        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.description = check.opt_str_param(description, 'description')

        self.optional = check.bool_param(is_optional, 'is_optional')

    @property
    def descriptive_key(self):
        return 'output'

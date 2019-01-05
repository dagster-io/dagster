from dagster import check

from dagster.core import types
from .expectation import ExpectationDefinition
from .utils import check_valid_name, DEFAULT_OUTPUT


class OutputDefinition(object):
    '''An OutputDefinition represents an output from a solid. Solids can have multiple
    outputs. In those cases the outputs must be named. Frequently solids have only one
    output, and so the user can construct a single OutputDefinition that will have
    the default name of "result".

    Attributes:
        dagster_type (DagsterType): Type of the output. Defaults to types.Any.
        name (str): Name of the output. Defaults to "result".
        expectations List[ExpectationDefinition]: Expectations for this output.
        description (str): Description of the output. Optional.
    '''

    def __init__(self, dagster_type=None, name=None, expectations=None, description=None):
        self.name = check_valid_name(check.opt_str_param(name, 'name', DEFAULT_OUTPUT))

        self.dagster_type = check.opt_inst_param(
            dagster_type, 'dagster_type', types.DagsterType, types.Any
        )

        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.description = check.opt_str_param(description, 'description')

    @property
    def descriptive_key(self):
        return 'output'

from collections import namedtuple

from dagster import check

from ..config import ConfigType


class TraversalContext(namedtuple('_TraversalContext', 'config_type config_value stack errors')):
    def __new__(cls, config_type, config_value, stack, errors):
        from .stack import EvaluationStack
        from .errors import EvaluationError

        return super(TraversalContext, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            config_value,  # arbitrary value, can't check
            check.inst_param(stack, 'stack', EvaluationStack),
            check.list_param(errors, 'errors', of_type=EvaluationError),
        )

    def add_error(self, error):
        from .errors import EvaluationError

        check.inst_param(error, 'error', EvaluationError)
        self.errors.append(error)

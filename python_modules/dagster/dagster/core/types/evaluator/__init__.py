from collections import namedtuple

import six

from dagster import check
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.utils import single_item, make_readonly_value

from ..config import ConfigType
from ..type_printer import print_config_type_to_string

from .errors import (
    create_field_not_defined_error,
    create_fields_not_defined_error,
    create_missing_required_field_error,
    create_missing_required_fields_error,
    DagsterEvaluationErrorReason,
    EvaluationError,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
)
from .stack import get_friendly_path_msg, get_friendly_path_info, EvaluationStack
from .traversal_context import TraversalContext
from .evaluation import evaluate_config


class EvaluateValueResult(namedtuple('_EvaluateValueResult', 'success value errors')):
    def __new__(cls, success, value, errors):
        return super(EvaluateValueResult, cls).__new__(
            cls,
            check.bool_param(success, 'success'),
            value,
            check.list_param(errors, 'errors', of_type=EvaluationError),
        )

    def errors_at_level(self, *levels):
        return list(self._iterate_errors_at_level(list(levels)))

    def _iterate_errors_at_level(self, levels):
        check.list_param(levels, 'levels', of_type=str)
        for error in self.errors:
            if error.stack.levels == levels:
                yield error


def evaluate_config_value(config_type, config_value, pipeline=None):
    check.inst_param(config_type, 'config_type', ConfigType)
    check.opt_inst_param(pipeline, 'pipeline', PipelineDefinition)

    errors, value = evaluate_config(config_type, config_value, pipeline)

    if errors:
        return EvaluateValueResult(success=False, value=None, errors=errors)

    return EvaluateValueResult(success=True, value=make_readonly_value(value), errors=[])

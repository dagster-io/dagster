from collections import namedtuple

from dagster import check
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.types.field_utils import FieldImpl

from ..config import ConfigType


class TraversalContext(
    namedtuple('_TraversalContext', 'config_type config_value stack errors pipeline seen_handles')
):
    def __new__(cls, config_type, config_value, stack, errors, pipeline, seen_handles=None):
        from .stack import EvaluationStack
        from .errors import EvaluationError

        return super(TraversalContext, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            config_value,  # arbitrary value, can't check
            check.inst_param(stack, 'stack', EvaluationStack),
            check.list_param(errors, 'errors', of_type=EvaluationError),
            check.opt_inst_param(pipeline, 'pipeline', PipelineDefinition),
            check.opt_set_param(seen_handles, 'seen_handles'),
        )

    def add_error(self, error):
        from .errors import EvaluationError

        check.inst_param(error, 'error', EvaluationError)
        self.errors.append(error)

    def for_list(self, index, item):
        check.int_param(index, 'index')

        return TraversalContext(
            self.config_type.inner_type,
            item,
            self.stack.for_list_index(index),
            self.errors,
            self.pipeline,
            self.seen_handles,
        )

    def for_field(self, field_def, key, value):
        check.inst_param(field_def, 'field_def', FieldImpl)
        check.str_param(key, 'key')

        return TraversalContext(
            field_def.config_type,
            value,
            self.stack.for_field(key, field_def),
            self.errors,
            self.pipeline,
            self.seen_handles,
        )

    def for_nullable_inner_type(self):
        return TraversalContext(
            self.config_type.inner_type,
            self.config_value,
            self.stack,
            self.errors,
            self.pipeline,
            self.seen_handles,
        )

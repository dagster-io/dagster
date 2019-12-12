from collections import namedtuple

from dagster import check
from dagster.core.types.config.field import Field

from ..config_type import ConfigType


class TraversalContext(namedtuple('_TraversalContext', 'config_type config_value stack')):
    def __new__(cls, config_type, config_value, stack):
        from .stack import EvaluationStack

        return super(TraversalContext, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            config_value,  # arbitrary value, can't check
            check.inst_param(stack, 'stack', EvaluationStack),
        )

    def for_list(self, index, item):
        check.int_param(index, 'index')
        return self._replace(
            config_type=self.config_type.inner_type,
            config_value=item,
            stack=self.stack.for_list_index(index),
        )

    def for_field(self, field_def, key, value):
        check.inst_param(field_def, 'field_def', Field)
        check.str_param(key, 'key')
        return self._replace(
            config_type=field_def.config_type,
            config_value=value,
            stack=self.stack.for_field(key, field_def),
        )

    def for_nullable_inner_type(self):
        return self._replace(config_type=self.config_type.inner_type)

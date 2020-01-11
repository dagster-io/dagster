from collections import namedtuple

from dagster import check
from dagster.config.config_type import ConfigType
from dagster.config.field import Field

from .stack import EvaluationStack


class ValidationContext(namedtuple('_ValidationContext', 'config_type stack')):
    def __new__(cls, config_type, stack):
        return super(ValidationContext, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            check.inst_param(stack, 'stack', EvaluationStack),
        )

    def for_array(self, index):
        check.int_param(index, 'index')
        return ValidationContext(
            config_type=self.config_type.inner_type, stack=self.stack.for_array_index(index),
        )

    def for_field(self, field_def, key):
        check.inst_param(field_def, 'field_def', Field)
        check.str_param(key, 'key')
        return ValidationContext(
            config_type=field_def.config_type, stack=self.stack.for_field(key, field_def),
        )

    def for_nullable_inner_type(self):
        return self._replace(config_type=self.config_type.inner_type)

    def for_new_config_type(self, config_type):
        return ValidationContext(
            config_type=config_type, stack=self.stack.for_new_type(config_type)
        )

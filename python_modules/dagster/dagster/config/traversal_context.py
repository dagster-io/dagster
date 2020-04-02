from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.config.config_type import ConfigType
from dagster.config.field import Field

from .stack import EvaluationStack


class TraversalType(Enum):
    VALIDATE = 'VALIDATE'
    RESOLVE_DEFAULTS = 'RESOLVE_DEFAULTS'
    RESOLVE_DEFAULTS_AND_POSTPROCESS = 'RESOLVE_DEFAULTS_AND_POSTPROCESS'


class TraversalContext(namedtuple('_TraversalContext', 'config_type stack traversal_type')):
    def __new__(cls, config_type, stack, traversal_type):
        return super(TraversalContext, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            check.inst_param(stack, 'stack', EvaluationStack),
            check.inst_param(traversal_type, 'traversal_type', TraversalType),
        )

    @property
    def do_post_process(self):
        return self.traversal_type == TraversalType.RESOLVE_DEFAULTS_AND_POSTPROCESS

    def for_array(self, index):
        check.int_param(index, 'index')
        return TraversalContext(
            config_type=self.config_type.inner_type,
            stack=self.stack.for_array_index(index),
            traversal_type=self.traversal_type,
        )

    def for_field(self, field_def, key):
        check.inst_param(field_def, 'field_def', Field)
        check.str_param(key, 'key')
        return TraversalContext(
            config_type=field_def.config_type,
            stack=self.stack.for_field(key, field_def),
            traversal_type=self.traversal_type,
        )

    def for_nullable_inner_type(self):
        return self._replace(config_type=self.config_type.inner_type)

    def for_new_config_type(self, config_type):
        return TraversalContext(
            config_type=config_type,
            stack=self.stack.for_new_type(config_type),
            traversal_type=self.traversal_type,
        )

from collections import namedtuple

from dagster import check
from dagster.core.definitions.environment_configs import is_solid_container_config
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.execution.config import RunConfig
from dagster.core.types.field_utils import FieldImpl

from ..config import ConfigType


class TraversalContext(
    namedtuple(
        '_TraversalContext', 'config_type config_value stack pipeline run_config seen_handles'
    )
):
    def __new__(
        cls, config_type, config_value, stack, pipeline, run_config=None, seen_handles=None
    ):
        from .stack import EvaluationStack

        return super(TraversalContext, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            config_value,  # arbitrary value, can't check
            check.inst_param(stack, 'stack', EvaluationStack),
            check.opt_inst_param(pipeline, 'pipeline', PipelineDefinition),
            check.opt_inst_param(run_config, 'run_config', RunConfig),
            check.opt_list_param(seen_handles, 'seen_handles'),
        )

    def for_list(self, index, item):
        check.int_param(index, 'index')
        return self._replace(
            config_type=self.config_type.inner_type,
            config_value=item,
            stack=self.stack.for_list_index(index),
        )

    def for_field(self, field_def, key, value):
        check.inst_param(field_def, 'field_def', FieldImpl)
        check.str_param(key, 'key')
        return self._replace(
            config_type=field_def.config_type,
            config_value=value,
            stack=self.stack.for_field(key, field_def),
        )

    def for_nullable_inner_type(self):
        return self._replace(config_type=self.config_type.inner_type)

    def for_mapped_composite_config(self, handle, mapped_config_value):
        return self._replace(
            config_type=self.config_type.child_solids_config_field.config_type,
            config_value=mapped_config_value,
            seen_handles=self.seen_handles + [handle],
        )

    def new_context_with_handle(self, handle):
        check.invariant(
            is_solid_container_config(self.config_type),
            'Not a solid container config schema; this is intended to create a new context for a '
            'solid container',
        )
        return self._replace(seen_handles=self.seen_handles + [handle])

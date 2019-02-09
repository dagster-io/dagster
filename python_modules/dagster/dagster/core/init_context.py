from collections import namedtuple

import warnings

from dagster import check

from .definitions.pipeline import PipelineDefinition


class InitContext(namedtuple('_InitContext', 'context_config pipeline_def run_id')):
    def __new__(cls, context_config, pipeline_def, run_id):
        return super(InitContext, cls).__new__(
            cls,
            context_config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            check.str_param(run_id, 'run_id'),
        )

    @property
    def config(self):
        warnings.warn('As of 3.0.2 the config property is deprecated. Use context_config instead.')
        return self.context_config


class InitResourceContext(
    namedtuple('InitResourceContext', 'context_config resource_config pipeline_def run_id')
):
    def __new__(cls, context_config, resource_config, pipeline_def, run_id):
        return super(InitResourceContext, cls).__new__(
            cls,
            context_config,
            resource_config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            check.str_param(run_id, 'run_id'),
        )

    @property
    def config(self):
        warnings.warn('As of 3.0.2 the config property is deprecated. Use resource_config instead.')
        return self.resource_config

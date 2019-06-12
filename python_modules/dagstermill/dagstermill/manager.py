import os
import pickle
import uuid

from contextlib import contextmanager

import scrapbook

from dagster import (
    check,
    ExecutionTargetHandle,
    ModeDefinition,
    PipelineDefinition,
    RunConfig,
    SolidDefinition,
)
from dagster.core.execution.api import scoped_pipeline_context
from dagster.core.execution.context_creation_pipeline import ResourcesStack
from dagster.core.definitions.dependency import SolidHandle
from dagster.loggers import colored_console_logger

from .context import DagstermillInPipelineExecutionContext
from .errors import DagstermillError
from .logger import construct_sqlite_logger
from .serialize import PICKLE_PROTOCOL, write_value


class Manager:
    def __init__(self):
        self.handle = None
        self.pipeline_def = None
        self.solid_def = None
        self.in_pipeline = False
        self.marshal_dir = None
        self.context = None
        self.resources_stack = None

    @contextmanager
    def _setup_resources(self, pipeline_def, environment_config, run_config, log_manager):
        '''This context manager is a drop-in replacement for
        dagster.core.execution.context_creation_pipeline.create_resources. It uses the Manager's
        instance of ResourceStack to create resources, but does not tear them down when the
        context manager returns -- teardown must be managed manually using Manager.teardown().
        '''

        # pylint: disable=protected-access
        self.resources_stack = ResourcesStack(
            pipeline_def, environment_config, run_config, log_manager
        )
        yield self.resources_stack.create()

    def reconstitute_pipeline_context(
        self,
        output_log_path=None,
        marshal_dir=None,
        environment_dict=None,
        handle=None,
        run_config=None,
        solid_handle=None,
    ):
        '''Reconstitutes a context for dagstermill-managed execution.
        
        This function is called to reconstruct a pipeline context within the injected parameters cell
        of a dagstermill notebook. Users should not call this function interactively except when
        debugging output notebooks.
        
        Use dagstermill.get_context in the ``parameters`` cell of your notebook when defining a
        context for interactive exploration and development.
        '''
        check.opt_str_param(output_log_path, 'output_log_path')
        check.opt_str_param(marshal_dir, 'marshal_dir')
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
        check.inst_param(run_config, 'run_config', RunConfig)
        check.inst_param(handle, 'handle', ExecutionTargetHandle)
        check.inst_param(solid_handle, 'solid_handle', SolidHandle)

        pipeline_def = check.inst_param(
            handle.entrypoint.perform_load(),
            'pipeline_def (from handle {handle_dict})'.format(handle_dict=handle.data._asdict()),
            PipelineDefinition,
        )

        solid_def = pipeline_def.get_solid(solid_handle)

        mode_def = pipeline_def.get_mode_definition(run_config.mode)
        shim_mode_def = ModeDefinition(
            name=mode_def.name,
            logger_defs=dict(
                mode_def.loggers, dagstermill=construct_sqlite_logger(output_log_path)
            ),
            resource_defs=mode_def.resource_defs,
        )
        pipeline_def.mode_definitions = [shim_mode_def]

        if 'loggers' not in environment_dict:
            environment_dict['loggers'] = {'dagstermill': {}}

        if 'dagstermill' not in environment_dict['loggers']:
            environment_dict['loggers']['dagstermill'] = {}

        self.marshal_dir = marshal_dir
        self.in_pipeline = True
        self.solid_def = solid_def
        self.pipeline_def = pipeline_def

        with scoped_pipeline_context(
            self.pipeline_def,
            environment_dict,
            run_config,
            scoped_resources_builder_cm=self._setup_resources,
        ) as pipeline_context:
            self.context = DagstermillInPipelineExecutionContext(pipeline_context)

        return self.context

    def get_context(self, solid_def=None, mode_def=None, environment_dict=None):
        check.opt_inst_param(solid_def, 'solid_def', SolidDefinition)
        check.opt_inst_param(mode_def, 'mode_def', ModeDefinition)
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)

        if solid_def is None:
            solid_def = SolidDefinition(
                name='this_solid',
                input_defs=[],
                compute_fn=lambda *args, **kwargs: None,
                output_defs=[],
                description='Ephemeral solid constructed by dagstermill.get_context()',
            )

        if not mode_def:
            mode_def = ModeDefinition(logger_defs={'dagstermill': colored_console_logger})
            environment_dict['loggers'] = {'dagstermill': {}}

        pipeline_def = PipelineDefinition(
            [solid_def], mode_defs=[mode_def], name='ephemeral_dagstermill_pipeline'
        )

        run_config = RunConfig(mode=mode_def.name)

        self.in_pipeline = False
        self.solid_def = solid_def
        self.pipeline_def = pipeline_def

        with scoped_pipeline_context(
            self.pipeline_def,
            environment_dict,
            run_config,
            scoped_resources_builder_cm=self._setup_resources,
        ) as pipeline_context:
            self.context = DagstermillInPipelineExecutionContext(pipeline_context)

        return self.context

    def yield_result(self, value, output_name='result'):
        if not self.in_pipeline:
            return value

        if not self.solid_def.has_output(output_name):
            raise DagstermillError(
                'Solid {solid_name} does not have output named {output_name}'.format(
                    solid_name=self.solid_def.name, output_name=output_name
                )
            )

        runtime_type = self.solid_def.output_def_named(output_name).runtime_type

        out_file = os.path.join(self.marshal_dir, 'output-{}'.format(output_name))
        scrapbook.glue(output_name, write_value(runtime_type, value, out_file))

    def yield_event(self, dagster_event):
        if not self.in_pipeline:
            return dagster_event

        event_id = 'event-{event_uuid}'.format(event_uuid=str(uuid.uuid4()))
        out_file_path = os.path.join(self.marshal_dir, event_id)
        with open(out_file_path, 'wb') as fd:
            fd.write(pickle.dumps(dagster_event, PICKLE_PROTOCOL))

        scrapbook.glue(event_id, out_file_path)

    def teardown_resources(self):
        if self.resources_stack is not None:
            self.resources_stack.teardown()


MANAGER_FOR_NOTEBOOK_INSTANCE = Manager()

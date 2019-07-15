import os
import pickle
import uuid

from contextlib import contextmanager

from dagster import (
    check,
    ExecutionTargetHandle,
    ExpectationResult,
    Failure,
    Materialization,
    ModeDefinition,
    PipelineDefinition,
    RunConfig,
    SolidDefinition,
    TypeCheck,
)
from dagster.core.execution.api import scoped_pipeline_context
from dagster.core.execution.context_creation_pipeline import ResourcesStack
from dagster.core.definitions.dependency import SolidHandle
from dagster.loggers import colored_console_logger

from .context import DagstermillExecutionContext
from .errors import DagstermillError
from .logger import construct_sqlite_logger
from .serialize import PICKLE_PROTOCOL, read_value, write_value


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

        You'll see this function called to reconstruct a pipeline context within the ``injected
        parameters`` cell of a dagstermill output notebook. Users should not call this function
        interactively except when debugging output notebooks.

        Use :func:`dagstermill.get_context` in the ``parameters`` cell of your notebook to define a
        context for interactive exploration and development. This call will be replaced by one to
        :func:`dagstermill.reconstitute_pipeline_context` when the notebook is executed by
        dagstermill.
        '''
        check.opt_str_param(output_log_path, 'output_log_path')
        check.opt_str_param(marshal_dir, 'marshal_dir')
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
        check.inst_param(run_config, 'run_config', RunConfig)
        check.inst_param(handle, 'handle', ExecutionTargetHandle)
        check.inst_param(solid_handle, 'solid_handle', SolidHandle)

        pipeline_def = check.inst_param(
            handle.build_pipeline_definition(),
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

        pipeline_def = PipelineDefinition(
            pipeline_def.solid_defs,
            name=pipeline_def.name,
            description=pipeline_def.description,
            dependencies=pipeline_def.dependencies,
            mode_defs=[shim_mode_def],
            preset_defs=pipeline_def.preset_defs,
        )

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
            self.context = DagstermillExecutionContext(pipeline_context)

        return self.context

    def get_context(self, solid_config=None, mode_def=None, environment_dict=None):
        '''Get a dagstermill execution context for interactive exploration and development.

        Args:
            solid_config (Optional[Any]): If specified, this value will be made available on the
                context as its ``solid_config`` property.
            mode_def (Optional[:class:`dagster.ModeDefinition`]): If specified, defines the mode to
                use to construct the context. Specify this if you would like a context constructed
                with specific ``resource_defs`` or ``logger_defs``. By default, an ephemeral mode
                with a console logger will be constructed.
            environment_dict(Optional[dict]): The environment config dict with which to construct
                the context.

        Returns:
            :class:`dagstermill.DagstermillExecutionContext`
        '''
        check.opt_inst_param(mode_def, 'mode_def', ModeDefinition)
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)

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
            self.context = DagstermillExecutionContext(pipeline_context, solid_config)

        return self.context

    def yield_result(self, value, output_name='result'):
        '''Yield a result directly from notebook code.

        When called interactively or in development, returns its input.

        Args:
            value (Any): The value to yield.
            output_name (Optional[str]): The name of the result to yield (default: ``'result'``).
        '''
        if not self.in_pipeline:
            return value

        # deferred import for perf
        import scrapbook

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
        '''Yield a dagster event directly from notebook code.

        When called interactively or in development, returns its input.

        Args:
            dagster_event (Union[:class:`dagster.Materialization`, :class:`dagster.ExpectationResult`, :class:`dagster.TypeCheck`, :class:`dagster.Failure`]):
                An event to yield back to Dagster.
        '''
        check.inst_param(
            dagster_event, 'dagster_event', (Materialization, ExpectationResult, TypeCheck, Failure)
        )

        if not self.in_pipeline:
            return dagster_event

        # deferred import for perf
        import scrapbook

        event_id = 'event-{event_uuid}'.format(event_uuid=str(uuid.uuid4()))
        out_file_path = os.path.join(self.marshal_dir, event_id)
        with open(out_file_path, 'wb') as fd:
            fd.write(pickle.dumps(dagster_event, PICKLE_PROTOCOL))

        scrapbook.glue(event_id, out_file_path)

    def teardown_resources(self):
        if self.resources_stack is not None:
            self.resources_stack.teardown()

    def load_parameter(self, input_name, input_value):
        input_def = self.solid_def.input_def_named(input_name)
        return read_value(input_def.runtime_type, input_value)


MANAGER_FOR_NOTEBOOK_INSTANCE = Manager()

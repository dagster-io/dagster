import os
import pickle
import uuid
import warnings

from contextlib import contextmanager

import scrapbook

from dagster import check, ModeDefinition, PipelineDefinition, RunConfig
from dagster.core.execution.api import scoped_pipeline_context
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.core.execution.context_creation_pipeline import ResourcesStack
from dagster.core.types.marshal import PickleSerializationStrategy

from .context import DagstermillInNotebookExecutionContext
from .errors import DagstermillError
from .logger import construct_logger
from .serialize import (
    dict_to_enum,
    is_json_serializable,
    PICKLE_PROTOCOL,
    SerializableRuntimeType,
    write_value,
)


class Manager:
    def __init__(self):
        self.repository_def = None
        self.populated_by_papermill = False
        self.pipeline_def = None
        self.solid_def = None
        self.marshal_dir = None
        self.context = None
        self.input_name_type_dict = None
        self.output_name_type_dict = None
        self.solid_def_name = None
        self.resources_stack = None

    def register_repository(self, repository_def):
        self.repository_def = repository_def

    def deregister_repository(self):
        # This function is intended to support test cases, and should not be invoked
        # from user notebooks.
        self.repository_def = None

    @contextmanager
    def setup_resources(self, pipeline_def, environment_config, run_config, log_manager):
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

    def define_out_of_pipeline_context(self, config=None):
        '''Defines a context to be used in a notebook (i.e., not in pipeline execution).

        '''
        config = check.opt_dict_param(config, 'config')
        pipeline_def = PipelineDefinition([], name='Ephemeral Notebook Pipeline')

        if config.keys():
            warnings.warn(
                'Config keys will not be respected for in-notebook '
                'execution: [{keys}]'.format(
                    keys=', '.join(['\'{key}\''.format(key=key) for key in config.keys()])
                )
            )

            config = {}

        run_config = RunConfig()

        with scoped_pipeline_context(
            pipeline_def, config, run_config, scoped_resources_builder_cm=self.setup_resources
        ) as pipeline_context:
            self.context = DagstermillInNotebookExecutionContext(
                pipeline_context, out_of_pipeline=True
            )

        if self.context.resources:  # pylint: disable=protected-access
            warnings.warn(
                'Call dagstermill.teardown() to finalize resources attached to the context.'
            )
        return self.context

    def yield_result(self, value, output_name='result'):
        if not self.populated_by_papermill:
            return value

        if self.solid_def is None:
            if output_name not in self.output_name_type_dict:
                raise DagstermillError(
                    'Solid {solid_name} does not have output named {output_name}'.format(
                        solid_name=self.solid_def_name, output_name=output_name
                    )
                )
            runtime_type_enum = self.output_name_type_dict[output_name]
            if runtime_type_enum == SerializableRuntimeType.SCALAR:
                scrapbook.glue(output_name, value)
            elif runtime_type_enum == SerializableRuntimeType.ANY and is_json_serializable(value):
                scrapbook.glue(output_name, value)
            elif runtime_type_enum == SerializableRuntimeType.PICKLE_SERIALIZABLE:
                out_file = os.path.join(self.marshal_dir, 'output-{}'.format(output_name))
                PickleSerializationStrategy().serialize_to_file(value, out_file)
                scrapbook.glue(output_name, out_file)
            else:
                raise DagstermillError(
                    # Discuss this in the docs and improve error message
                    # https://github.com/dagster-io/dagster/issues/1275
                    # https://github.com/dagster-io/dagster/issues/1276
                    'Output Definition for output {output_name} requires repo registration '
                    'since it has a complex serialization format'.format(output_name=output_name)
                )
        else:
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
        if not self.populated_by_papermill:
            return dagster_event

        event_id = 'event-{event_uuid}'.format(event_uuid=str(uuid.uuid4()))
        out_file_path = os.path.join(self.marshal_dir, event_id)
        with open(out_file_path, 'wb') as fd:
            fd.write(pickle.dumps(dagster_event, PICKLE_PROTOCOL))

        scrapbook.glue(event_id, out_file_path)

    def populate_context(
        self,
        run_id=None,
        mode=None,
        solid_def_name=None,
        pipeline_name=None,
        marshal_dir=None,
        environment_config=None,
        input_name_type_dict=None,
        output_name_type_dict=None,
        output_log_path=None,
        **_kwargs
    ):
        check.str_param(run_id, 'run_id')
        check.str_param(mode, 'mode')
        check.str_param(solid_def_name, 'solid_def_name')
        check.str_param(pipeline_name, 'pipeline_name')
        check.str_param(marshal_dir, 'marshal_dir')
        check.dict_param(environment_config, 'environment_config')
        check.dict_param(input_name_type_dict, 'input_name_type_dict')
        check.dict_param(output_name_type_dict, 'output_name_type_dict')
        check.str_param(output_log_path, 'output_log_path')

        self.populated_by_papermill = True
        self.solid_def_name = solid_def_name
        self.marshal_dir = marshal_dir

        logger_def = construct_logger(output_log_path)
        loggers = {'dagstermill': logger_def}

        if self.repository_def is None:
            self.solid_def = None
            self.pipeline_def = PipelineDefinition(
                [],
                mode_defs=[ModeDefinition(logger_defs=loggers)],
                name='Dummy Pipeline (No Repo Registration)',
            )
            self.input_name_type_dict = dict_to_enum(input_name_type_dict)
            self.output_name_type_dict = dict_to_enum(output_name_type_dict)
            for _, runtime_type_enum in self.input_name_type_dict.items():
                if runtime_type_enum == SerializableRuntimeType.NONE:
                    raise DagstermillError(
                        'If Dagstermill solids have inputs that require serialization strategies '
                        'that are not pickling, then you must register a repository within '
                        'notebook by calling dagstermill.register_repository(repository_def)'
                    )
            for _, runtime_type_enum in self.output_name_type_dict.items():
                if runtime_type_enum == SerializableRuntimeType.NONE:
                    raise DagstermillError(
                        'If Dagstermill solids have outputs that require serialization strategies '
                        'that are not pickling, then you must register a repository within '
                        'notebook by calling dagstermill.register_repository(repository_def).'
                    )
            environment_config = {'loggers': {'dagstermill': {}}}
            run_config = RunConfig(run_id=run_id, mode=mode)

        else:
            self.pipeline_def = self.repository_def.get_pipeline(pipeline_name)
            check.invariant(
                self.pipeline_def.has_solid_def(solid_def_name),
                'solid {} not found'.format(solid_def_name),
            )
            self.solid_def = self.pipeline_def.solid_def_named(solid_def_name)

            logger = logger_def.logger_fn(
                InitLoggerContext({}, self.pipeline_def, logger_def, run_id)
            )

            run_config = RunConfig(run_id, loggers=[logger], mode=mode)

        with scoped_pipeline_context(
            self.pipeline_def,
            environment_config,
            run_config,
            scoped_resources_builder_cm=self.setup_resources,
        ) as pipeline_context:
            self.context = DagstermillInNotebookExecutionContext(pipeline_context)

        return self.context

    def teardown_resources(self):
        if self.resources_stack is not None:
            self.resources_stack.teardown()


MANAGER_FOR_NOTEBOOK_INSTANCE = Manager()

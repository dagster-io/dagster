import multiprocessing
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple

import six

from dagster import check
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.serdes import whitelist_for_serdes
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts

EXECUTION_TIME_KEY = 'execution_epoch_time'


class IRunConfig(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''
    Interface for a container for RunConfig-like (e.g. RunConfig and PipelineRun) properties.
    Implementation should be left to the respective `namedtuple` superclass.
    '''

    @abstractproperty
    def run_id(self):
        pass

    @abstractproperty
    def tags(self):
        pass

    @abstractproperty
    def reexecution_config(self):
        pass

    @abstractproperty
    def step_keys_to_execute(self):
        pass

    @abstractproperty
    def mode(self):
        pass

    @abstractproperty
    def previous_run_id(self):
        pass


class RunConfig(
    namedtuple(
        '_RunConfig', 'run_id tags reexecution_config step_keys_to_execute mode previous_run_id'
    ),
    IRunConfig,
):
    '''Configuration for pipeline execution.

    Args:
        run_id (Optional[str]): The ID to use for this run. If not provided a new UUID will
            be created (using :py:func:`python:uuid4.uuid4`).
        tags (Optional[dict[str, str]]): Key value pairs that will be added to logs.
        rexecution_config (Optional[RexecutionConfig]): Information about a previous run to allow
            for subset rexecution.
        step_keys_to_execute (Optional[list[str]]): The subset of steps from a pipeline to execute
            this run.
        mode (Optional[str]): The name of the mode in which to execute the pipeline.
    '''

    def __new__(
        cls,
        run_id=None,
        tags=None,
        reexecution_config=None,
        step_keys_to_execute=None,
        mode=None,
        previous_run_id=None,
    ):

        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        tags = check.opt_dict_param(tags, 'tags', key_type=str)

        if EXECUTION_TIME_KEY in tags:
            # execution_epoch_time expected to be able to be cast to float
            # can be passed in as a string from airflow integration
            tags[EXECUTION_TIME_KEY] = float(tags[EXECUTION_TIME_KEY])

        return super(RunConfig, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id') if run_id else make_new_run_id(),
            tags=tags,
            reexecution_config=check.opt_inst_param(
                reexecution_config, 'reexecution_config', ReexecutionConfig
            ),
            step_keys_to_execute=step_keys_to_execute,
            mode=check.opt_str_param(mode, 'mode'),
            previous_run_id=check.opt_str_param(previous_run_id, 'previous_run_id'),
        )

    def with_tags(self, **new_tags):
        '''Extend an existing RunConfig with additional logging tags.

        Args:
            **new_tags: Values should be strings. The logging tags to add.

        Returns:
            RunConfig: The extended RunConfig.
        '''
        new_tags = merge_dicts(self.tags, new_tags)
        return RunConfig(**merge_dicts(self._asdict(), {'tags': new_tags}))

    def with_mode(self, mode):
        '''Extend an existing RunConfig with a different mode.

        Args:
            mode (str): The new mode to use.

        Returns:
            RunConfig: The extended RunConfig.
        '''
        return RunConfig(**merge_dicts(self._asdict(), {'mode': mode}))

    def with_step_keys_to_execute(self, step_keys_to_execute):
        '''Extend an existing run config with different step keys to execute.

        Args:
            step_keys_to_execute (List[str]): The step keys to execute.

        Returns:
            RunConfig: The extended RunConfig.
        '''
        return RunConfig(
            **merge_dicts(self._asdict(), {'step_keys_to_execute': step_keys_to_execute})
        )


class ExecutorConfig(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def check_requirements(self, instance, system_storage_def):
        '''Check whether this executor config is valid given the instance and system storage.

        Args:
            instance (DagsterInstance): The available Dagster instance.
            system_storage_def (SystemStorageDefinition): The available system storage.

        Raises if the executor config is not valid.
        '''

    @abstractmethod
    def get_engine(self):
        '''(Engine): Return the corresponding engine class.'''


class InProcessExecutorConfig(ExecutorConfig):
    def check_requirements(self, _instance, _system_storage_def):
        pass

    def get_engine(self):
        from dagster.core.engine.engine_inprocess import InProcessEngine

        return InProcessEngine


class MultiprocessExecutorConfig(ExecutorConfig):
    def __init__(self, handle, max_concurrent=None):
        from dagster import ExecutionTargetHandle

        # TODO: These gnomic process boundary/execution target handle exceptions should link to
        # a fuller explanation in the docs.
        # https://github.com/dagster-io/dagster/issues/1649
        self._handle = check.inst_param(
            handle,
            'handle',
            ExecutionTargetHandle,
            additional_message='Multiprocessing can only be configured when a pipeline is executed '
            'from an ExecutionTargetHandle: do not pass a pure in-memory pipeline definition.',
        )

        max_concurrent = max_concurrent if max_concurrent else multiprocessing.cpu_count()
        self.max_concurrent = check.int_param(max_concurrent, 'max_concurrent')

    def check_requirements(self, instance, system_storage_def):
        check_persistent_storage_requirement(system_storage_def)
        check_non_ephemeral_instance(instance)

    def load_pipeline(self, pipeline_run):
        from dagster.core.storage.pipeline_run import PipelineRun

        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        return self._handle.build_pipeline_definition().build_sub_pipeline(
            pipeline_run.selector.solid_subset
        )

    def get_engine(self):
        from dagster.core.engine.engine_multiprocess import MultiprocessEngine

        return MultiprocessEngine


@whitelist_for_serdes
class ReexecutionConfig(namedtuple('_ReexecutionConfig', 'previous_run_id step_output_handles')):
    pass


def check_persistent_storage_requirement(system_storage_def):
    if not system_storage_def.is_persistent:
        raise DagsterUnmetExecutorRequirementsError(
            (
                'You have attempted use a multi process executor while using system '
                'storage {storage_name} which does not persist intermediates. '
                'This means there would be no way to move data between different '
                'processes. Please configure your pipeline in the storage config '
                'section to use persistent system storage such as the filesystem.'
            ).format(storage_name=system_storage_def.name)
        )


def check_non_ephemeral_instance(instance):
    if instance.is_ephemeral:
        raise DagsterUnmetExecutorRequirementsError(
            'You have attempted to use a multi process executor with an ephemeral DagsterInstance. '
            'A non-ephermal instance is needed to coordinate execution between multiple processes. '
            'You can configure your default instance via $DAGSTER_HOME or ensure a valid one is '
            'passed when invoking the python APIs.'
        )

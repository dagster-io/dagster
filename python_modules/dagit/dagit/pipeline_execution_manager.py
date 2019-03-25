from __future__ import absolute_import
from collections import namedtuple
import copy
import os
import sys
import time

import gevent
import six

from dagster import (
    InProcessExecutorConfig,
    PipelineDefinition,
    RunConfig,
    RunStorageMode,
    check,
    execute_pipeline,
)
from dagster.core.events import PipelineEventRecord, EventType
from dagster.utils.error import serializable_error_info_from_exc_info, SerializableErrorInfo
from dagster.utils.logging import level_from_string
from dagster.utils import get_multiprocessing_context

from .pipeline_run_storage import PipelineRun


class PipelineExecutionManager(object):
    def execute_pipeline(self, repository_container, pipeline, pipeline_run, throw_on_user_error):
        raise NotImplementedError()


def build_synthetic_pipeline_error_record(run_id, error_info, pipeline_name):
    return PipelineEventRecord(
        message=error_info.message,
        user_message=error_info.message,
        level=level_from_string('ERROR'),
        event_type=EventType.PIPELINE_FAILURE,
        run_id=run_id,
        timestamp=time.time(),
        error_info=error_info,
        pipeline_name=pipeline_name,
    )


def build_process_start_event(run_id, pipeline_name):
    message = 'About to start process for pipeline {pipeline_name} run_id {run_id}'.format(
        pipeline_name=pipeline_name, run_id=run_id
    )

    return PipelineEventRecord(
        message=message,
        user_message=message,
        level=level_from_string('INFO'),
        event_type=EventType.PIPELINE_PROCESS_START,
        run_id=run_id,
        timestamp=time.time(),
        error_info=None,
        pipeline_name=pipeline_name,
    )


def build_process_started_event(run_id, pipeline_name, process_id):
    message = 'Started process {process_id} for pipeline {pipeline_name} run_id {run_id}'.format(
        pipeline_name=pipeline_name, run_id=run_id, process_id=process_id
    )

    return PipelineProcessStartedEvent(
        message=message,
        user_message=message,
        level=level_from_string('INFO'),
        event_type=EventType.PIPELINE_PROCESS_STARTED,
        run_id=run_id,
        timestamp=time.time(),
        error_info=None,
        pipeline_name=pipeline_name,
        process_id=process_id,
    )


class PipelineProcessStartedEvent(PipelineEventRecord):
    def __init__(self, process_id, **kwargs):
        super(PipelineProcessStartedEvent, self).__init__(**kwargs)
        self._process_id = check.int_param(process_id, 'process_id')

    @property
    def process_id(self):
        return self._process_id


DAGIT_DEFAULT_STORAGE_MODE = RunStorageMode.FILESYSTEM


def get_storage_mode(environment_dict):
    return None if 'storage' in environment_dict else DAGIT_DEFAULT_STORAGE_MODE


class SynchronousExecutionManager(PipelineExecutionManager):
    def execute_pipeline(self, repository_container, pipeline, pipeline_run, throw_on_user_error):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        try:

            return execute_pipeline(
                pipeline,
                pipeline_run.config,
                run_config=RunConfig(
                    pipeline_run.run_id,
                    event_callback=pipeline_run.handle_new_event,
                    executor_config=InProcessExecutorConfig(
                        throw_on_user_error=throw_on_user_error
                    ),
                    reexecution_config=pipeline_run.reexecution_config,
                    step_keys_to_execute=pipeline_run.step_keys_to_execute,
                    storage_mode=get_storage_mode(pipeline_run.config),
                ),
            )
        except:  # pylint: disable=W0702
            if throw_on_user_error:
                six.reraise(*sys.exc_info())

            pipeline_run.handle_new_event(
                build_synthetic_pipeline_error_record(
                    pipeline_run.run_id,
                    serializable_error_info_from_exc_info(sys.exc_info()),
                    pipeline.name,
                )
            )


class MultiprocessingDone(object):
    pass


class MultiprocessingError(object):
    def __init__(self, error_info):
        self.error_info = check.inst_param(error_info, 'error_info', SerializableErrorInfo)


class ProcessStartedSentinel(object):
    def __init__(self, process_id):
        self.process_id = check.int_param(process_id, 'process_id')


class MultiprocessingExecutionManager(PipelineExecutionManager):
    def __init__(self):
        self._multiprocessing_context = get_multiprocessing_context()
        self._processes_lock = self._multiprocessing_context.Lock()
        self._processes = []
        # This is actually a reverse semaphore. We keep track of number of
        # processes we have by releasing semaphore every time we start
        # processing, we release after processing is finished
        self._processing_semaphore = gevent.lock.Semaphore(0)

        gevent.spawn(self._start_polling)

    def _start_polling(self):
        while True:
            self._poll()
            gevent.sleep(0.1)

    def _poll(self):
        with self._processes_lock:
            processes = copy.copy(self._processes)
            self._processes = []
            for process in processes:
                self._processing_semaphore.release()

        for process in processes:
            done = self._consume_process_queue(process)
            if not done and not process.process.is_alive():
                done = self._consume_process_queue(process)
                if not done:
                    try:
                        done = True
                        raise Exception(
                            'Pipeline execution process for {run_id} unexpectedly exited'.format(
                                run_id=process.pipeline_run.run_id
                            )
                        )
                    except:  # pylint: disable=W0702
                        process.pipeline_run.handle_new_event(
                            build_synthetic_pipeline_error_record(
                                process.pipeline_run.run_id,
                                serializable_error_info_from_exc_info(sys.exc_info()),
                                process.pipeline_run.pipeline_name,
                            )
                        )

            if not done:
                with self._processes_lock:
                    self._processes.append(process)

            with self._processes_lock:
                self._processing_semaphore.acquire()

    def _consume_process_queue(self, process):
        while not process.message_queue.empty():
            message = process.message_queue.get(False)

            if isinstance(message, MultiprocessingDone):
                return True
            elif isinstance(message, MultiprocessingError):
                process.pipeline_run.handle_new_event(
                    build_synthetic_pipeline_error_record(
                        process.pipeline_run.run_id,
                        message.error_info,
                        process.pipeline_run.pipeline_name,
                    )
                )
            elif isinstance(message, ProcessStartedSentinel):
                process.pipeline_run.handle_new_event(
                    build_process_started_event(
                        process.pipeline_run.run_id,
                        process.pipeline_run.pipeline_name,
                        message.process_id,
                    )
                )
            else:
                process.pipeline_run.handle_new_event(message)
        return False

    def join(self):
        '''Waits until all there are no processes enqueued.'''
        while True:
            with self._processes_lock:
                if not self._processes and self._processing_semaphore.locked():
                    return True
            gevent.sleep(0.1)

    def execute_pipeline(self, repository_container, pipeline, pipeline_run, throw_on_user_error):
        check.invariant(
            throw_on_user_error is False,
            'Multiprocessing execute_pipeline does not rethrow user error',
        )

        message_queue = self._multiprocessing_context.Queue()
        p = self._multiprocessing_context.Process(
            target=execute_pipeline_through_queue,
            args=(
                repository_container.repository_info,
                pipeline_run.selector.name,
                pipeline_run.selector.solid_subset,
                pipeline_run.config,
            ),
            kwargs={
                'run_id': pipeline_run.run_id,
                'message_queue': message_queue,
                'reexecution_config': pipeline_run.reexecution_config,
                'step_keys_to_execute': pipeline_run.step_keys_to_execute,
            },
        )

        pipeline_run.handle_new_event(build_process_start_event(pipeline_run.run_id, pipeline.name))

        p.start()
        with self._processes_lock:
            process = RunProcessWrapper(pipeline_run, p, message_queue)
            self._processes.append(process)


class RunProcessWrapper(namedtuple('RunProcessWrapper', 'pipeline_run process message_queue')):
    def __new__(cls, pipeline_run, process, message_queue):
        return super(RunProcessWrapper, cls).__new__(
            cls, check.inst_param(pipeline_run, 'pipeline_run', PipelineRun), process, message_queue
        )


def execute_pipeline_through_queue(
    repository_info,
    pipeline_name,
    solid_subset,
    environment_dict,
    run_id,
    message_queue,
    reexecution_config,
    step_keys_to_execute,
):
    """
    Execute pipeline using message queue as a transport
    """

    message_queue.put(ProcessStartedSentinel(os.getpid()))

    run_config = RunConfig(
        run_id,
        event_callback=message_queue.put,
        executor_config=InProcessExecutorConfig(throw_on_user_error=False),
        reexecution_config=reexecution_config,
        step_keys_to_execute=step_keys_to_execute,
        storage_mode=get_storage_mode(environment_dict),
    )

    from .app import RepositoryContainer

    repository_container = RepositoryContainer(repository_info)
    if repository_container.repo_error:
        message_queue.put(
            MultiprocessingError(
                serializable_error_info_from_exc_info(repository_container.repo_error)
            )
        )
        return

    try:
        result = execute_pipeline(
            repository_container.repository.get_pipeline(pipeline_name).build_sub_pipeline(
                solid_subset
            ),
            environment_dict,
            run_config=run_config,
        )
        return result
    except:  # pylint: disable=W0702
        message_queue.put(
            MultiprocessingError(serializable_error_info_from_exc_info(sys.exc_info()))
        )
    finally:
        message_queue.put(MultiprocessingDone())

from __future__ import absolute_import
from collections import namedtuple
import copy
import multiprocessing
import os
import sys
import time

import gevent

from dagster import check, ReentrantInfo, PipelineDefinition
from dagster.core.execution import create_typed_environment, execute_reentrant_pipeline
from dagster.core.events import PipelineEventRecord, EventType
from dagster.core.types.evaluator import evaluate_config_value
from dagster.core.system_config.types import construct_environment_config
from dagster.utils.error import serializable_error_info_from_exc_info, SerializableErrorInfo
from dagster.utils.logging import level_from_string

from .pipeline_run_storage import PipelineRun


class PipelineExecutionManager(object):
    def execute_pipeline(self, repository_container, pipeline, pipeline_run):
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


class SynchronousExecutionManager(PipelineExecutionManager):
    def execute_pipeline(self, repository_container, pipeline, pipeline_run):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        try:
            return execute_reentrant_pipeline(
                pipeline,
                create_typed_environment(pipeline, pipeline_run.config),
                throw_on_error=False,
                reentrant_info=ReentrantInfo(
                    pipeline_run.run_id, event_callback=pipeline_run.handle_new_event
                ),
            )
        except:  # pylint: disable=W0702
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
        # Set execution method to spawn, to avoid fork and to have same behavior between platforms.
        # Older versions are stuck with whatever is the default on their platform (fork on
        # Unix-like and spawn on windows)
        #
        # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.get_context
        if hasattr(multiprocessing, 'get_context'):
            self._multiprocessing_context = multiprocessing.get_context('spawn')
        else:
            self._multiprocessing_context = multiprocessing
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

    def execute_pipeline(self, repository_container, pipeline, pipeline_run):
        message_queue = self._multiprocessing_context.Queue()
        p = self._multiprocessing_context.Process(
            target=execute_pipeline_through_queue,
            args=(repository_container.repository_info, pipeline.name, pipeline_run.config),
            kwargs={'run_id': pipeline_run.run_id, 'message_queue': message_queue},
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


def execute_pipeline_through_queue(repository_info, pipeline_name, config, run_id, message_queue):
    """
    Execute pipeline using message queue as a transport
    """

    message_queue.put(ProcessStartedSentinel(os.getpid()))

    reentrant_info = ReentrantInfo(run_id, event_callback=message_queue.put)

    from .app import RepositoryContainer

    repository_container = RepositoryContainer(repository_info)
    if repository_container.repo_error:
        message_queue.put(
            MultiprocessingError(
                serializable_error_info_from_exc_info(repository_container.repo_error)
            )
        )
        return

    pipeline = repository_container.repository.get_pipeline(pipeline_name)
    typed_environment = construct_environment_config(
        evaluate_config_value(pipeline.environment_type, config).value
    )

    try:
        result = execute_reentrant_pipeline(
            pipeline, typed_environment, throw_on_error=False, reentrant_info=reentrant_info
        )
        return result
    except:  # pylint: disable=W0702
        message_queue.put(
            MultiprocessingError(serializable_error_info_from_exc_info(sys.exc_info()))
        )
    finally:
        message_queue.put(MultiprocessingDone())

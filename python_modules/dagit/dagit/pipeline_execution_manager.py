from __future__ import absolute_import
import copy
from collections import namedtuple
import multiprocessing
import time
import queue
import sys
import gevent

from dagster import (check, ReentrantInfo, PipelineDefinition)
from dagster.core.execution import (
    execute_reentrant_pipeline,
)
from dagster.core.evaluator import evaluate_config_value
from dagster.core.events import PipelineEventRecord, EventType
from dagster.utils.error import (
    serializable_error_info_from_exc_info,
    SerializableErrorInfo,
)
from dagster.utils.logging import level_from_string

from .pipeline_run_storage import PipelineRun


class PipelineExecutionManager(object):
    def execute_pipeline(self, repository_container, pipeline, pipeline_run):
        raise NotImplementedError()


class SyntheticPipelineEventRecord(PipelineEventRecord):
    def __init__(self, message, level, event_type, run_id, timestamp, error_info):
        self._message = check.str_param(message, 'message')
        self._level = check.int_param(level, 'level')
        self._event_type = check.inst_param(event_type, 'event_type', EventType)
        self._run_id = check.str_param(run_id, 'run_id')
        self._timestamp = check.float_param(timestamp, 'timestamp')
        self._error_info = check.opt_inst_param(error_info, 'error_info', SerializableErrorInfo)

    @property
    def message(self):
        return self._message

    @property
    def level(self):
        return self._level

    @property
    def original_message(self):
        return self._message

    @property
    def event_type(self):
        return self._event_type

    @property
    def run_id(self):
        return self._run_id

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def error_info(self):
        return self._error_info

    @staticmethod
    def error_record(run_id, error_info):
        return SyntheticPipelineEventRecord(
            message=error_info.message,
            level=level_from_string('ERROR'),
            event_type=EventType.PIPELINE_FAILURE,
            run_id=run_id,
            timestamp=time.time(),
            error_info=error_info
        )


class SynchronousExecutionManager(PipelineExecutionManager):
    def execute_pipeline(self, repository_container, pipeline, pipeline_run):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        try:
            return execute_reentrant_pipeline(
                pipeline,
                pipeline_run.typed_environment,
                throw_on_error=False,
                reentrant_info=ReentrantInfo(
                    pipeline_run.run_id,
                    event_callback=pipeline_run.handle_new_event,
                ),
            )
        except Exception as e:
            pipeline_run.handle_new_event(
                SyntheticPipelineEventRecord.error_record(
                    pipeline_run.run_id, serializable_error_info_from_exc_info(sys.exc_info())
                )
            )


class MultiprocessingDone(object):
    pass


class MultiprocessingError(object):
    def __init__(self, error_info):
        self.error_info = check.inst_param(error_info, 'error_info', SerializableErrorInfo)


class MultiprocessingExecutionManager(PipelineExecutionManager):
    def __init__(self):
        if hasattr(multiprocessing, 'get_context'):
            self._context = multiprocessing.get_context('spawn')
        else:
            # Python 2.7 doesn't support alternative starting methods
            self._context = multiprocessing
        self._processes_lock = self._context.Lock()
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
                    except:
                        process.pipeline_run.handle_new_event(
                            SyntheticPipelineEventRecord.error_record(
                                process.pipeline_run.run_id,
                                serializable_error_info_from_exc_info(sys.exc_info())
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
                    SyntheticPipelineEventRecord.error_record(
                        process.pipeline_run.run_id, message.error_info
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
        message_queue = self._context.Queue()
        p = self._context.Process(
            target=execute_pipeline_through_queue,
            args=(
                repository_container.repository_info,
                pipeline.name,
                pipeline_run.config,
            ),
            kwargs={
                'run_id': pipeline_run.run_id,
                'message_queue': message_queue,
            }
        )
        p.start()
        with self._processes_lock:
            process = RunProcessWrapper(
                pipeline_run,
                p,
                message_queue,
            )
            self._processes.append(process)


class RunProcessWrapper(namedtuple('RunProcessWrapper', 'pipeline_run process message_queue')):
    def __new__(cls, pipeline_run, process, message_queue):
        return super(RunProcessWrapper, cls).__new__(
            cls, check.inst_param(pipeline_run, 'pipeline_run', PipelineRun), process, message_queue
        )


def execute_pipeline_through_queue(
    repository_info,
    pipeline_name,
    config,
    run_id,
    message_queue,
):
    """
    Execute pipeline using message queue as a transport
    """
    reentrant_info = ReentrantInfo(
        run_id,
        event_callback=lambda event: message_queue.put(event),
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

    pipeline = repository_container.repository.get_pipeline(pipeline_name)
    typed_environment = evaluate_config_value(pipeline.environment_type, config).value

    try:
        result = execute_reentrant_pipeline(
            pipeline, typed_environment, throw_on_error=False, reentrant_info=reentrant_info
        )
        return result
    except Exception as e:
        message_queue.put(
            MultiprocessingError(serializable_error_info_from_exc_info(sys.exc_info()))
        )
    finally:
        message_queue.put(MultiprocessingDone())

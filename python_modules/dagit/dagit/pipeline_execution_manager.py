from __future__ import absolute_import
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
from dagster.core.events import PipelineEventRecord, EventType
from dagster.utils.error import (
    serializable_error_info_from_exc_info,
    SerializableErrorInfo,
)
from dagster.utils.logging import level_from_string

from .pipeline_run_storage import PipelineRun


class PipelineExecutionManager(object):
    def execute_pipeline(self, pipeline, typed_environment, pipeline_run):
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
    def execute_pipeline(self, pipeline, typed_environment, pipeline_run):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        try:
            return execute_reentrant_pipeline(
                pipeline,
                typed_environment,
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
        self._processes_lock = multiprocessing.Lock()
        self._processes = []

        gevent.spawn(self._start_polling)

    def _start_polling(self):
        while True:
            self._poll()
            gevent.sleep(0.1)

    def _poll(self):
        with self._processes_lock:
            processes = self._processes
            self._processes = []

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
        '''Joins on all processes synchronously.'''
        for process in self._processes:
            while process.process.is_alive():
                process.process.join(0.1)
                gevent.sleep(0.1)

    def execute_pipeline(self, pipeline, typed_environment, pipeline_run):
        message_queue = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=execute_pipeline_through_queue,
            args=(
                pipeline,
                typed_environment,
            ),
            kwargs={
                'throw_on_error': False,
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
            cls, check.inst_param(pipeline_run, 'pipeline_run', PipelineRun),
            check.inst_param(process, 'process', multiprocessing.Process), message_queue
        )


def execute_pipeline_through_queue(
    pipeline,
    typed_environment,
    throw_on_error,
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

    try:
        result = execute_reentrant_pipeline(
            pipeline,
            typed_environment,
            throw_on_error=throw_on_error,
            reentrant_info=reentrant_info
        )
        return result
    except Exception as e:
        message_queue.put(
            MultiprocessingError(serializable_error_info_from_exc_info(sys.exc_info()))
        )
    finally:
        message_queue.put(MultiprocessingDone())

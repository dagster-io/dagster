from __future__ import absolute_import

import abc
import os
import sys
from queue import Empty

import gevent
import six

from dagster import ExecutionTargetHandle, PipelineDefinition, PipelineExecutionResult, check
from dagster.core.errors import DagsterSubprocessError
from dagster.core.events import EngineEventData
from dagster.core.execution.api import execute_run_iterator
from dagster.core.instance import DagsterInstance
from dagster.utils import get_multiprocessing_context, start_termination_thread
from dagster.utils.error import serializable_error_info_from_exc_info


class PipelineExecutionManager(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def execute_pipeline(self, handle, pipeline, pipeline_run, instance):
        '''Subclasses must implement this method.'''

    @abc.abstractmethod
    def terminate(self, run_id):
        '''Attempt to terminate a run if possible. Return False if unable to, True if it can.'''

    @abc.abstractmethod
    def can_terminate(self, run_id):
        '''Whether or not this execution manager can terminate the given run_id'''

    @abc.abstractmethod
    def get_active_run_count(self):
        '''The number of actively running execution jobs'''

    @abc.abstractmethod
    def is_active(self, run_id):
        '''Whether a given run_id is actively running'''


class SynchronousExecutionManager(PipelineExecutionManager):
    def __init__(self):
        self._active = set()

    def execute_pipeline(self, _, pipeline, pipeline_run, instance):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)

        event_list = []
        self._active.add(pipeline_run.run_id)
        for event in execute_run_iterator(pipeline, pipeline_run, instance):
            event_list.append(event)
        self._active.remove(pipeline_run.run_id)
        return PipelineExecutionResult(pipeline, pipeline_run.run_id, event_list, lambda: None)

    def can_terminate(self, run_id):
        return False

    def terminate(self, run_id):
        return False

    def get_active_run_count(self):
        return len(self._active)

    def is_active(self, run_id):
        return run_id in self._active


SUBPROCESS_TICK = 0.5


class SubprocessExecutionManager(PipelineExecutionManager):
    '''
    This execution manager launches a new process for every pipeline invocation.
    It tries to spawn new processes with clean state whenever possible,
    in order to pick up the latest changes, to not inherit in-memory
    state accumulated from the webserver, and to mimic standalone invocations
    of the CLI as much as possible.

    The exception here is unix variants before python 3.4. Before 3.4
    multiprocessing could not configure process start methods, so it
    falls back to system default. On unix variants that means it forks
    the process. This could lead to subtle behavior changes between
    python 2 and python 3.
    '''

    def __init__(self, instance):
        self._multiprocessing_context = get_multiprocessing_context()
        self._instance = instance
        self._living_process_by_run_id = {}
        self._term_events = {}
        self._processes_lock = self._multiprocessing_context.Lock()

        gevent.spawn(self._clock)

    def _generate_synthetic_error_from_crash(self, run):
        message = 'Pipeline execution process for {run_id} unexpectedly exited.'.format(
            run_id=run.run_id
        )
        self._instance.report_engine_event(
            self.__class__, message, run,
        )
        self._instance.report_run_failed(run)

    def _living_process_snapshot(self):
        with self._processes_lock:
            return {run_id: process for run_id, process in self._living_process_by_run_id.items()}

    def _clock(self):
        '''
        This function polls the instance to synchronize it with the state of processes managed
        by this manager instance. On every tick (every 0.5 seconds currently) it checks for zombie
        processes
        '''
        while True:
            self._check_for_zombies()
            gevent.sleep(SUBPROCESS_TICK)

    def _check_for_zombies(self):
        '''
        Checks the current index of run_id => process and sees if any of them are dead. If they are,
        it queries the instance to see if the runs are in a proper terminal state (success or
        failure). If not, then we can assume that the underlying process died unexpected and clean
        everything. In either case, the dead process is removed from the run_id => process index.
        '''
        runs_to_clear = []

        living_process_snapshot = self._living_process_snapshot()

        for run_id, process in living_process_snapshot.items():
            if not process.is_alive():
                run = self._instance.get_run_by_id(run_id)
                if not run:  # defensive
                    continue

                runs_to_clear.append(run_id)

                # expected terminal state. it's fine for process to be dead
                if run.is_finished:
                    continue

                # the process died in an unexpected manner. inform the system
                self._generate_synthetic_error_from_crash(run)

        with self._processes_lock:
            for run_to_clear_id in runs_to_clear:
                del self._living_process_by_run_id[run_to_clear_id]
                del self._term_events[run_to_clear_id]

    def check(self):
        '''
        Utility method for pytest to manually kick off zombie cleanup calls (in absence of
        gevent)
        '''
        self._check_for_zombies()

    def execute_pipeline(self, handle, pipeline, pipeline_run, instance):
        '''Subclasses must implement this method.'''
        check.inst_param(handle, 'handle', ExecutionTargetHandle)
        term_event = self._multiprocessing_context.Event()
        mp_process = self._multiprocessing_context.Process(
            target=self.__class__.in_mp_process,
            kwargs={
                'handle': handle,
                'pipeline_run': pipeline_run,
                'instance_ref': instance.get_ref(),
                'term_event': term_event,
            },
        )

        instance.report_engine_event(
            self.__class__,
            'About to start process for pipeline "{pipeline_name}" (run_id: {run_id}).'.format(
                pipeline_name=pipeline_run.pipeline_name, run_id=pipeline_run.run_id
            ),
            pipeline_run,
            engine_event_data=EngineEventData(marker_start='dagit_subprocess_init'),
        )
        mp_process.start()

        with self._processes_lock:
            self._living_process_by_run_id[pipeline_run.run_id] = mp_process
            self._term_events[pipeline_run.run_id] = term_event

    def join(self):
        with self._processes_lock:
            for run_id, process in self._living_process_by_run_id.items():
                if process.is_alive():
                    process.join()

                run = self._instance.get_run_by_id(run_id)

                if run and not run.is_finished:
                    self._generate_synthetic_error_from_crash(run)

    def _get_process(self, run_id):
        with self._processes_lock:
            return self._living_process_by_run_id.get(run_id)

    def is_process_running(self, run_id):
        check.str_param(run_id, 'run_id')
        process = self._get_process(run_id)
        return process.is_alive() if process else False

    def can_terminate(self, run_id):
        check.str_param(run_id, 'run_id')

        process = self._get_process(run_id)

        if not process:
            return False

        if not process.is_alive():
            return False

        return True

    def terminate(self, run_id):
        check.str_param(run_id, 'run_id')

        process = self._get_process(run_id)

        if not process:
            return False

        if not process.is_alive():
            return False

        self._term_events[run_id].set()
        process.join()
        return True

    def get_active_run_count(self):
        with self._processes_lock:
            return len(self._living_process_by_run_id)

    def is_active(self, run_id):
        with self._processes_lock:
            return run_id in self._living_process_by_run_id

    @classmethod
    def in_mp_process(cls, handle, pipeline_run, instance_ref, term_event):
        """
        Execute pipeline using message queue as a transport
        """
        run_id = pipeline_run.run_id
        pipeline_name = pipeline_run.pipeline_name

        instance = DagsterInstance.from_ref(instance_ref)
        pid = os.getpid()
        instance.report_engine_event(
            cls,
            'Started process for pipeline (pid: {pid}).'.format(pid=pid),
            pipeline_run,
            EngineEventData.in_process(pid, marker_end='dagit_subprocess_init'),
        )

        start_termination_thread(term_event)

        try:
            handle.build_repository_definition()
            pipeline_def = handle.with_pipeline_name(pipeline_name).build_pipeline_definition()
        except Exception:  # pylint: disable=broad-except
            instance.report_engine_event(
                cls,
                'Failed attempting to load pipeline "{}"'.format(pipeline_name),
                pipeline_run,
                EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            )
            return

        try:
            event_list = []
            for event in execute_run_iterator(
                pipeline_def.build_sub_pipeline(pipeline_run.selector.solid_subset),
                pipeline_run,
                instance,
            ):
                event_list.append(event)
            return PipelineExecutionResult(pipeline_def, run_id, event_list, lambda: None)

        # Add a DagsterEvent for unexpected exceptions
        # Explicitly ignore KeyboardInterrupts since they are used for termination
        except DagsterSubprocessError as err:
            if not all(
                [
                    err_info.cls_name == 'KeyboardInterrupt'
                    for err_info in err.subprocess_error_infos
                ]
            ):
                instance.report_engine_event(
                    cls,
                    'An exception was thrown during execution that is likely a framework error, '
                    'rather than an error in user code.',
                    pipeline_run,
                    EngineEventData.engine_error(
                        serializable_error_info_from_exc_info(sys.exc_info())
                    ),
                )
        except Exception:  # pylint: disable=broad-except
            instance.report_engine_event(
                cls,
                'An exception was thrown during execution that is likely a framework error, '
                'rather than an error in user code.',
                pipeline_run,
                EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            )
        finally:
            instance.report_engine_event(
                cls, 'Process for pipeline exited (pid: {pid}).'.format(pid=pid), pipeline_run,
            )


class QueueingSubprocessExecutionManager(PipelineExecutionManager):
    def __init__(self, instance, max_concurrent_runs):
        check.inst_param(instance, 'instance', DagsterInstance)
        self._delegate = SubprocessExecutionManager(instance)
        self._max_concurrent_runs = check.int_param(max_concurrent_runs, 'max_concurrent_runs')
        self._multiprocessing_context = get_multiprocessing_context()
        self._queue = self._multiprocessing_context.JoinableQueue(maxsize=0)
        gevent.spawn(self._clock)

    def _clock(self):
        while True:
            self._check_queue()
            gevent.sleep(1)

    def _check_queue(self):
        run_count = self._delegate.get_active_run_count()
        if run_count < self._max_concurrent_runs:
            try:
                job_args = self._queue.get(block=False)
            except Empty:
                return
            else:
                self._start_pipeline_execution(job_args)

    def _start_pipeline_execution(self, job_args):
        handle = job_args['handle']
        pipeline_run = job_args['pipeline_run']
        pipeline = handle.build_repository_definition().get_pipeline(pipeline_run.pipeline_name)
        instance = DagsterInstance.from_ref(job_args['instance_ref'])
        self._delegate.execute_pipeline(handle, pipeline, pipeline_run, instance)

    def execute_pipeline(self, handle, pipeline, pipeline_run, instance):
        check.inst_param(handle, 'handle', ExecutionTargetHandle)
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        job_args = {
            'handle': handle,
            'pipeline_run': pipeline_run,
            'instance_ref': instance.get_ref(),
        }
        self._queue.put(job_args, block=False)
        self._check_queue()

    def check(self):
        '''
        Utility method for pytest to manually kick off queue check calls
        '''
        self._check_queue()
        self._delegate.check()

    def can_terminate(self, run_id):
        # deal with enqueued shit
        return self._delegate.can_terminate(run_id)

    def terminate(self, run_id):
        # deal with enqueued shit
        return self._delegate.terminate(run_id)

    def get_active_run_count(self):
        return self._delegate.get_active_run_count()

    def is_active(self, run_id):
        return self._delegate.is_active(run_id)

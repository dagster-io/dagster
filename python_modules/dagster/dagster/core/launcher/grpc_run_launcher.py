import multiprocessing
import threading
import time
import weakref

from dagster import check
from dagster.api.execute_run import sync_execute_run_grpc
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.instance.ref import InstanceRef
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.grpc.client import ephemeral_grpc_api_client
from dagster.grpc.types import CancelExecutionRequest
from dagster.serdes import ConfigurableClass

from .base import RunLauncher

SUBPROCESS_TICK = 0.5


def _launched_run_client(instance_ref, pipeline_origin, pipeline_run_id, cancellation_event):
    check.inst_param(instance_ref, 'instance_ref', InstanceRef)
    check.inst_param(pipeline_origin, 'pipeline_origin', PipelinePythonOrigin)
    check.str_param(pipeline_run_id, 'pipeline_run_id')
    check.inst_param(cancellation_event, 'cancellation_event', multiprocessing.synchronize.Event)
    instance = DagsterInstance.from_ref(instance_ref)
    pipeline_run = instance.get_run_by_id(pipeline_run_id)

    with ephemeral_grpc_api_client(max_workers=2) as api_client:
        execute_run_thread = threading.Thread(
            target=sync_execute_run_grpc,
            kwargs={
                'api_client': api_client,
                'instance_ref': instance_ref,
                'pipeline_origin': pipeline_origin,
                'pipeline_run': pipeline_run,
            },
        )

        execute_run_thread.start()
        while execute_run_thread.is_alive():
            if cancellation_event.is_set():
                api_client.cancel_execution(CancelExecutionRequest(run_id=pipeline_run_id))
                execute_run_thread.join()
            time.sleep(SUBPROCESS_TICK)


class EphemeralGrpcRunLauncher(RunLauncher, ConfigurableClass):
    '''Launches runs in local processes, using GRPC for IPC.

    Note that this launcher does *not* launch runs against a (possibly remote) running GRPC server.

    Instead, for each call to launch_run, a new process is created that uses a wrapper around the
    ephemeral_grpc_api_client machinery to spin up a GRPC server. A streaming query is performed
    by the client process, and then the client process terminates the server and itself exits.
    If there are N launched runs, 2N processes are created.

    This is a drop-in replacement for the CliApiRunLauncher
    '''

    def __init__(self, inst_data=None):
        self._instance_ref = None
        # Dict[str, multiprocessing.Process]
        self._living_process_by_run_id = {}
        # Dict[str, multiprocessing.Process]
        self._cancellation_events_by_run_id = {}
        self._processes_lock = threading.Lock()
        self._stopping = False
        self._clock_thread = None
        self._inst_data = inst_data

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return EphemeralGrpcRunLauncher(inst_data=inst_data)

    @property
    def _instance(self):
        return self._instance_ref() if self._instance_ref else None

    def initialize(self, instance):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.invariant(self._instance is None, 'Must only call initialize once')
        # Store a weakref to avoid a circular reference / enable GC
        self._instance_ref = weakref.ref(instance)

        self._clock_thread = threading.Thread(
            target=self._clock, args=(), name='grpc-run-launcher-clock'
        )
        self._clock_thread.daemon = True
        self._clock_thread.start()

    def _generate_synthetic_error_from_crash(self, run):
        message = 'User process: GRPC client for {run_id} unexpectedly exited.'.format(
            run_id=run.run_id
        )
        self._instance.report_engine_event(message, run, cls=self.__class__)

    def _living_process_snapshot(self):
        with self._processes_lock:
            return {run_id: process for run_id, process in self._living_process_by_run_id.items()}

    def _clock(self):
        '''
        This function polls the instance to synchronize it with the state of processes managed
        by this manager instance. On every tick (every 0.5 seconds currently) it checks for zombie
        processes
        '''
        while not self._stopping:
            self._check_for_zombies()

            time.sleep(SUBPROCESS_TICK)

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
            if not process.is_alive:
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
                self._delete_process(run_to_clear_id)

    # always call this within lock
    def _delete_process(self, run_id):
        if run_id in self._living_process_by_run_id:
            del self._living_process_by_run_id[run_id]
        if run_id in self._cancellation_events_by_run_id:
            del self._cancellation_events_by_run_id[run_id]

    def launch_run(self, instance, run, external_pipeline):
        '''Subclasses must implement this method.'''

        check.inst_param(run, 'run', PipelineRun)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)

        cancellation_event = multiprocessing.Event()
        process = multiprocessing.Process(
            target=_launched_run_client,
            kwargs={
                'instance_ref': self._instance.get_ref(),
                'pipeline_origin': external_pipeline.get_origin(),
                'pipeline_run_id': run.run_id,
                'cancellation_event': cancellation_event,
            },
        )

        with self._processes_lock:
            self._living_process_by_run_id[run.run_id] = process
            self._cancellation_events_by_run_id[run.run_id] = cancellation_event

        process.start()

        return run

    def join(self):
        # If this hasn't been initialized at all, we can just do a noop
        if not self._instance:
            return

        # Stop the watcher tread
        self._stopping = True
        self._clock_thread.join()

        # Wrap up all open executions
        with self._processes_lock:
            for run_id, process in self._living_process_by_run_id.items():
                if process.is_alive():
                    process.join()

                run = self._instance.get_run_by_id(run_id)

                if run and not run.is_finished:
                    self._generate_synthetic_error_from_crash(run)

    def _get_process(self, run_id):
        if not self._instance:
            return (None, None)

        with self._processes_lock:
            return (
                self._living_process_by_run_id.get(run_id),
                self._cancellation_events_by_run_id.get(run_id),
            )

    def is_process_running(self, run_id):
        check.str_param(run_id, 'run_id')
        process, _ = self._get_process(run_id)
        return process.is_alive() if process else False

    def can_terminate(self, run_id):
        check.str_param(run_id, 'run_id')

        process, cancellation_event = self._get_process(run_id)

        if not process or not cancellation_event:
            return False

        if not process.is_alive() or cancellation_event.is_set():
            return False

        return True

    def terminate(self, run_id):
        check.str_param(run_id, 'run_id')

        process, cancellation_event = self._get_process(run_id)

        if not process or not cancellation_event:
            return False

        if not process.is_alive() or cancellation_event.is_set():
            return False

        with self._processes_lock:
            self._cancellation_events_by_run_id[run_id].set()

        return True

    def get_active_run_count(self):
        if not self._instance:
            return 0

        with self._processes_lock:
            return len(self._living_process_by_run_id)

    def is_active(self, run_id):
        if not self._instance:
            return False

        with self._processes_lock:
            return run_id in self._living_process_by_run_id

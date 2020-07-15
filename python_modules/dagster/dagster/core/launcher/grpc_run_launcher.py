import sys
import threading
import time

from dagster import check
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass, serialize_dagster_namedtuple
from dagster.serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess
from dagster.seven import json
from dagster.utils import file_relative_path

from .base import RunLauncher

SUBPROCESS_TICK = 0.5


class EphemeralGrpcRunLauncher(RunLauncher, ConfigurableClass):
    '''Launches runs in local processes, using GRPC for IPC.

    Note that this launcher does *not* launch runs against a (possibly remote) running GRPC server.

    Instead, for each call to launch_run, a new process is created that uses a wrapper around the
    ephemeral_grpc_api_client machinery to spin up a GRPC server. A streaming query is performed
    by the client process, and then the client process hard terminates the server and itself exits.
    If there are N launched runs, 2N processes are created.

    This is a drop-in replacement for the CliApiRunLauncher
    '''

    def __init__(self, inst_data=None):
        self._instance = None
        self._living_process_by_run_id = {}
        self._output_files_by_run_id = {}
        self._processes_lock = threading.Lock()
        self._stopping = False
        self._thread = None
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

    def initialize(self, instance):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.invariant(self._instance is None, 'Must only call initialize once')
        self._instance = instance

        self._thread = threading.Thread(target=self._clock, args=())
        self._thread.daemon = True
        self._thread.start()

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
            if not process.poll() is None:
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
        del self._living_process_by_run_id[run_id]

    def launch_run(self, instance, run, external_pipeline):
        '''Subclasses must implement this method.'''

        check.inst_param(run, 'run', PipelineRun)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)

        # We use the IPC subprocess machinery here because we want to be able to interrupt this
        # process. We could use multiprocessing and a thread to poll a shared multiprocessing.Event,
        # interrupting when the event is set, but in this case that's six of one, half a dozen of
        # the other.
        process = open_ipc_subprocess(
            [
                sys.executable,
                file_relative_path(__file__, 'sync_cli_api_execute_run.py'),
                json.dumps(
                    {
                        'instance_ref': serialize_dagster_namedtuple(self._instance.get_ref()),
                        'pipeline_origin': serialize_dagster_namedtuple(
                            external_pipeline.get_origin()
                        ),
                        'pipeline_run_id': run.run_id,
                    }
                ),
            ]
        )

        with self._processes_lock:
            self._living_process_by_run_id[run.run_id] = process

        return run

    def join(self):
        # If this hasn't been initialized at all, we can just do a noop
        if not self._instance:
            return

        # Stop the watcher tread
        self._stopping = True
        self._thread.join()

        # Wrap up all open executions
        with self._processes_lock:
            for run_id, process in self._living_process_by_run_id.items():
                if process.poll() is None:
                    process.wait()

                run = self._instance.get_run_by_id(run_id)

                if run and not run.is_finished:
                    self._generate_synthetic_error_from_crash(run)

    def _get_process(self, run_id):
        if not self._instance:
            return None

        with self._processes_lock:
            return self._living_process_by_run_id.get(run_id)

    def is_process_running(self, run_id):
        check.str_param(run_id, 'run_id')
        process = self._get_process(run_id)
        return process.poll() is None if process else False

    def can_terminate(self, run_id):
        check.str_param(run_id, 'run_id')

        process = self._get_process(run_id)

        if not process:
            return False

        if not process.poll() is None:
            return False

        return True

    def terminate(self, run_id):
        check.str_param(run_id, 'run_id')

        process = self._get_process(run_id)

        if not process:
            return False

        if not process.poll() is None:
            return False

        # Pipeline execution machinery is set up to gracefully
        # terminate and report to instance on KeyboardInterrupt
        interrupt_ipc_subprocess(process)
        process.wait()
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

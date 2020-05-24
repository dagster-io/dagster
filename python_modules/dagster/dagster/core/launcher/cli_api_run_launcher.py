import os
import signal
import threading
import time

from dagster import check
from dagster.api.execute_run import cli_api_execute_run
from dagster.config import Field
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass
from dagster.seven.temp_dir import get_system_temp_directory

from .base import RunLauncher

SUBPROCESS_TICK = 0.5


def _is_alive(popen):
    return popen.poll() is None


class CliApiRunLauncher(RunLauncher, ConfigurableClass):
    '''
    This run launcher launches a new process which invokes
    the command `dagster api execute_run`.
    '''

    def __init__(self, hijack_start=False, inst_data=None):
        self._instance = None
        self._living_process_by_run_id = {}
        self._output_files_by_run_id = {}
        self._processes_lock = None
        self._stopping = False
        self._thread = None
        self._inst_data = inst_data
        self._hijack_start = check.bool_param(hijack_start, 'hijack_start')

    @property
    def inst_data(self):
        return self._inst_data

    @property
    def hijack_start(self):
        return self._hijack_start

    @classmethod
    def config_type(cls):
        return {'hijack_start': Field(bool, is_required=False, default_value=False)}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return CliApiRunLauncher(hijack_start=config_value['hijack_start'], inst_data=inst_data)

    def initialize(self, instance):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.invariant(self._instance is None, 'Must only call initialize once')
        self._instance = instance

        self._processes_lock = threading.Lock()
        self._thread = threading.Thread(target=self._clock, args=())
        self._thread.daemon = True
        self._thread.start()

    def _generate_synthetic_error_from_crash(self, run):
        message = 'Pipeline execution process for {run_id} unexpectedly exited.'.format(
            run_id=run.run_id
        )
        self._instance.report_engine_event(message, run, cls=self.__class__)
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
            if not _is_alive(process):
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
        output_file = self._output_files_by_run_id[run_id]
        try:
            if os.path.exists(output_file):
                os.unlink(output_file)
        finally:
            del self._output_files_by_run_id[run_id]

    def launch_run(self, instance, run, external_pipeline=None):
        '''Subclasses must implement this method.'''

        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(run, 'run', PipelineRun)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        env_handle = external_pipeline.handle.repository_handle.environment_handle
        check.param_invariant(
            env_handle.in_process_origin.repo_yaml,
            'external_pipeline',
            'Must come from repo_yaml for now',
        )

        # initialize when the first run happens
        if not self._instance:
            self.initialize(instance)

        output_file = os.path.join(
            get_system_temp_directory(), 'cli-api-execute-run-{}'.format(run.run_id)
        )

        process = cli_api_execute_run(
            output_file=output_file,
            instance=self._instance,
            repo_yaml=env_handle.in_process_origin.repo_yaml,
            pipeline_run=run,
        )

        with self._processes_lock:
            self._living_process_by_run_id[run.run_id] = process
            self._output_files_by_run_id[run.run_id] = output_file

        return run

    def join(self):
        # If this hasn't been initialize at all, we can just do a noop
        if not self._instance:
            return

        # Stop the watcher tread
        self._stopping = True
        self._thread.join()

        # Wrap up all open executions
        with self._processes_lock:
            for run_id, process in self._living_process_by_run_id.items():
                if _is_alive(process):
                    _stdout, _std_error = process.communicate()

                run = self._instance.get_run_by_id(run_id)

                if run and not run.is_finished:
                    self._generate_synthetic_error_from_crash(run)

            for output_file in self._output_files_by_run_id.values():
                if os.path.exists(output_file):
                    os.unlink(output_file)

    def _get_process(self, run_id):
        with self._processes_lock:
            return self._living_process_by_run_id.get(run_id)

    def is_process_running(self, run_id):
        check.str_param(run_id, 'run_id')
        process = self._get_process(run_id)
        return _is_alive(process) if process else False

    @property
    def supports_termination(self):
        return True

    def can_terminate(self, run_id):
        check.str_param(run_id, 'run_id')

        process = self._get_process(run_id)

        if not process:
            return False

        if not _is_alive(process):
            return False

        return True

    def terminate(self, run_id):
        check.str_param(run_id, 'run_id')

        process = self._get_process(run_id)

        if not process:
            return False

        if not _is_alive(process):
            return False

        # Send sigint to allow the pipeline run to terminate gracefully and
        # report termination to the instance.
        process.send_signal(signal.SIGINT)

        process.wait()
        return True

    def get_active_run_count(self):
        with self._processes_lock:
            return len(self._living_process_by_run_id)

    def is_active(self, run_id):
        with self._processes_lock:
            return run_id in self._living_process_by_run_id

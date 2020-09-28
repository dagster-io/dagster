import os
import threading
import weakref

from dagster import check, seven
from dagster.api.execute_run import cli_api_launch_run
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass
from dagster.serdes.ipc import interrupt_ipc_subprocess
from dagster.seven.temp_dir import get_system_temp_directory

from .base import RunLauncher

SUBPROCESS_TICK = 0.5


def _is_alive(popen):
    return popen.poll() is None


class CliApiRunLauncher(RunLauncher, ConfigurableClass):
    """
    This run launcher launches a new process by invoking the command `dagster api execute_run`.

    This run launcher, the associated CLI, and the homegrown IPC mechanism used to communicate with
    the launched processes, are slated for deprecation in favor of communicating over GRPC with
    managed server processes. You will likely not want to use the ``CliApiRunLauncher`` directly.
    Instead, use the :py:class:`dagster.DefaultRunLauncher`, which is aware of instance- and
    repository-level options governing whether repositories should be loaded over the CLI or over
    GRPC, and able to switch between both.
    """

    def __init__(self, inst_data=None):
        self._instance_ref = None
        self._living_process_by_run_id = {}
        self._output_files_by_run_id = {}
        self._processes_lock = threading.Lock()
        self._cleanup_stop_event = None
        self._cleanup_thread = None
        self._inst_data = inst_data

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return CliApiRunLauncher(inst_data=inst_data)

    @property
    def _instance(self):
        return self._instance_ref() if self._instance_ref else None

    def initialize(self, instance):
        check.inst_param(instance, "instance", DagsterInstance)
        check.invariant(self._instance is None, "Must only call initialize once")

        # Store a weakref to avoid a circular reference / enable GC
        self._instance_ref = weakref.ref(instance)

    def _generate_synthetic_error_from_crash(self, run):
        message = "Pipeline execution process for {run_id} unexpectedly exited.".format(
            run_id=run.run_id
        )
        self._instance.report_engine_event(message, run, cls=self.__class__)
        self._instance.report_run_failed(run)

    def _living_process_snapshot(self):
        with self._processes_lock:
            return {run_id: process for run_id, process in self._living_process_by_run_id.items()}

    def _clock(self):
        """
        This function polls the instance to synchronize it with the state of processes managed
        by this manager instance. On every tick (every 0.5 seconds currently) it checks for zombie
        processes
        """
        while True:
            self._cleanup_stop_event.wait(SUBPROCESS_TICK)
            if self._cleanup_stop_event.is_set():
                break
            self._check_for_zombies()

    def _check_for_zombies(self):
        """
        Checks the current index of run_id => process and sees if any of them are dead. If they are,
        it queries the instance to see if the runs are in a proper terminal state (success or
        failure). If not, then we can assume that the underlying process died unexpected and clean
        everything. In either case, the dead process is removed from the run_id => process index.
        """
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

    def launch_run(self, instance, run, external_pipeline):
        """Subclasses must implement this method."""

        if not self._cleanup_thread:
            self._cleanup_stop_event = threading.Event()
            self._cleanup_thread = threading.Thread(target=self._clock, args=())
            self._cleanup_thread.daemon = True
            self._cleanup_thread.start()

        check.inst_param(run, "run", PipelineRun)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)

        output_file = os.path.join(
            get_system_temp_directory(), "cli-api-execute-run-{}".format(run.run_id)
        )

        process = cli_api_launch_run(
            output_file=output_file,
            instance=self._instance,
            pipeline_origin=external_pipeline.get_origin(),
            pipeline_run=run,
        )

        with self._processes_lock:
            self._living_process_by_run_id[run.run_id] = process
            self._output_files_by_run_id[run.run_id] = output_file

        return run

    def dispose(self):
        # Stop the watcher thread
        if self._cleanup_thread:
            self._cleanup_stop_event.set()
            self._cleanup_thread.join()
            self._cleanup_thread = None
            self._cleanup_stop_event = None

    def join(self, timeout=15):
        self.dispose()

        # If this hasn't been initialized at all, we can just do a noop
        if not self._instance:
            return

        # Wrap up all open executions
        with self._processes_lock:
            for run_id, process in self._living_process_by_run_id.items():
                if _is_alive(process):
                    seven.wait_for_process(process, timeout=timeout)

                run = self._instance.get_run_by_id(run_id)

                if run and not run.is_finished:
                    self._generate_synthetic_error_from_crash(run)

            for output_file in self._output_files_by_run_id.values():
                if os.path.exists(output_file):
                    os.unlink(output_file)

    def _get_process(self, run_id):
        if not self._instance:
            return None

        with self._processes_lock:
            return self._living_process_by_run_id.get(run_id)

    def is_process_running(self, run_id):
        check.str_param(run_id, "run_id")
        process = self._get_process(run_id)
        return _is_alive(process) if process else False

    def can_terminate(self, run_id):
        check.str_param(run_id, "run_id")

        process = self._get_process(run_id)

        if not process:
            return False

        if not _is_alive(process):
            return False

        return True

    def terminate(self, run_id):
        check.str_param(run_id, "run_id")
        if not self._instance:
            return False

        run = self._instance.get_run_by_id(run_id)
        if not run:
            return False

        self._instance.report_engine_event(
            message="Received pipeline termination request.", pipeline_run=run, cls=self.__class__
        )

        process = self._get_process(run_id)

        if not process:
            self._instance.report_engine_event(
                message="Pipeline was not terminated since process is not found.",
                pipeline_run=run,
                cls=self.__class__,
            )
            return False

        if not _is_alive(process):
            self._instance.report_engine_event(
                message="Pipeline was not terminated since process is not alive.",
                pipeline_run=run,
                cls=self.__class__,
            )
            return False

        # Pipeline execution machinery is set up to gracefully
        # terminate and report to instance on KeyboardInterrupt
        interrupt_ipc_subprocess(process)
        seven.wait_for_process(process, timeout=30)

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

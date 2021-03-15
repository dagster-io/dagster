import io
import os
import shutil
import stat
import sys
import warnings

from crontab import CronTab
from dagster import DagsterInstance, check, utils
from dagster.core.host_representation import ExternalSchedule
from dagster.core.scheduler import DagsterSchedulerError, Scheduler
from dagster.core.test_utils import get_mocked_system_timezone
from dagster.serdes import ConfigurableClass


class SystemCronScheduler(Scheduler, ConfigurableClass):
    """Scheduler implementation that uses the local systems cron. Only works on unix systems that
    have cron.

    Enable this scheduler by adding it to your ``dagster.yaml`` in ``$DAGSTER_HOME``.
    """

    def __init__(
        self,
        inst_data=None,
    ):
        warnings.warn(
            "`SystemCronScheduler` is deprecated and will be removed in the 0.12.0 dagster release."
            " We recommend that you use the Dagster native scheduler instead, which runs automatically "
            " as part of the dagster-daemon process. You can configure this scheduler by removing "
            " the `scheduler` key from your `dagster.yaml` file. See"
            " https://docs.dagster.io/deployment/dagster-daemon for more information on how to deploy."
        )
        self._inst_data = inst_data

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SystemCronScheduler(inst_data=inst_data)

    def get_cron_tab(self):
        return CronTab(user=True)

    def debug_info(self):
        return "Running Cron Jobs:\n{jobs}\n".format(
            jobs="\n".join(
                [str(job) for job in self.get_cron_tab() if "dagster-schedule:" in job.comment]
            )
        )

    def start_schedule(self, instance, external_schedule):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(external_schedule, "external_schedule", ExternalSchedule)
        schedule_origin_id = external_schedule.get_external_origin_id()

        # If the cron job already exists, remove it. This prevents duplicate entries.
        # Then, add a new cron job to the cron tab.
        if self.running_schedule_count(instance, external_schedule.get_external_origin_id()) > 0:
            self._end_cron_job(instance, schedule_origin_id)

        self._start_cron_job(instance, external_schedule)

        # Verify that the cron job is running
        running_schedule_count = self.running_schedule_count(instance, schedule_origin_id)
        if running_schedule_count == 0:
            raise DagsterSchedulerError(
                "Attempted to write cron job for schedule "
                "{schedule_name}, but failed. "
                "The scheduler is not running {schedule_name}.".format(
                    schedule_name=external_schedule.name
                )
            )
        elif running_schedule_count > 1:
            raise DagsterSchedulerError(
                "Attempted to write cron job for schedule "
                "{schedule_name}, but duplicate cron jobs were found. "
                "There are {running_schedule_count} jobs running for the schedule."
                "To resolve, run `dagster schedule up`, or edit the cron tab to "
                "remove duplicate schedules".format(
                    schedule_name=external_schedule.name,
                    running_schedule_count=running_schedule_count,
                )
            )

    def stop_schedule(self, instance, schedule_origin_id):
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        schedule = self._get_schedule_state(instance, schedule_origin_id)

        self._end_cron_job(instance, schedule_origin_id)

        # Verify that the cron job has been removed
        running_schedule_count = self.running_schedule_count(instance, schedule_origin_id)
        if running_schedule_count > 0:
            raise DagsterSchedulerError(
                "Attempted to remove existing cron job for schedule "
                "{schedule_name}, but failed. "
                "There are still {running_schedule_count} jobs running for the schedule.".format(
                    schedule_name=schedule.name, running_schedule_count=running_schedule_count
                )
            )

    def wipe(self, instance):
        # Note: This method deletes schedules from ALL repositories
        check.inst_param(instance, "instance", DagsterInstance)

        # Delete all script files
        script_directory = os.path.join(instance.schedules_directory(), "scripts")
        if os.path.isdir(script_directory):
            shutil.rmtree(script_directory)

        # Delete all logs
        logs_directory = os.path.join(instance.schedules_directory(), "logs")
        if os.path.isdir(logs_directory):
            shutil.rmtree(logs_directory)

        # Remove all cron jobs
        with self.get_cron_tab() as cron_tab:
            for job in cron_tab:
                if "dagster-schedule:" in job.comment:
                    cron_tab.remove_all(comment=job.comment)

    def _get_bash_script_file_path(self, instance, schedule_origin_id):
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        script_directory = os.path.join(instance.schedules_directory(), "scripts")
        utils.mkdir_p(script_directory)

        script_file_name = "{}.sh".format(schedule_origin_id)
        return os.path.join(script_directory, script_file_name)

    def _cron_tag_for_schedule(self, schedule_origin_id):
        return "dagster-schedule: {schedule_origin_id}".format(
            schedule_origin_id=schedule_origin_id
        )

    def _get_command(self, script_file, instance, schedule_origin_id):
        schedule_log_file_path = self.get_logs_path(instance, schedule_origin_id)
        command = "{script_file} > {schedule_log_file_path} 2>&1".format(
            script_file=script_file, schedule_log_file_path=schedule_log_file_path
        )

        return command

    def _start_cron_job(self, instance, external_schedule):
        schedule_origin_id = external_schedule.get_external_origin_id()
        script_file = self._write_bash_script_to_file(instance, external_schedule)
        command = self._get_command(script_file, instance, schedule_origin_id)

        with self.get_cron_tab() as cron_tab:
            job = cron_tab.new(
                command=command,
                comment="dagster-schedule: {schedule_origin_id}".format(
                    schedule_origin_id=schedule_origin_id
                ),
            )
            job.setall(external_schedule.cron_schedule)

    def _end_cron_job(self, instance, schedule_origin_id):
        with self.get_cron_tab() as cron_tab:
            cron_tab.remove_all(comment=self._cron_tag_for_schedule(schedule_origin_id))

        script_file = self._get_bash_script_file_path(instance, schedule_origin_id)
        if os.path.isfile(script_file):
            os.remove(script_file)

    def running_schedule_count(self, instance, schedule_origin_id):
        matching_jobs = self.get_cron_tab().find_comment(
            self._cron_tag_for_schedule(schedule_origin_id)
        )

        return len(list(matching_jobs))

    def _get_or_create_logs_directory(self, instance, schedule_origin_id):
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        logs_directory = os.path.join(instance.schedules_directory(), "logs", schedule_origin_id)
        if not os.path.isdir(logs_directory):
            utils.mkdir_p(logs_directory)

        return logs_directory

    def get_logs_path(self, instance, schedule_origin_id):
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        logs_directory = self._get_or_create_logs_directory(instance, schedule_origin_id)
        return os.path.join(logs_directory, "scheduler.log")

    def _write_bash_script_to_file(self, instance, external_schedule):
        # Get path to store bash script
        schedule_origin_id = external_schedule.get_external_origin_id()
        script_file = self._get_bash_script_file_path(instance, schedule_origin_id)

        # Get path to store schedule attempt logs
        logs_directory = self._get_or_create_logs_directory(instance, schedule_origin_id)
        schedule_log_file_name = "{}_{}.result".format("${RUN_DATE}", schedule_origin_id)
        schedule_log_file_path = os.path.join(logs_directory, schedule_log_file_name)

        local_target = external_schedule.get_external_origin()

        # Environment information needed for execution
        dagster_home = os.getenv("DAGSTER_HOME")

        override_system_timezone = get_mocked_system_timezone()

        script_contents = """
            #!/bin/bash
            export DAGSTER_HOME={dagster_home}
            export LANG=en_US.UTF-8
            {env_vars}

            export RUN_DATE=$(date "+%Y%m%dT%H%M%S")

            {python_exe} -m dagster api launch_scheduled_execution --schedule_name {schedule_name} {repo_cli_args} {override_timezone_args} "{result_file}"
        """.format(
            python_exe=sys.executable,
            schedule_name=external_schedule.name,
            repo_cli_args=local_target.get_repo_cli_args(),
            override_timezone_args=(
                f"--override-system-timezone={override_system_timezone}"
                if override_system_timezone
                else ""
            ),
            result_file=schedule_log_file_path,
            dagster_home=dagster_home,
            env_vars="\n".join(
                [
                    "export {key}={value}".format(key=key, value=value)
                    for key, value in external_schedule.environment_vars.items()
                ]
            ),
        )

        with io.open(script_file, "w", encoding="utf-8") as f:
            f.write(script_contents)

        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

        return script_file

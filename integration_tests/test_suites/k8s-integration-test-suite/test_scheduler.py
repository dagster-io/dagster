import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager

import kubernetes
import pytest
from dagster import DagsterInstance, ScheduleDefinition
from dagster.core.definitions import lambda_solid, pipeline, repository
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.scheduler.job import JobStatus, JobType
from dagster.core.scheduler.scheduler import (
    DagsterScheduleDoesNotExist,
    DagsterScheduleReconciliationError,
    DagsterSchedulerError,
)
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import environ
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from marks import mark_scheduler


@pytest.fixture(scope="function")
def unset_dagster_home():
    old_env = os.getenv("DAGSTER_HOME")
    if old_env is not None:
        del os.environ["DAGSTER_HOME"]
    yield
    if old_env is not None:
        os.environ["DAGSTER_HOME"] = old_env


@pipeline
def no_config_pipeline():
    @lambda_solid
    def return_hello():
        return "Hello"

    return return_hello()


schedules_dict = {
    "no_config_pipeline_daily_schedule": ScheduleDefinition(
        name="no_config_pipeline_daily_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        run_config={"storage": {"filesystem": None}},
    ),
    "no_config_pipeline_every_min_schedule": ScheduleDefinition(
        name="no_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
        run_config={"storage": {"filesystem": None}},
    ),
    "default_config_pipeline_every_min_schedule": ScheduleDefinition(
        name="default_config_pipeline_every_min_schedule",
        cron_schedule="* * * * *",
        pipeline_name="no_config_pipeline",
    ),
}


def define_schedules():
    return list(schedules_dict.values())


@repository
def test_repository():
    if os.getenv("DAGSTER_TEST_SMALL_REPO"):
        return [no_config_pipeline] + list(
            filter(
                lambda x: not x.name == "default_config_pipeline_every_min_schedule",
                define_schedules(),
            )
        )

    return [no_config_pipeline] + define_schedules()


@contextmanager
def get_test_external_repo():
    with RepositoryLocationHandle.create_from_repository_location_origin(
        ManagedGrpcPythonEnvRepositoryLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=__file__,
                attribute="test_repository",
            ),
            location_name="test_location",
        ),
    ) as handle:
        yield RepositoryLocation.from_handle(handle).get_repository("test_repository")


@contextmanager
def get_smaller_external_repo():
    with environ({"DAGSTER_TEST_SMALL_REPO": "1"}):
        with get_test_external_repo() as repo:
            yield repo


@mark_scheduler
def test_init(
    dagster_instance_with_k8s_scheduler,
    schedule_tempdir,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler

    with get_test_external_repo() as external_repository:
        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repository)

        # Check schedules are saved to disk
        assert "schedules" in os.listdir(schedule_tempdir)

        assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3

        schedules = instance.all_stored_job_state(job_type=JobType.SCHEDULE)
        for schedule in schedules:
            assert schedule.status == JobStatus.STOPPED


@mark_scheduler
def test_re_init(
    dagster_instance_with_k8s_scheduler,
    schedule_tempdir,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        # Start schedule
        schedule_state = instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )

        # Re-initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        # Check schedules are saved to disk
        assert "schedules" in os.listdir(schedule_tempdir)

        schedule_states = instance.all_stored_job_state(job_type=JobType.SCHEDULE)

        for state in schedule_states:
            assert state.job_specific_data.scheduler == "K8sScheduler"
            if state.name == "no_config_pipeline_every_min_schedule":
                assert state == schedule_state


@mark_scheduler
def test_start_and_stop_schedule(
    dagster_instance_with_k8s_scheduler,
    schedule_tempdir,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        schedule = external_repo.get_external_schedule(
            schedule_name="no_config_pipeline_every_min_schedule"
        )
        schedule_origin_id = schedule.get_external_origin_id()

        instance.start_schedule_and_update_storage_state(external_schedule=schedule)

        assert "schedules" in os.listdir(schedule_tempdir)

        assert instance.scheduler.get_cron_job(schedule_origin_id=schedule_origin_id)

        instance.stop_schedule_and_update_storage_state(schedule_origin_id=schedule_origin_id)
        assert not instance.scheduler.get_cron_job(schedule_origin_id=schedule_origin_id)


@mark_scheduler
def test_start_non_existent_schedule(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with pytest.raises(DagsterScheduleDoesNotExist):
        # Initialize scheduler
        instance.stop_schedule_and_update_storage_state("asdf")


@mark_scheduler
def test_start_schedule_cron_job(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_daily_schedule")
        )
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("default_config_pipeline_every_min_schedule")
        )

        # Inspect the cron tab
        cron_jobs = instance.scheduler.get_all_cron_jobs()

        assert len(cron_jobs) == 3

        external_schedules_dict = {
            external_repo.get_external_schedule(name).get_external_origin_id(): schedule_def
            for name, schedule_def in schedules_dict.items()
        }

        for cron_job in cron_jobs:
            cron_schedule = cron_job.spec.schedule
            command = cron_job.spec.job_template.spec.template.spec.containers[0].command
            args = cron_job.spec.job_template.spec.template.spec.containers[0].args
            schedule_origin_id = cron_job.metadata.name

            schedule_def = external_schedules_dict[schedule_origin_id]
            assert cron_schedule == schedule_def.cron_schedule
            assert command == None
            assert args[:5] == [
                "dagster",
                "api",
                "launch_scheduled_execution",
                "/tmp/launch_scheduled_execution_output",
                "--schedule_name",
            ]


@mark_scheduler
def test_remove_schedule_def(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3

        with get_smaller_external_repo() as smaller_repo:
            instance.reconcile_scheduler_state(smaller_repo)

            assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 2


@mark_scheduler
def test_add_schedule_def(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:
        with get_smaller_external_repo() as smaller_repo:
            # Initialize scheduler
            instance.reconcile_scheduler_state(smaller_repo)

        # Start all schedule and verify cron tab, schedule storage, and errors
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_daily_schedule")
        )
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )

        assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 2
        assert len(instance.scheduler.get_all_cron_jobs()) == 2
        assert len(instance.scheduler_debug_info().errors) == 0

        # Reconcile with an additional schedule added
        instance.reconcile_scheduler_state(external_repo)

        assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3
        assert len(instance.scheduler.get_all_cron_jobs()) == 2
        assert len(instance.scheduler_debug_info().errors) == 0

        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("default_config_pipeline_every_min_schedule")
        )

        assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3
        assert len(instance.scheduler.get_all_cron_jobs()) == 3
        assert len(instance.scheduler_debug_info().errors) == 0


@mark_scheduler
def test_start_and_stop_schedule_cron_tab(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:
        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        # Start schedule
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 1

        # Try starting it again
        with pytest.raises(DagsterSchedulerError):
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 1

        # Start another schedule
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_daily_schedule")
        )
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 2

        # Stop second schedule
        instance.stop_schedule_and_update_storage_state(
            external_repo.get_external_schedule(
                "no_config_pipeline_daily_schedule"
            ).get_external_origin_id()
        )
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 1

        # Try stopping second schedule again
        instance.stop_schedule_and_update_storage_state(
            external_repo.get_external_schedule(
                "no_config_pipeline_daily_schedule"
            ).get_external_origin_id()
        )
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 1

        # Start second schedule
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_daily_schedule")
        )
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 2

        # Reconcile schedule state, should be in the same state
        instance.reconcile_scheduler_state(external_repo)
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 2

        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("default_config_pipeline_every_min_schedule")
        )
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 3

        # Reconcile schedule state, should be in the same state
        instance.reconcile_scheduler_state(external_repo)
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 3

        # Stop all schedules
        instance.stop_schedule_and_update_storage_state(
            external_repo.get_external_schedule(
                "no_config_pipeline_every_min_schedule"
            ).get_external_origin_id()
        )
        instance.stop_schedule_and_update_storage_state(
            external_repo.get_external_schedule(
                "no_config_pipeline_daily_schedule"
            ).get_external_origin_id()
        )
        instance.stop_schedule_and_update_storage_state(
            external_repo.get_external_schedule(
                "default_config_pipeline_every_min_schedule"
            ).get_external_origin_id()
        )

        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 0

        # Reconcile schedule state, should be in the same state
        instance.reconcile_scheduler_state(external_repo)
        cron_jobs = instance.scheduler.get_all_cron_jobs()
        assert len(cron_jobs) == 0


@mark_scheduler
def test_script_execution(
    dagster_instance_with_k8s_scheduler,
    unset_dagster_home,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument,redefined-outer-name
    with tempfile.TemporaryDirectory() as tempdir:
        with environ({"DAGSTER_HOME": tempdir}):
            local_instance = DagsterInstance.get()

            with get_test_external_repo() as external_repo:
                # Initialize scheduler
                dagster_instance_with_k8s_scheduler.reconcile_scheduler_state(external_repo)
                dagster_instance_with_k8s_scheduler.start_schedule_and_update_storage_state(
                    external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
                )

                local_runs = local_instance.get_runs()
                assert len(local_runs) == 0

                cron_job_name = external_repo.get_external_schedule(
                    "no_config_pipeline_every_min_schedule"
                ).get_external_origin_id()

                batch_v1beta1_api = kubernetes.client.BatchV1beta1Api()
                cron_job = batch_v1beta1_api.read_namespaced_cron_job(
                    cron_job_name, helm_namespace_for_k8s_run_launcher
                )
                container = cron_job.spec.job_template.spec.template.spec.containers[0]
                args = container.args
                cli_cmd = [sys.executable, "-m"] + args

                p = subprocess.Popen(
                    cli_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={
                        "DAGSTER_HOME": tempdir,
                        "LC_ALL": "C.UTF-8",
                        "LANG": "C.UTF-8",
                    },  # https://stackoverflow.com/questions/36651680/click-will-abort-further-execution-because-python-3-was-configured-to-use-ascii
                )
                stdout, stderr = p.communicate()
                print("Command completed with stdout: ", stdout)  # pylint: disable=print-call
                print("Command completed with stderr: ", stderr)  # pylint: disable=print-call
                assert p.returncode == 0

                local_runs = local_instance.get_runs()
                assert len(local_runs) == 1

                run_id = local_runs[0].run_id

                pipeline_run = local_instance.get_run_by_id(run_id)
                assert pipeline_run
                assert pipeline_run.status == PipelineRunStatus.SUCCESS


@mark_scheduler
def test_start_schedule_fails(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        def raises(*args, **kwargs):
            raise Exception("Patch")

        instance._scheduler._api.create_namespaced_cron_job = (  # pylint: disable=protected-access
            raises
        )
        with pytest.raises(Exception, match="Patch"):
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )

        schedule = instance.get_job_state(
            external_repo.get_external_schedule(
                "no_config_pipeline_every_min_schedule"
            ).get_external_origin_id()
        )

        assert schedule.status == JobStatus.STOPPED


@mark_scheduler
def test_start_schedule_unsuccessful(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        def do_nothing(**_):
            pass

        instance._scheduler._api.create_namespaced_cron_job = (  # pylint: disable=protected-access
            do_nothing
        )

        # Start schedule
        with pytest.raises(
            DagsterSchedulerError,
            match="Attempted to add K8s CronJob for schedule no_config_pipeline_every_min_schedule, "
            "but failed. The schedule no_config_pipeline_every_min_schedule is not running.",
        ):
            instance.start_schedule_and_update_storage_state(
                external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
            )


@mark_scheduler
def test_start_schedule_manual_delete_debug(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )

        instance.scheduler.get_all_cron_jobs()

        # Manually delete the schedule
        instance.scheduler._end_cron_job(  # pylint: disable=protected-access
            external_repo.get_external_schedule(
                "no_config_pipeline_every_min_schedule"
            ).get_external_origin_id(),
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        instance.reconcile_scheduler_state(external_repo)
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


@mark_scheduler
def test_start_schedule_manual_add_debug(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        # Manually add the schedule from to the crontab
        instance.scheduler._start_cron_job(  # pylint: disable=protected-access
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )

        # Check debug command
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 1

        # Reconcile should fix error
        instance.reconcile_scheduler_state(external_repo)
        debug_info = instance.scheduler_debug_info()
        assert len(debug_info.errors) == 0


@mark_scheduler
def test_stop_schedule_fails(
    dagster_instance_with_k8s_scheduler,
    schedule_tempdir,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        external_schedule = external_repo.get_external_schedule(
            "no_config_pipeline_every_min_schedule"
        )
        schedule_origin_id = external_schedule.get_external_origin_id()

        def raises(*args, **kwargs):
            raise Exception("Patch")

        instance._scheduler._end_cron_job = raises  # pylint: disable=protected-access

        instance.start_schedule_and_update_storage_state(external_schedule)

        assert "schedules" in os.listdir(schedule_tempdir)

        # End schedule
        with pytest.raises(Exception, match="Patch"):
            instance.stop_schedule_and_update_storage_state(schedule_origin_id)

        schedule = instance.get_job_state(schedule_origin_id)

        assert schedule.status == JobStatus.RUNNING


@mark_scheduler
def test_stop_schedule_unsuccessful(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        def do_nothing(**_):
            pass

        instance._scheduler._end_cron_job = do_nothing  # pylint: disable=protected-access

        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )

        # End schedule
        with pytest.raises(
            DagsterSchedulerError,
            match="Attempted to remove existing K8s CronJob for schedule "
            "no_config_pipeline_every_min_schedule, but failed. Schedule is still running.",
        ):
            instance.stop_schedule_and_update_storage_state(
                external_repo.get_external_schedule(
                    "no_config_pipeline_every_min_schedule"
                ).get_external_origin_id()
            )


@mark_scheduler
def test_wipe(
    dagster_instance_with_k8s_scheduler, helm_namespace_for_k8s_run_launcher, restore_k8s_cron_tab
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        # Start schedule
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )

        # Wipe scheduler
        instance.wipe_all_schedules()

        # Check schedules are wiped
        assert instance.all_stored_job_state(job_type=JobType.SCHEDULE) == []


@mark_scheduler
def test_reconcile_failure(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        instance.reconcile_scheduler_state(external_repo)
        instance.start_schedule_and_update_storage_state(
            external_repo.get_external_schedule("no_config_pipeline_every_min_schedule")
        )

        def failed_start_job(*_):
            raise DagsterSchedulerError("Failed to start")

        def failed_refresh_job(*_):
            raise DagsterSchedulerError("Failed to refresh")

        def failed_end_job(*_):
            raise DagsterSchedulerError("Failed to stop")

        instance._scheduler.start_schedule = failed_start_job  # pylint: disable=protected-access
        instance._scheduler.refresh_schedule = (  # pylint: disable=protected-access
            failed_refresh_job
        )
        instance._scheduler.stop_schedule = failed_end_job  # pylint: disable=protected-access

        with pytest.raises(
            DagsterScheduleReconciliationError,
            match="Error 1: Failed to stop\n    Error 2: Failed to stop\n    Error 3: Failed to refresh",
        ):
            instance.reconcile_scheduler_state(external_repo)


@mark_scheduler
def test_reconcile_failure_when_deleting_schedule_def(
    dagster_instance_with_k8s_scheduler,
    helm_namespace_for_k8s_run_launcher,
    restore_k8s_cron_tab,
):  # pylint:disable=unused-argument
    instance = dagster_instance_with_k8s_scheduler
    with get_test_external_repo() as external_repo:

        # Initialize scheduler
        instance.reconcile_scheduler_state(external_repo)

        assert len(instance.all_stored_job_state(job_type=JobType.SCHEDULE)) == 3

        def failed_end_job(*_):
            raise DagsterSchedulerError("Failed to stop")

        instance._scheduler.stop_schedule_and_delete_from_storage = (  # pylint: disable=protected-access
            failed_end_job
        )

        with pytest.raises(
            DagsterScheduleReconciliationError,
            match="Error 1: Failed to stop",
        ):
            with get_smaller_external_repo() as smaller_repo:
                instance.reconcile_scheduler_state(smaller_repo)

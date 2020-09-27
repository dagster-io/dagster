import os
import time

from dagster import file_relative_path, pipeline, repository, solid
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.repository_location import InProcessRepositoryLocation
from dagster.core.launcher import CliApiRunLauncher
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test, poll_for_finished_run, poll_for_step_start


@solid
def noop_solid(_):
    pass


@pipeline
def noop_pipeline():
    pass


@solid
def crashy_solid(_):
    os._exit(1)  # pylint: disable=W0212


@pipeline
def crashy_pipeline():
    crashy_solid()


@solid
def sleepy_solid(_):
    while True:
        time.sleep(0.1)


@pipeline
def sleepy_pipeline():
    sleepy_solid()


@solid
def return_one(_):
    return 1


@solid
def multiply_by_2(_, num):
    return num * 2


@solid
def multiply_by_3(_, num):
    return num * 3


@solid
def add(_, num1, num2):
    return num1 + num2


@pipeline
def math_diamond():
    one = return_one()
    add(multiply_by_2(one), multiply_by_3(one))


@repository
def nope():
    return [noop_pipeline, crashy_pipeline, sleepy_pipeline, math_diamond]


def test_repo_construction():
    repo_yaml = file_relative_path(__file__, "repo.yaml")
    assert ReconstructableRepository.from_legacy_repository_yaml(repo_yaml).get_definition()


def get_full_external_pipeline(repo_yaml, pipeline_name):
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(repo_yaml)
    return (
        InProcessRepositoryLocation(recon_repo)
        .get_repository("nope")
        .get_full_external_pipeline(pipeline_name)
    )


def test_successful_run():
    with instance_for_test() as instance:
        repo_yaml = file_relative_path(__file__, "repo.yaml")
        pipeline_run = instance.create_run_for_pipeline(pipeline_def=noop_pipeline, run_config=None)

        external_pipeline = get_full_external_pipeline(repo_yaml, pipeline_run.pipeline_name)

        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        launcher = instance.run_launcher
        launcher.launch_run(
            instance=instance, run=pipeline_run, external_pipeline=external_pipeline
        )

        pipeline_run = instance.get_run_by_id(run_id)
        assert pipeline_run
        assert pipeline_run.run_id == run_id

        pipeline_run = poll_for_finished_run(instance, run_id, timeout=5)
        assert pipeline_run.status == PipelineRunStatus.SUCCESS


def test_crashy_run():
    with instance_for_test() as instance:
        repo_yaml = file_relative_path(__file__, "repo.yaml")
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=crashy_pipeline, run_config=None
        )
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        external_pipeline = get_full_external_pipeline(repo_yaml, pipeline_run.pipeline_name)

        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)

        failed_pipeline_run = instance.get_run_by_id(run_id)

        assert failed_pipeline_run
        assert failed_pipeline_run.run_id == run_id

        failed_pipeline_run = poll_for_finished_run(instance, run_id, timeout=5)
        assert failed_pipeline_run.status == PipelineRunStatus.FAILURE

        event_records = instance.all_logs(run_id)

        message = "Pipeline execution process for {run_id} unexpectedly exited.".format(
            run_id=run_id
        )

        assert _message_exists(event_records, message)


def test_terminated_run():
    with instance_for_test() as instance:
        repo_yaml = file_relative_path(__file__, "repo.yaml")
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=sleepy_pipeline, run_config=None
        )
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        external_pipeline = get_full_external_pipeline(repo_yaml, pipeline_run.pipeline_name)
        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)

        poll_for_step_start(instance, run_id)

        assert launcher.can_terminate(run_id)
        assert launcher.terminate(run_id)

        # Return false is already terminated
        assert not launcher.terminate(run_id)

        terminated_pipeline_run = poll_for_finished_run(instance, run_id, timeout=2)
        terminated_pipeline_run = instance.get_run_by_id(run_id)
        assert terminated_pipeline_run.status == PipelineRunStatus.FAILURE

        all_logs = instance.all_logs(run_id)

        events = [event.dagster_event.event_type_value for event in all_logs]

        assert events == [
            "ENGINE_EVENT",
            "ENGINE_EVENT",
            "PIPELINE_START",
            "ENGINE_EVENT",
            "STEP_START",
            "ENGINE_EVENT",
            "STEP_FAILURE",
            "PIPELINE_FAILURE",
            "ENGINE_EVENT",
            "ENGINE_EVENT",
            "ENGINE_EVENT",
        ]

        expected_termination_events = [
            "[CliApiRunLauncher] Received pipeline termination request.",
            "[CliApiRunLauncher] Pipeline was terminated successfully.",
            "[DefaultRunLauncher] Pipeline was not terminated since CliApiRunLauncher and GrpcRunLauncher could not find in-progress run.",
        ]

        actual_termination_events = [
            event.dagster_event.message
            for event in all_logs
            if event.dagster_event.message in expected_termination_events
        ]

        assert expected_termination_events == actual_termination_events


def _get_engine_events(event_records):
    for er in event_records:
        if er.dagster_event and er.dagster_event.is_engine_event:
            yield er


def _get_successful_step_keys(event_records):

    step_keys = set()

    for er in event_records:
        if er.dagster_event and er.dagster_event.is_step_success:
            step_keys.add(er.dagster_event.step_key)

    return step_keys


def _message_exists(event_records, message_text):
    for event_record in event_records:
        if message_text in event_record.message:
            return True

    return False


def test_single_solid_selection_execution():
    with instance_for_test() as instance:
        repo_yaml = file_relative_path(__file__, "repo.yaml")

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond, run_config=None, solids_to_execute={"return_one"}
        )
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        external_pipeline = get_full_external_pipeline(repo_yaml, pipeline_run.pipeline_name)

        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)
        launcher.join()
        finished_pipeline_run = instance.get_run_by_id(run_id)

        event_records = instance.all_logs(run_id)

        assert finished_pipeline_run
        assert finished_pipeline_run.run_id == run_id
        assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

        assert _get_successful_step_keys(event_records) == {"return_one.compute"}


def test_multi_solid_selection_execution():
    with instance_for_test() as instance:
        repo_yaml = file_relative_path(__file__, "repo.yaml")

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond,
            run_config=None,
            solids_to_execute={"return_one", "multiply_by_2"},
        )
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        external_pipeline = get_full_external_pipeline(repo_yaml, pipeline_run.pipeline_name)

        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)
        launcher.join()

        finished_pipeline_run = instance.get_run_by_id(run_id)

        event_records = instance.all_logs(run_id)

        assert finished_pipeline_run
        assert finished_pipeline_run.run_id == run_id
        assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

        assert _get_successful_step_keys(event_records) == {
            "return_one.compute",
            "multiply_by_2.compute",
        }


def test_engine_events():

    with instance_for_test() as instance:
        repo_yaml = file_relative_path(__file__, "repo.yaml")

        pipeline_run = instance.create_run_for_pipeline(pipeline_def=math_diamond, run_config=None)
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        external_pipeline = get_full_external_pipeline(repo_yaml, pipeline_run.pipeline_name)
        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)
        launcher.join()

        finished_pipeline_run = instance.get_run_by_id(run_id)

        assert finished_pipeline_run
        assert finished_pipeline_run.run_id == run_id
        assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS
        event_records = instance.all_logs(run_id)

        about_to_start, started_process, executing_steps, finished_steps, process_exited = tuple(
            _get_engine_events(event_records)
        )

        assert "About to start process" in about_to_start.message
        assert "Started process for pipeline" in started_process.message
        assert "Executing steps in process" in executing_steps.message
        assert "Finished steps in process" in finished_steps.message
        assert "Process for pipeline exited" in process_exited.message


def test_not_initialized():
    run_launcher = CliApiRunLauncher()
    run_id = "dummy"

    assert run_launcher.join() is None
    assert run_launcher.is_process_running(run_id) is False
    assert run_launcher.can_terminate(run_id) is False
    assert run_launcher.terminate(run_id) is False
    assert run_launcher.get_active_run_count() == 0
    assert run_launcher.is_active(run_id) is False

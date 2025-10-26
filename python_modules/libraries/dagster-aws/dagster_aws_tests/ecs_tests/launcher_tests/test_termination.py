from dagster import DagsterRunStatus
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.remote_representation.external import RemoteJob
from dagster._core.test_utils import in_process_test_workspace
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin

from dagster_aws_tests.ecs_tests.launcher_tests import repo


def test_termination(instance, workspace, run):
    instance.launch_run(run.run_id, workspace)

    assert instance.run_launcher.terminate(run.run_id)

    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.CANCELING

    assert not instance.run_launcher.terminate(run.run_id)


def test_termination_xregion(
    instance_regional, workspace, job: JobDefinition, remote_job: RemoteJob, image: str, xregion
):
    instance = instance_regional
    run = instance.create_run_for_job(
        job,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
        tags={"region": xregion},
    )
    workspace = in_process_test_workspace(
        instance,
        loadable_target_origin=LoadableTargetOrigin(
            python_file=repo.__file__,
            attribute=repo.repository.name,
        ),
        container_image=image,
    )
    instance.launch_run(run.run_id, workspace)

    assert instance.run_launcher.terminate(run.run_id)

    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.CANCELING

    assert not instance.run_launcher.terminate(run.run_id)


def test_missing_run(instance, workspace, run, monkeypatch):
    instance.launch_run(run.run_id, workspace)

    def missing_run(*_args, **_kwargs):
        return None

    original = instance.get_run_by_id

    monkeypatch.setattr(instance, "get_run_by_id", missing_run)
    assert not instance.run_launcher.terminate(run.run_id)

    monkeypatch.setattr(instance, "get_run_by_id", original)
    assert instance.run_launcher.terminate(run.run_id)


def test_missing_tag(instance, workspace, run):
    instance.launch_run(run.run_id, workspace)
    original = instance.get_run_by_id(run.run_id).tags

    instance.add_run_tags(run.run_id, {"ecs/task_arn": ""})
    assert not instance.run_launcher.terminate(run.run_id)

    # Still moves to CANCELING
    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.CANCELING

    instance.add_run_tags(run.run_id, original)
    instance.add_run_tags(run.run_id, {"ecs/cluster": ""})
    assert not instance.run_launcher.terminate(run.run_id)

    instance.add_run_tags(run.run_id, original)
    assert instance.run_launcher.terminate(run.run_id)


def test_eventual_consistency(instance, workspace, run, monkeypatch):
    instance.launch_run(run.run_id, workspace)

    def empty(*_args, **_kwargs):
        return {"tasks": []}

    original = instance.run_launcher.ecs.describe_tasks

    monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", empty)
    assert not instance.run_launcher.terminate(run.run_id)

    monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", original)
    assert instance.run_launcher.terminate(run.run_id)

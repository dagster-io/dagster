# pylint: disable=redefined-outer-name, protected-access
import pytest
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.origin import InProcessRepositoryLocationOrigin
from dagster.core.test_utils import instance_for_test

from . import repo


@pytest.fixture
def task_definition(ecs):
    return ecs.register_task_definition(
        family="dagster",
        containerDefinitions=[{"name": "dagster", "image": "dagster:latest"}],
        networkMode="awsvpc",
    )["taskDefinition"]


@pytest.fixture
def task(ecs, task_definition):
    return ecs.run_task(
        taskDefinition=task_definition["family"],
        networkConfiguration={"awsvpcConfiguration": {"subnets": ["subnet-12345"]}},
    )["tasks"][0]


@pytest.fixture
def instance(ecs, task, task_definition, monkeypatch, requests_mock):
    container_uri = "http://metadata_host"
    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI_V4", container_uri)
    container = task["containers"][0]["name"]
    requests_mock.get(container_uri, json={"Name": container})

    task_uri = container_uri + "/task"
    requests_mock.get(
        task_uri,
        json={
            "Cluster": task["clusterArn"],
            "TaskARN": task["taskArn"],
            "Family": task_definition["family"],
        },
    )
    overrides = {"run_launcher": {"module": "dagster_aws.ecs", "class": "EcsRunLauncher"}}
    with instance_for_test(overrides) as instance:
        monkeypatch.setattr(instance.run_launcher, "ecs", ecs)
        yield instance


@pytest.fixture
def pipeline():
    return repo.pipeline


@pytest.fixture
def external_pipeline():
    with InProcessRepositoryLocationOrigin(
        ReconstructableRepository.for_file(repo.__file__, repo.repository.__name__),
    ).create_location() as location:
        yield location.get_repository(repo.repository.__name__).get_full_external_pipeline(
            repo.pipeline.__name__
        )


@pytest.fixture
def run_id(instance, pipeline):
    return instance.create_run_for_pipeline(pipeline).run_id


def test_launching(ecs, instance, run_id, external_pipeline):
    assert not instance.run_launcher._get_task_arn_by_run_id_tag(run_id)

    instance.launch_run(run_id, external_pipeline)

    task_arn = instance.run_launcher._get_task_arn_by_run_id_tag(run_id)
    task = ecs.describe_tasks(tasks=[task_arn])
    assert "execute_run" in task["tasks"][0]["overrides"]["containerOverrides"][0]["command"]


def test_termination(instance, run_id, external_pipeline):
    assert not instance.run_launcher.can_terminate(run_id)

    instance.launch_run(run_id, external_pipeline)

    assert instance.run_launcher.can_terminate(run_id)
    assert instance.run_launcher.terminate(run_id)
    assert not instance.run_launcher.terminate(run_id)

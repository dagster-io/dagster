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
def task(ecs, network_interface, security_group, task_definition):
    return ecs.run_task(
        taskDefinition=task_definition["family"],
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": [network_interface.subnet_id],
                "securityGroups": [security_group.id],
            },
        },
    )["tasks"][0]


@pytest.fixture
def instance(ecs, ec2, task, task_definition, monkeypatch, requests_mock):
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
        monkeypatch.setattr(instance.run_launcher, "ec2", ec2)
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
def run(instance, pipeline):
    return instance.create_run_for_pipeline(pipeline)


def test_launching(ecs, instance, run, external_pipeline, subnet, network_interface):
    assert not run.tags
    initial_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, external_pipeline)

    # A new task is launched
    tasks = ecs.list_tasks()["taskArns"]
    assert len(tasks) == len(initial_tasks) + 1
    task_arn = list(set(tasks).difference(initial_tasks))[0]

    # The run is tagged with info about the ECS task
    assert instance.get_run_by_id(run.run_id).tags["ecs/task_arn"] == task_arn
    assert instance.get_run_by_id(run.run_id).tags["ecs/cluster"] == ecs._cluster_arn("default")

    # And the ECS task is tagged with info about the Dagster run
    assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["key"] == "dagster/run_id"
    assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["value"] == run.run_id

    # We override the command to run our pipeline
    task = ecs.describe_tasks(tasks=[task_arn])
    assert subnet.id in str(task)
    assert network_interface.id in str(task)
    assert "execute_run" in task["tasks"][0]["overrides"]["containerOverrides"][0]["command"]


def test_termination(instance, run, external_pipeline):
    assert not instance.run_launcher.can_terminate(run.run_id)

    instance.launch_run(run.run_id, external_pipeline)

    assert instance.run_launcher.can_terminate(run.run_id)
    assert instance.run_launcher.terminate(run.run_id)
    assert not instance.run_launcher.can_terminate(run.run_id)
    assert not instance.run_launcher.terminate(run.run_id)

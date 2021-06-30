# pylint: disable=redefined-outer-name, protected-access, unused-argument
import boto3
import pytest
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.origin import InProcessRepositoryLocationOrigin
from dagster.core.test_utils import instance_for_test

from . import repo


@pytest.fixture
def image():
    return "dagster:latest"


@pytest.fixture
def environment():
    return [{"name": "FOO", "value": "bar"}]


@pytest.fixture
def task_definition(ecs, image, environment):
    return ecs.register_task_definition(
        family="dagster",
        containerDefinitions=[
            {
                "name": "dagster",
                "image": image,
                "environment": environment,
            }
        ],
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
def stub_aws(ecs, ec2, monkeypatch):
    # Any call to boto3.client() will return ecs.
    # Any call to boto3.resource() will return ec2.
    # This only works because our launcher happens to use a client for ecs and
    # a resource for ec2 - if that were to change or if new aws objects were to
    # be introduced, this fixture would need to be refactored.
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: ecs)
    monkeypatch.setattr(boto3, "resource", lambda *args, **kwargs: ec2)


@pytest.fixture
def instance(stub_aws, task, monkeypatch, requests_mock):
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
        },
    )
    overrides = {"run_launcher": {"module": "dagster_aws.ecs", "class": "EcsRunLauncher"}}
    with instance_for_test(overrides) as instance:
        yield instance


@pytest.fixture
def pipeline():
    return repo.pipeline


@pytest.fixture
def external_pipeline(image):
    with InProcessRepositoryLocationOrigin(
        ReconstructableRepository.for_file(
            repo.__file__, repo.repository.__name__, container_image=image
        ),
    ).create_location() as location:
        yield location.get_repository(repo.repository.__name__).get_full_external_pipeline(
            repo.pipeline.__name__
        )


@pytest.fixture
def run(instance, pipeline):
    return instance.create_run_for_pipeline(pipeline)


def test_launching(
    ecs, instance, run, external_pipeline, subnet, network_interface, image, environment
):
    assert not run.tags
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    initial_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, external_pipeline)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It has a new family, name, and image
    assert task_definition["family"] == "dagster-run"
    assert len(task_definition["containerDefinitions"]) == 1
    container_definition = task_definition["containerDefinitions"][0]
    assert container_definition["name"] == "run"
    assert container_definition["image"] == image
    # But other stuff is inhereted from the parent task definition
    assert container_definition["environment"] == environment

    # A new task is launched
    tasks = ecs.list_tasks()["taskArns"]
    assert len(tasks) == len(initial_tasks) + 1
    task_arn = list(set(tasks).difference(initial_tasks))[0]
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
    assert subnet.id in str(task)
    assert network_interface.id in str(task)
    assert task["taskDefinitionArn"] == task_definition["taskDefinitionArn"]

    # The run is tagged with info about the ECS task
    assert instance.get_run_by_id(run.run_id).tags["ecs/task_arn"] == task_arn
    assert instance.get_run_by_id(run.run_id).tags["ecs/cluster"] == ecs._cluster_arn("default")

    # And the ECS task is tagged with info about the Dagster run
    assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["key"] == "dagster/run_id"
    assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["value"] == run.run_id

    # We set pipeline-specific overides
    overrides = task["overrides"]["containerOverrides"]
    assert len(overrides) == 1
    override = overrides[0]
    assert override["name"] == "run"
    assert "execute_run" in override["command"]
    assert run.run_id in str(override["command"])


def test_termination(instance, run, external_pipeline):
    assert not instance.run_launcher.can_terminate(run.run_id)

    instance.launch_run(run.run_id, external_pipeline)

    assert instance.run_launcher.can_terminate(run.run_id)
    assert instance.run_launcher.terminate(run.run_id)
    assert not instance.run_launcher.can_terminate(run.run_id)
    assert not instance.run_launcher.terminate(run.run_id)

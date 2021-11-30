# pylint: disable=redefined-outer-name, unused-argument
import warnings
from contextlib import contextmanager

import boto3
import pytest
from dagster import ExperimentalWarning
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.test_utils import in_process_test_workspace, instance_for_test

from . import repo


@pytest.fixture(autouse=True)
def ignore_experimental_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ExperimentalWarning)
        yield


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
            {"name": "dagster", "image": image, "environment": environment, "entryPoint": ["ls"]}
        ],
        networkMode="awsvpc",
        memory="512",
        cpu="256",
    )["taskDefinition"]


@pytest.fixture
def assign_public_ip():
    return True


@pytest.fixture
def task(ecs, subnet, security_group, task_definition, assign_public_ip):
    return ecs.run_task(
        taskDefinition=task_definition["family"],
        networkConfiguration={
            "awsvpcConfiguration": {
                "assignPublicIp": "ENABLED" if assign_public_ip else "DISABLED",
                "subnets": [subnet.id],
                "securityGroups": [security_group.id],
            },
        },
    )["tasks"][0]


@pytest.fixture
def stub_aws(ecs, ec2, secrets_manager, monkeypatch):
    def mock_client(*args, **kwargs):
        if "ecs" in args:
            return ecs
        if "secretsmanager" in args:
            return secrets_manager

    monkeypatch.setattr(boto3, "client", mock_client)
    monkeypatch.setattr(boto3, "resource", lambda *args, **kwargs: ec2)


@pytest.fixture
def stub_ecs_metadata(task, monkeypatch, requests_mock):
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


@pytest.fixture
def instance_cm(stub_aws, stub_ecs_metadata):
    @contextmanager
    def cm(config=None):
        overrides = {
            "run_launcher": {
                "module": "dagster_aws.ecs",
                "class": "EcsRunLauncher",
                "config": {**(config or {})},
            }
        }
        with instance_for_test(overrides) as dagster_instance:
            yield dagster_instance

    return cm


@pytest.fixture
def instance(instance_cm):
    with instance_cm() as dagster_instance:
        yield dagster_instance


@pytest.fixture
def pipeline():
    return repo.pipeline


@pytest.fixture
def external_pipeline(workspace):
    location = workspace.get_repository_location(workspace.repository_location_names[0])
    return location.get_repository(repo.repository.__name__).get_full_external_pipeline(
        repo.pipeline.__name__
    )


@pytest.fixture
def workspace(instance, image):
    with in_process_test_workspace(
        instance,
        ReconstructableRepository.for_file(
            repo.__file__, repo.repository.__name__, container_image=image
        ),
    ) as workspace:
        yield workspace


@pytest.fixture
def run(instance, pipeline, external_pipeline):
    return instance.create_run_for_pipeline(
        pipeline,
        external_pipeline_origin=external_pipeline.get_external_origin(),
        pipeline_code_origin=external_pipeline.get_python_origin(),
    )

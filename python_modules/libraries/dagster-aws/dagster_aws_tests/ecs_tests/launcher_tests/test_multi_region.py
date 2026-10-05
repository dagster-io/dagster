import uuid

import pytest
from dagster import DagsterRunStatus
from dagster._check import CheckError
from dagster._core.launcher.base import WorkerStatus

from dagster_aws.ecs.utils import get_task_definition_family


def _launch_cross_region(instance, workspace, job, remote_job, subnet, security_group):
    """Helper: create a run with cross-region tags, launch it, return (run, task_arn)."""
    run = instance.create_run_for_job(
        job,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    instance.add_run_tags(
        run.run_id,
        {
            "ecs/region": "eu-north-1",
            "ecs/cluster": "my-eu-cluster",
            "ecs/security_groups": security_group.id,
            "ecs/subnets": subnet.id,
        },
    )
    instance.launch_run(run.run_id, workspace)
    task_arn = instance.get_run_by_id(run.run_id).tags["ecs/task_arn"]
    return run, task_arn


def test_multi_region_launch(
    ecs,
    instance,
    workspace,
    job,
    remote_job,
    subnet,
    security_group,
    image,
):
    """UC-1: Cross-region tags override network configuration, cluster, and ECS tags."""
    run = instance.create_run_for_job(
        job,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )

    target_cluster = "my-eu-cluster"
    target_region = "eu-north-1"

    instance.add_run_tags(
        run.run_id,
        {
            "ecs/region": target_region,
            "ecs/cluster": target_cluster,
            "ecs/security_groups": security_group.id,
            "ecs/subnets": subnet.id,
        },
    )

    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    initial_tasks = ecs.list_tasks(cluster=target_cluster)["taskArns"]

    instance.launch_run(run.run_id, workspace)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = next(iter(set(task_definitions).difference(initial_task_definitions)))
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)[
        "taskDefinition"
    ]

    assert task_definition["family"] == get_task_definition_family("run", run.remote_job_origin)
    assert len(task_definition["containerDefinitions"]) == 1
    assert task_definition["containerDefinitions"][0]["image"] == image

    # A new task is launched in the target cluster
    tasks = ecs.list_tasks(cluster=target_cluster)["taskArns"]
    assert len(tasks) == len(initial_tasks) + 1

    task_arn = next(iter(set(tasks).difference(initial_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn], cluster=target_cluster)["tasks"][0]

    # Task uses the target cluster
    assert task["clusterArn"] == ecs._cluster_arn(target_cluster)  # noqa: SLF001

    # Network config uses the provided subnet
    assert subnet.id in str(task)

    # The ECS task has a region tag
    task_tags = ecs.list_tags_for_resource(resourceArn=task_arn)["tags"]
    region_tags = [t for t in task_tags if t["key"] == "region"]
    assert len(region_tags) == 1
    assert region_tags[0]["value"] == target_region

    # Run tags are updated with the task ARN and cluster
    updated_run = instance.get_run_by_id(run.run_id)
    assert updated_run.tags["ecs/task_arn"] == task_arn

    # Health check works for cross-region task
    assert instance.run_launcher.check_run_worker_health(run).status == WorkerStatus.RUNNING

    # Termination works for cross-region task
    assert instance.run_launcher.terminate(run.run_id)


def test_cross_region_cluster_name_matches_arn(
    ecs,
    instance,
    workspace,
    job,
    remote_job,
    subnet,
    security_group,
):
    """Plain cluster name in tag should not warn when AWS returns the full ARN."""
    run = instance.create_run_for_job(
        job,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    # Use a plain cluster name -- AWS will return the full ARN
    instance.add_run_tags(
        run.run_id,
        {
            "ecs/region": "eu-north-1",
            "ecs/cluster": "my-eu-cluster",
            "ecs/security_groups": security_group.id,
            "ecs/subnets": subnet.id,
        },
    )

    import warnings as _warnings

    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        instance.launch_run(run.run_id, workspace)

    cluster_warnings = [w for w in caught if "does not match run tag cluster" in str(w.message)]
    assert len(cluster_warnings) == 0, f"Unexpected warning: {cluster_warnings}"


@pytest.mark.parametrize(
    "missing_tag",
    [
        pytest.param("ecs/cluster", id="missing_cluster"),
        pytest.param("ecs/security_groups", id="missing_security_groups"),
        pytest.param("ecs/subnets", id="missing_subnets"),
    ],
)
def test_cross_region_tag_validation(
    instance,
    workspace,
    job,
    remote_job,
    subnet,
    security_group,
    missing_tag,
):
    """UC-2: Setting ecs/region without a required companion tag raises CheckError."""
    all_tags = {
        "ecs/region": "eu-north-1",
        "ecs/cluster": "my-eu-cluster",
        "ecs/security_groups": security_group.id,
        "ecs/subnets": subnet.id,
    }
    # Remove the tag under test
    del all_tags[missing_tag]

    run = instance.create_run_for_job(
        job,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    instance.add_run_tags(run.run_id, all_tags)

    with pytest.raises(CheckError, match=missing_tag):
        instance.launch_run(run.run_id, workspace)


def test_cross_region_termination(
    ecs,
    instance,
    workspace,
    job,
    remote_job,
    subnet,
    security_group,
):
    """UC-3: terminate() stops a cross-region task using the region-specific client."""
    run, task_arn = _launch_cross_region(
        instance, workspace, job, remote_job, subnet, security_group
    )

    # Task is running in the target cluster
    target_cluster = "my-eu-cluster"
    task = ecs.describe_tasks(tasks=[task_arn], cluster=target_cluster)["tasks"][0]
    assert task["lastStatus"] == "RUNNING"

    # Terminate succeeds
    assert instance.run_launcher.terminate(run.run_id)
    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.CANCELING

    # Task is now stopped -- second terminate returns False
    assert not instance.run_launcher.terminate(run.run_id)


def test_cross_region_health_check(
    ecs,
    instance,
    workspace,
    job,
    remote_job,
    subnet,
    security_group,
):
    """UC-4: check_run_worker_health() reports correct status for cross-region tasks."""
    run, task_arn = _launch_cross_region(
        instance, workspace, job, remote_job, subnet, security_group
    )

    # Running task -> RUNNING
    assert instance.run_launcher.check_run_worker_health(run).status == WorkerStatus.RUNNING

    # Stop the task -> FAILED (containers have non-zero exit code by default in stub)
    target_cluster = "my-eu-cluster"
    ecs.stop_task(task=task_arn, cluster=target_cluster)

    health = instance.run_launcher.check_run_worker_health(run)
    assert health.status == WorkerStatus.FAILED


def test_cross_region_docker_image_override(
    ecs,
    instance,
    workspace,
    job,
    remote_job,
    subnet,
    security_group,
    image,
):
    """UC-6: ecs/image + ecs/task_definition_arn clones the base task def with the new image
    and registers it in the target region.
    """
    # Register a base task def with container name matching the launcher ("run")
    base_task_def = ecs.register_task_definition(
        family="base-for-clone",
        containerDefinitions=[
            {"name": "run", "image": image, "environment": []},
        ],
        networkMode="awsvpc",
        memory="512",
        cpu="256",
    )["taskDefinition"]

    override_image = "123456789.dkr.ecr.eu-north-1.amazonaws.com/my-app:latest"
    base_task_def_arn = base_task_def["taskDefinitionArn"]

    run = instance.create_run_for_job(
        job,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    instance.add_run_tags(
        run.run_id,
        {
            "ecs/region": "eu-north-1",
            "ecs/cluster": "my-eu-cluster",
            "ecs/security_groups": security_group.id,
            "ecs/subnets": subnet.id,
            "ecs/image": override_image,
            "ecs/task_definition_arn": base_task_def_arn,
        },
    )

    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    instance.launch_run(run.run_id, workspace)

    # Two new task definitions: the normal run one + the cloned image-override one
    new_task_defs = set(ecs.list_task_definitions()["taskDefinitionArns"]).difference(
        initial_task_definitions
    )
    assert len(new_task_defs) >= 1

    # The cloned task definition has family = "<original>-img-<hash>"
    image_hash = str(uuid.uuid5(uuid.NAMESPACE_URL, override_image)).replace("-", "")[:8]
    expected_family = f"{base_task_def['family']}-img-{image_hash}"

    cloned_def = ecs.describe_task_definition(taskDefinition=expected_family)["taskDefinition"]
    assert cloned_def["family"] == expected_family

    # The run container uses the override image
    container_name = instance.run_launcher.container_name
    run_container = next(
        c for c in cloned_def["containerDefinitions"] if c["name"] == container_name
    )
    assert run_container["image"] == override_image

    # Task launched in target cluster
    target_cluster = "my-eu-cluster"
    updated_run = instance.get_run_by_id(run.run_id)
    task_arn = updated_run.tags["ecs/task_arn"]
    task = ecs.describe_tasks(tasks=[task_arn], cluster=target_cluster)["tasks"][0]
    assert task["clusterArn"] == ecs._cluster_arn(target_cluster)  # noqa: SLF001


@pytest.mark.parametrize(
    "assign_public_ip_tag,expect_public_ip",
    [
        pytest.param("ENABLED", True, id="enabled"),
        pytest.param("DISABLED", False, id="disabled"),
        pytest.param(None, False, id="default_disabled"),
    ],
)
def test_cross_region_public_ip_assignment(
    ecs,
    ec2,
    instance,
    workspace,
    job,
    remote_job,
    subnet,
    security_group,
    assign_public_ip_tag,
    expect_public_ip,
):
    """UC-5: ecs/assign_public_ip controls assignPublicIp in cross-region awsvpcConfiguration."""
    run = instance.create_run_for_job(
        job,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    tags = {
        "ecs/region": "eu-north-1",
        "ecs/cluster": "my-eu-cluster",
        "ecs/security_groups": security_group.id,
        "ecs/subnets": subnet.id,
    }
    if assign_public_ip_tag is not None:
        tags["ecs/assign_public_ip"] = assign_public_ip_tag
    instance.add_run_tags(run.run_id, tags)

    target_cluster = "my-eu-cluster"
    initial_tasks = ecs.list_tasks(cluster=target_cluster)["taskArns"]

    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks(cluster=target_cluster)["taskArns"]
    task_arn = next(iter(set(tasks).difference(initial_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn], cluster=target_cluster)["tasks"][0]

    attachment = task.get("attachments")[0]
    details = dict([(d.get("name"), d.get("value")) for d in attachment["details"]])
    eni = ec2.NetworkInterface(details["networkInterfaceId"])
    attributes = eni.association_attribute or {}

    assert bool(attributes.get("PublicIp")) == expect_public_ip


def test_cross_region_cpu_memory_overrides(
    ecs,
    instance,
    workspace,
    job,
    remote_job,
    subnet,
    security_group,
):
    """UC-7: ecs/cpu and ecs/memory overrides work alongside cross-region tags."""
    run = instance.create_run_for_job(
        job,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    instance.add_run_tags(
        run.run_id,
        {
            "ecs/region": "eu-north-1",
            "ecs/cluster": "my-eu-cluster",
            "ecs/security_groups": security_group.id,
            "ecs/subnets": subnet.id,
            "ecs/cpu": "512",
            "ecs/memory": "1024",
        },
    )

    target_cluster = "my-eu-cluster"
    initial_tasks = ecs.list_tasks(cluster=target_cluster)["taskArns"]

    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks(cluster=target_cluster)["taskArns"]
    task_arn = next(iter(set(tasks).difference(initial_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn], cluster=target_cluster)["tasks"][0]

    # Task is in the target cluster
    assert task["clusterArn"] == ecs._cluster_arn(target_cluster)  # noqa: SLF001

    # CPU/memory overrides applied as strings at task level
    assert task["overrides"]["cpu"] == "512"
    assert task["overrides"]["memory"] == "1024"

    # CPU/memory overrides applied as integers at container level
    container_override = task["overrides"]["containerOverrides"][0]
    assert container_override["cpu"] == 512
    assert container_override["memory"] == 1024


def test_cross_region_cloudwatch_logs_region(
    ecs,
    instance_cm,
    log_group,
    job,
    remote_job,
    subnet,
    security_group,
    image,
):
    """UC-10: awslogs-region is overwritten to the target region and
    awslogs-create-group is set to 'true' for cross-region launches.
    """
    from dagster._core.test_utils import in_process_test_workspace
    from dagster._core.types.loadable_target_origin import LoadableTargetOrigin

    from dagster_aws_tests.ecs_tests.launcher_tests import repo

    with instance_cm({"task_definition": {"log_group": log_group}}) as instance:
        with in_process_test_workspace(
            instance,
            loadable_target_origin=LoadableTargetOrigin(
                python_file=repo.__file__,
                attribute=repo.repository.name,
            ),
            container_image=image,
        ) as workspace:
            remote_job_local = (
                workspace.get_code_location(workspace.code_location_names[0])
                .get_repository(repo.repository.name)
                .get_full_job(repo.job.name)
            )

            run = instance.create_run_for_job(
                job,
                remote_job_origin=remote_job_local.get_remote_origin(),
                job_code_origin=remote_job_local.get_python_origin(),
            )

            target_region = "eu-north-1"
            instance.add_run_tags(
                run.run_id,
                {
                    "ecs/region": target_region,
                    "ecs/cluster": "my-eu-cluster",
                    "ecs/security_groups": security_group.id,
                    "ecs/subnets": subnet.id,
                },
            )

            initial_task_defs = ecs.list_task_definitions()["taskDefinitionArns"]

            instance.launch_run(run.run_id, workspace)

            # Find the newly registered task definition
            new_task_defs = set(ecs.list_task_definitions()["taskDefinitionArns"]).difference(
                initial_task_defs
            )
            assert len(new_task_defs) == 1
            task_def_arn = next(iter(new_task_defs))
            task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)["taskDefinition"]

            # The run container's logConfiguration has the target region
            container_def = next(
                c
                for c in task_def["containerDefinitions"]
                if c["name"] == instance.run_launcher.container_name
            )
            log_config = container_def["logConfiguration"]
            assert log_config["logDriver"] == "awslogs"
            assert log_config["options"]["awslogs-region"] == target_region
            assert log_config["options"]["awslogs-create-group"] == "true"
            assert log_config["options"]["awslogs-group"] == log_group

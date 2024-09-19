import docker
import pytest
from dagster import RetryRequested, job, op
from dagster_docker import docker_container_op, execute_docker_container
from dagster_docker.ops.docker_container_op import _get_container_name


def _get_container_logs(container_name):
    return str(docker.client.from_env().containers.get(container_name).logs())


def test_docker_container_op():
    first_op = docker_container_op.configured(
        {
            "image": "busybox",
            "entrypoint": ["/bin/sh", "-c"],
            "command": ["echo HI"],
        },
        name="first_op",
    )
    second_op = docker_container_op.configured(
        {
            "image": "busybox",
            "entrypoint": ["/bin/sh", "-c"],
            "command": ["echo GOODBYE"],
        },
        name="second_op",
    )

    @job
    def my_full_job():
        second_op(first_op())

    execute_result = my_full_job.execute_in_process()
    assert execute_result.success

    run_id = execute_result.dagster_run.run_id
    container_name = _get_container_name(run_id, first_op.name, 0)
    assert "HI" in _get_container_logs(container_name)

    container_name = _get_container_name(run_id, second_op.name, 0)
    assert "GOODBYE" in _get_container_logs(container_name)


def test_custom_docker_op():
    @op
    def my_custom_op(context):
        execute_docker_container(
            context,
            image="busybox",
            entrypoint=["/bin/sh", "-c"],
            command=["echo HI"],
        )
        return "GOODBYE"

    @op
    def my_second_custom_op(context, what_to_echo: str):
        execute_docker_container(
            context,
            image="busybox",
            entrypoint=["/bin/sh", "-c"],
            command=[f"echo {what_to_echo}"],
        )

    @job
    def my_job_with_custom_ops():
        my_second_custom_op(my_custom_op())

    execute_result = my_job_with_custom_ops.execute_in_process()
    assert execute_result.success

    run_id = execute_result.dagster_run.run_id
    job_name = _get_container_name(run_id, my_custom_op.name, 0)
    assert "HI" in _get_container_logs(job_name)

    job_name = _get_container_name(run_id, my_second_custom_op.name, 0)
    assert "GOODBYE" in _get_container_logs(job_name)


def test_docker_container_op_with_failure():
    failure_op = docker_container_op.configured(
        {
            "image": "busybox",
            "entrypoint": ["/bin/sh", "-c"],
            "command": ["exit 1"],
        },
        name="failure_op",
    )

    @job
    def failure_job():
        failure_op()

    with pytest.raises(Exception, match="Docker container returned exit code 1"):
        failure_job.execute_in_process()


def test_docker_container_op_retries():
    @op
    def fails_sometimes(context):
        execute_docker_container(
            context,
            image="busybox",
            entrypoint=["/bin/sh", "-c"],
            command=[f"echo HERE IS RETRY NUMBER {context.retry_number}"],
        )
        if context.retry_number == 0:
            raise RetryRequested(max_retries=1, seconds_to_wait=1)

    @job
    def fails_sometimes_job():
        fails_sometimes()

    execute_result = fails_sometimes_job.execute_in_process()
    run_id = execute_result.dagster_run.run_id
    container_name = _get_container_name(run_id, fails_sometimes.name, 0)
    assert "HERE IS RETRY NUMBER 0" in _get_container_logs(container_name)

    container_name = _get_container_name(run_id, fails_sometimes.name, 1)

    assert "HERE IS RETRY NUMBER 1" in _get_container_logs(container_name)

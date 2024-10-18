import os
import time
from contextlib import contextmanager

import pytest
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import instance_for_test, poll_for_finished_run
from dagster._daemon.controller import all_daemons_healthy
from dagster._serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess
from dagster._utils.merger import merge_dicts
from dagster._utils.test.postgres_instance import postgres_instance_for_test
from dagster._utils.yaml_utils import load_yaml_from_path
from dagster_aws.utils import ensure_dagster_aws_tests_import
from dagster_test.test_project import (
    ReOriginatedExternalJobForTest,
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_recon_job,
    get_test_project_workspace_and_remote_job,
)

ensure_dagster_aws_tests_import()
from dagster_aws_tests.aws_credential_test_utils import get_aws_creds

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@contextmanager
def docker_postgres_instance(overrides=None, conn_args=None):
    with postgres_instance_for_test(
        __file__,
        "test-postgres-db-docker",
        overrides=overrides,
        conn_args=conn_args,
    ) as instance:
        yield instance


@contextmanager
def start_daemon(timeout=60):
    p = open_ipc_subprocess(["dagster-daemon", "run", "--empty-workspace"])
    try:
        yield
    finally:
        interrupt_ipc_subprocess(p)
        p.communicate(timeout=timeout)


@contextmanager
def log_run_events(instance, run_id):
    try:
        yield
    finally:
        for log in instance.all_logs(run_id):
            print(str(log) + "\n")  # noqa: T201


def test_monitoring():
    # with setup_instance() as instance:
    with instance_for_test(
        {
            "run_monitoring": {
                "enabled": True,
                "poll_interval_seconds": 5,
                "max_resume_run_attempts": 3,
            },
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": {},
            },
        }
    ) as instance:
        with start_daemon():
            time.sleep(5)
            assert all_daemons_healthy(instance)


def test_docker_monitoring(aws_env):
    docker_image = get_test_project_docker_image()

    launcher_config = {
        "env_vars": aws_env,
        "networks": ["container:test-postgres-db-docker"],
        "container_kwargs": {
            # "auto_remove": True,
            "volumes": ["/var/run/docker.sock:/var/run/docker.sock"],
        },
    }

    if IS_BUILDKITE:
        launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "ops": {
                "multiply_the_word_slow": {
                    "inputs": {"word": "bar"},
                    "config": {"factor": 2, "sleep_time": 20},
                }
            },
        },
    )

    with docker_postgres_instance(
        {
            "run_monitoring": {"enabled": True, "max_resume_run_attempts": 3},
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": launcher_config,
            },
        }
    ) as instance:
        recon_job = get_test_project_recon_job("demo_slow_job_docker", docker_image)
        with get_test_project_workspace_and_remote_job(
            instance, "demo_slow_job_docker", container_image=docker_image
        ) as (
            workspace,
            orig_job,
        ):
            with start_daemon():
                remote_job = ReOriginatedExternalJobForTest(orig_job, container_image=docker_image)

                run = instance.create_run_for_job(
                    job_def=recon_job.get_definition(),
                    run_config=run_config,
                    remote_job_origin=remote_job.get_remote_origin(),
                    job_code_origin=remote_job.get_python_origin(),
                )

                with log_run_events(instance, run.run_id):
                    instance.launch_run(run.run_id, workspace)

                    start_time = time.time()
                    while time.time() - start_time < 60:
                        run = instance.get_run_by_id(run.run_id)
                        if run.status == DagsterRunStatus.STARTED:
                            break
                        assert run.status == DagsterRunStatus.STARTING
                        time.sleep(1)

                    time.sleep(3)

                    instance.run_launcher._get_container(  # noqa: SLF001
                        instance.get_run_by_id(run.run_id)
                    ).stop()

                    # daemon resumes the run
                    poll_for_finished_run(instance, run.run_id, timeout=300)
                    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.SUCCESS


@pytest.fixture
def aws_env():
    aws_creds = get_aws_creds()
    return [
        f"AWS_ACCESS_KEY_ID={aws_creds['aws_access_key_id']}",
        f"AWS_SECRET_ACCESS_KEY={aws_creds['aws_secret_access_key']}",
    ]


def test_docker_monitoring_run_out_of_attempts(aws_env):
    docker_image = get_test_project_docker_image()

    launcher_config = {
        "env_vars": aws_env,
        "networks": ["container:test-postgres-db-docker"],
        "container_kwargs": {
            # "auto_remove": True,
            "volumes": ["/var/run/docker.sock:/var/run/docker.sock"],
        },
    }

    if IS_BUILDKITE:
        launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "ops": {
                "multiply_the_word_slow": {
                    "inputs": {"word": "bar"},
                    "config": {"factor": 2, "sleep_time": 20},
                }
            },
        },
    )

    with docker_postgres_instance(
        {
            "run_monitoring": {
                "enabled": True,
                "max_resume_run_attempts": 0,
                "poll_interval_seconds": 5,
            },
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": launcher_config,
            },
        }
    ) as instance:
        recon_job = get_test_project_recon_job("demo_slow_job_docker", docker_image)
        with get_test_project_workspace_and_remote_job(
            instance, "demo_slow_job_docker", container_image=docker_image
        ) as (
            workspace,
            orig_job,
        ):
            with start_daemon():
                remote_job = ReOriginatedExternalJobForTest(orig_job, container_image=docker_image)

                run = instance.create_run_for_job(
                    job_def=recon_job.get_definition(),
                    run_config=run_config,
                    remote_job_origin=remote_job.get_remote_origin(),
                    job_code_origin=remote_job.get_python_origin(),
                )

                with log_run_events(instance, run.run_id):
                    instance.launch_run(run.run_id, workspace)

                    start_time = time.time()
                    while time.time() - start_time < 60:
                        run = instance.get_run_by_id(run.run_id)
                        if run.status == DagsterRunStatus.STARTED:
                            break
                        assert run.status == DagsterRunStatus.STARTING
                        time.sleep(1)

                    time.sleep(3)

                    instance.run_launcher._get_container(  # noqa: SLF001
                        instance.get_run_by_id(run.run_id)
                    ).stop(timeout=0)

                    poll_for_finished_run(instance, run.run_id, timeout=60)
                    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.FAILURE

import os
import time

import pytest
from dagster._core.definitions.events import AssetKey
from dagster._core.storage.pipeline_run import DagsterRunStatus
from dagster._core.test_utils import poll_for_finished_run
from dagster._utils.merger import merge_dicts
from dagster._utils.yaml_utils import load_yaml_from_path, merge_yamls
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    find_local_test_image,
    get_buildkite_registry_config,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_recon_pipeline,
    get_test_project_workspace_and_external_pipeline,
)

from . import IS_BUILDKITE, docker_postgres_instance


@pytest.mark.parametrize(
    "from_pending_repository, asset_selection",
    [
        (False, None),
        (True, None),
        (True, {AssetKey("foo"), AssetKey("bar")}),
    ],
)
def test_image_on_pipeline(monkeypatch, aws_env, from_pending_repository, asset_selection):
    monkeypatch.setenv("IN_EXTERNAL_PROCESS", "yes")
    docker_image = get_test_project_docker_image()

    launcher_config = {
        "env_vars": aws_env,
        "networks": ["container:test-postgres-db-docker"],
        "container_kwargs": {
            "auto_remove": True,
            "volumes": ["/var/run/docker.sock:/var/run/docker.sock"],
        },
    }

    if IS_BUILDKITE:
        launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    executor_config = (
        {
            "execution": {"docker": {"config": {}}},
        }
        if not from_pending_repository
        else {}
    )

    env_yamls = [os.path.join(get_test_project_environments_path(), "env_s3.yaml")]
    if not from_pending_repository:
        env_yamls.append(os.path.join(get_test_project_environments_path(), "env.yaml"))
    run_config = merge_dicts(
        merge_yamls(env_yamls),
        executor_config,
    )

    with docker_postgres_instance(
        overrides={
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": launcher_config,
            }
        }
    ) as instance:
        filename = "pending_repo.py" if from_pending_repository else "repo.py"
        recon_pipeline = get_test_project_recon_pipeline(
            "demo_pipeline_docker", docker_image, filename=filename
        )
        repository_load_data = recon_pipeline.repository.get_definition().repository_load_data
        recon_pipeline = recon_pipeline.with_repository_load_data(repository_load_data)

        with get_test_project_workspace_and_external_pipeline(
            instance,
            "demo_pipeline_docker",
            container_image=docker_image,
            filename=filename,
        ) as (
            workspace,
            orig_pipeline,
        ):
            external_pipeline = ReOriginatedExternalPipelineForTest(
                orig_pipeline, container_image=docker_image, filename=filename
            )

            run = instance.create_run_for_pipeline(
                pipeline_def=recon_pipeline.get_definition(),
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
                repository_load_data=repository_load_data,
                asset_selection=frozenset(asset_selection) if asset_selection else None,
            )

            instance.launch_run(run.run_id, workspace)

            poll_for_finished_run(instance, run.run_id, timeout=60)

            for log in instance.all_logs(run.run_id):
                print(log)  # noqa: T201

            assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.SUCCESS


def test_container_context_on_pipeline(aws_env):
    docker_image = get_test_project_docker_image()

    launcher_config = {}

    if IS_BUILDKITE:
        launcher_config["registry"] = get_buildkite_registry_config()
    else:
        find_local_test_image(docker_image)

    executor_config = {
        "execution": {"docker": {"config": {}}},
    }

    run_config = merge_dicts(
        merge_yamls(
            [
                os.path.join(get_test_project_environments_path(), "env.yaml"),
                os.path.join(get_test_project_environments_path(), "env_s3.yaml"),
            ]
        ),
        executor_config,
    )

    with docker_postgres_instance(
        overrides={
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": launcher_config,
            }
        }
    ) as instance:
        recon_pipeline = get_test_project_recon_pipeline(
            "demo_pipeline_docker",
            docker_image,
            container_context={
                "docker": {
                    "env_vars": aws_env,
                    "networks": ["container:test-postgres-db-docker"],
                    "container_kwargs": {
                        "auto_remove": True,
                        "volumes": ["/var/run/docker.sock:/var/run/docker.sock"],
                    },
                }
            },
        )
        with get_test_project_workspace_and_external_pipeline(
            instance, "demo_pipeline_docker", container_image=docker_image
        ) as (
            workspace,
            orig_pipeline,
        ):
            external_pipeline = ReOriginatedExternalPipelineForTest(
                orig_pipeline, container_image=docker_image
            )

            run = instance.create_run_for_pipeline(
                pipeline_def=recon_pipeline.get_definition(),
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=recon_pipeline.get_python_origin(),
            )

            instance.launch_run(run.run_id, workspace)

            poll_for_finished_run(instance, run.run_id, timeout=60)

            for log in instance.all_logs(run.run_id):
                print(log)  # noqa: T201

            assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.SUCCESS


def test_recovery(aws_env):
    docker_image = get_test_project_docker_image()

    launcher_config = {
        "env_vars": aws_env,
        "networks": ["container:test-postgres-db-docker"],
        "container_kwargs": {
            "auto_remove": True,
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
            "solids": {
                "multiply_the_word_slow": {
                    "inputs": {"word": "bar"},
                    "config": {"factor": 2, "sleep_time": 10},
                }
            },
            "execution": {"docker": {"config": {}}},
        },
    )

    with docker_postgres_instance(
        overrides={
            "run_launcher": {
                "class": "DockerRunLauncher",
                "module": "dagster_docker",
                "config": launcher_config,
            },
            "run_monitoring": {"enabled": True},
        }
    ) as instance:
        recon_pipeline = get_test_project_recon_pipeline("demo_pipeline_docker_slow", docker_image)
        with get_test_project_workspace_and_external_pipeline(
            instance, "demo_pipeline_docker_slow", container_image=docker_image
        ) as (
            workspace,
            orig_pipeline,
        ):
            external_pipeline = ReOriginatedExternalPipelineForTest(
                orig_pipeline, container_image=docker_image
            )

            run = instance.create_run_for_pipeline(
                pipeline_def=recon_pipeline.get_definition(),
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            instance.launch_run(run.run_id, workspace)

            start_time = time.time()
            while time.time() - start_time < 60:
                run = instance.get_run_by_id(run.run_id)
                if run.status == DagsterRunStatus.STARTED:
                    break
                assert run.status == DagsterRunStatus.STARTING
                time.sleep(1)

            time.sleep(3)

            instance.run_launcher._get_container(  # pylint:disable=protected-access
                instance.get_run_by_id(run.run_id)
            ).stop()
            instance.resume_run(run.run_id, workspace, attempt_number=1)
            poll_for_finished_run(instance, run.run_id, timeout=60)

            for log in instance.all_logs(run.run_id):
                print(str(log) + "\n")  # noqa: T201
            assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.SUCCESS

import os

from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import poll_for_finished_run
from dagster.utils.merger import merge_dicts
from dagster.utils.yaml_utils import merge_yamls
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


def test_image_on_pipeline():
    docker_image = get_test_project_docker_image()

    launcher_config = {
        "env_vars": [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ],
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
        recon_pipeline = get_test_project_recon_pipeline("demo_pipeline_docker", docker_image)
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
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            instance.launch_run(run.run_id, workspace)

            poll_for_finished_run(instance, run.run_id, timeout=60)

            for log in instance.all_logs(run.run_id):
                print(log)  # pylint: disable=print-call

            assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS

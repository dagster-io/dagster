import datetime
import os
import time

import pytest
from dagster import check
from dagster.core.events import DagsterEventType
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import DOCKER_IMAGE_TAG
from dagster.core.test_utils import create_run_for_test
from dagster.utils import load_yaml_from_path, merge_dicts
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.job import get_k8s_job_name
from dagster_k8s.launcher import K8sRunLauncher
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s.utils import get_pods_in_job, wait_for_job
from dagster_k8s_test_infra.helm import (
    TEST_AWS_CONFIGMAP_NAME,
    TEST_CONFIGMAP_NAME,
    TEST_IMAGE_PULL_SECRET_NAME,
    TEST_OTHER_CONFIGMAP_NAME,
    TEST_OTHER_IMAGE_PULL_SECRET_NAME,
    TEST_OTHER_SECRET_NAME,
    TEST_SECRET_NAME,
)
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import (
    IS_BUILDKITE,
    ReOriginatedExternalPipelineForTest,
    get_test_project_docker_image,
    get_test_project_environments_path,
    get_test_project_external_pipeline_hierarchy,
)


@pytest.mark.integration
def test_k8s_run_launcher_no_celery_pods(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher
):
    # sanity check that we have a K8sRunLauncher
    check.inst(dagster_instance_for_k8s_run_launcher.run_launcher, K8sRunLauncher)
    pods = DagsterKubernetesClient.production_client().core_api.list_namespaced_pod(
        namespace=helm_namespace_for_k8s_run_launcher
    )
    celery_pod_names = [p.metadata.name for p in pods.items if "celery-workers" in p.metadata.name]
    check.invariant(not celery_pod_names)


@pytest.mark.integration
def test_k8s_run_launcher_default(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher, dagster_docker_image
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml")),
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": helm_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                        "env_config_maps": ["dagster-pipeline-env"]
                        + ([TEST_AWS_CONFIGMAP_NAME] if not IS_BUILDKITE else []),
                    }
                }
            },
        },
    )
    _launch_executor_run(
        run_config,
        dagster_instance_for_k8s_run_launcher,
        helm_namespace_for_k8s_run_launcher,
    )


@pytest.mark.integration
def test_k8s_run_launcher_volume_mounts(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher, dagster_docker_image
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": helm_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                        "env_config_maps": ["dagster-pipeline-env"]
                        + ([TEST_AWS_CONFIGMAP_NAME] if not IS_BUILDKITE else []),
                    }
                }
            },
        },
    )
    _launch_executor_run(
        run_config,
        dagster_instance_for_k8s_run_launcher,
        helm_namespace_for_k8s_run_launcher,
        pipeline_name="volume_mount_pipeline",
        num_steps=1,
    )


@pytest.mark.integration
def test_k8s_executor_get_config_from_run_launcher(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher, dagster_docker_image
):
    # Verify that if you do not specify executor config it is delegated by the run launcher
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml")),
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {"k8s": {"config": {"job_image": dagster_docker_image}}},
        },
    )
    _launch_executor_run(
        run_config,
        dagster_instance_for_k8s_run_launcher,
        helm_namespace_for_k8s_run_launcher,
    )


@pytest.mark.integration
def test_k8s_executor_combine_configs(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher, dagster_docker_image
):
    # Verifies that the step pods created by the k8s executor combine secrets
    # from run launcher config and executor config. Also includes each executor secret
    # twice to verify that duplicates within the combined config are acceptable
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml")),
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_image": dagster_docker_image,
                        "image_pull_secrets": [
                            {"name": TEST_OTHER_IMAGE_PULL_SECRET_NAME},
                            {"name": TEST_OTHER_IMAGE_PULL_SECRET_NAME},
                        ],
                        "env_config_maps": [TEST_OTHER_CONFIGMAP_NAME, TEST_OTHER_CONFIGMAP_NAME],
                        "env_secrets": [TEST_OTHER_SECRET_NAME, TEST_OTHER_SECRET_NAME],
                    }
                }
            },
        },
    )
    run_id = _launch_executor_run(
        run_config,
        dagster_instance_for_k8s_run_launcher,
        helm_namespace_for_k8s_run_launcher,
    )

    step_job_key = get_k8s_job_name(run_id, "count_letters")
    step_job_name = f"dagster-job-{step_job_key}"

    step_pods = get_pods_in_job(
        job_name=step_job_name, namespace=helm_namespace_for_k8s_run_launcher
    )

    assert len(step_pods) == 1

    step_pod = step_pods[0]

    assert len(step_pod.spec.containers) == 1, str(step_pod)

    env_from = step_pod.spec.containers[0].env_from

    config_map_names = {env.config_map_ref.name for env in env_from if env.config_map_ref}
    secret_names = {env.secret_ref.name for env in env_from if env.secret_ref}

    # Run launcher secrets and config maps included
    assert TEST_SECRET_NAME in secret_names
    assert TEST_CONFIGMAP_NAME in config_map_names

    # Executor secrets and config maps included
    assert TEST_OTHER_SECRET_NAME in secret_names
    assert TEST_OTHER_CONFIGMAP_NAME in config_map_names

    image_pull_secrets_names = [secret.name for secret in step_pod.spec.image_pull_secrets]

    assert TEST_IMAGE_PULL_SECRET_NAME in image_pull_secrets_names
    assert TEST_OTHER_IMAGE_PULL_SECRET_NAME in image_pull_secrets_names


def _launch_executor_run(
    run_config,
    dagster_instance_for_k8s_run_launcher,
    helm_namespace_for_k8s_run_launcher,
    pipeline_name="demo_k8s_executor_pipeline",
    num_steps=2,
):
    tags = {"key": "value"}

    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)
        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            tags=tags,
            mode="default",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "default", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )
        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)

        result = wait_for_job_and_get_raw_logs(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

        updated_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run.run_id)
        assert updated_run.tags[DOCKER_IMAGE_TAG] == get_test_project_docker_image()

        events = dagster_instance_for_k8s_run_launcher.all_logs(run.run_id)
        assert (
            len(
                [
                    event
                    for event in events
                    if ("Executing step" in event.message and "in Kubernetes job" in event.message)
                ]
            )
            == num_steps
        )

        return run.run_id


@pytest.mark.integration
def test_k8s_run_launcher_image_from_origin(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher, dagster_docker_image
):
    # Like the previous test, but the executor doesn't supply an image - it's pulled
    # from the origin (see get_test_project_external_pipeline_hierarchy below) instead

    check.inst(dagster_instance_for_k8s_run_launcher.run_launcher, K8sRunLauncher)
    pods = DagsterKubernetesClient.production_client().core_api.list_namespaced_pod(
        namespace=helm_namespace_for_k8s_run_launcher
    )
    celery_pod_names = [p.metadata.name for p in pods.items if "celery-workers" in p.metadata.name]
    check.invariant(not celery_pod_names)

    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml")),
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": helm_namespace_for_k8s_run_launcher,
                        "image_pull_policy": image_pull_policy(),
                        "env_config_maps": ["dagster-pipeline-env"]
                        + ([TEST_AWS_CONFIGMAP_NAME] if not IS_BUILDKITE else []),
                    }
                }
            },
        },
    )

    pipeline_name = "demo_k8s_executor_pipeline"
    tags = {"key": "value"}

    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name, dagster_docker_image
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(
            external_pipeline, container_image=dagster_docker_image
        )
        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            tags=tags,
            mode="default",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "default", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )
        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)

        result = wait_for_job_and_get_raw_logs(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

        updated_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run.run_id)
        assert updated_run.tags[DOCKER_IMAGE_TAG] == get_test_project_docker_image()


@pytest.mark.integration
def test_k8s_run_launcher_terminate(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher, dagster_docker_image
):
    pipeline_name = "slow_pipeline"

    tags = {"key": "value"}

    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": helm_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                        "env_config_maps": ["dagster-pipeline-env"]
                        + ([TEST_AWS_CONFIGMAP_NAME] if not IS_BUILDKITE else []),
                    }
                }
            },
        },
    )

    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)
        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            tags=tags,
            mode="k8s",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "k8s", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )

        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)

        wait_for_job(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )
        timeout = datetime.timedelta(0, 30)
        start_time = datetime.datetime.now()
        while datetime.datetime.now() < start_time + timeout:
            if dagster_instance_for_k8s_run_launcher.run_launcher.can_terminate(run_id=run.run_id):
                break
            time.sleep(5)

        assert dagster_instance_for_k8s_run_launcher.run_launcher.can_terminate(run_id=run.run_id)
        assert dagster_instance_for_k8s_run_launcher.run_launcher.terminate(run_id=run.run_id)

        start_time = datetime.datetime.now()
        pipeline_run = None
        while datetime.datetime.now() < start_time + timeout:
            pipeline_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run.run_id)
            if pipeline_run.status == PipelineRunStatus.CANCELED:
                break

            time.sleep(5)

        # useful to have logs here, because the worker pods get deleted
        print(  # pylint: disable=print-call
            dagster_instance_for_k8s_run_launcher.all_logs(run.run_id)
        )

        assert pipeline_run.status == PipelineRunStatus.CANCELED

        assert not dagster_instance_for_k8s_run_launcher.run_launcher.terminate(run_id=run.run_id)


@pytest.mark.integration
def test_k8s_executor_resource_requirements(
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher, dagster_docker_image
):
    # sanity check that we have a K8sRunLauncher
    check.inst(dagster_instance_for_k8s_run_launcher.run_launcher, K8sRunLauncher)
    pods = DagsterKubernetesClient.production_client().core_api.list_namespaced_pod(
        namespace=helm_namespace_for_k8s_run_launcher
    )
    celery_pod_names = [p.metadata.name for p in pods.items if "celery-workers" in p.metadata.name]
    check.invariant(not celery_pod_names)

    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": helm_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                        "env_config_maps": ["dagster-pipeline-env"]
                        + ([TEST_AWS_CONFIGMAP_NAME] if not IS_BUILDKITE else []),
                    }
                }
            },
        },
    )

    pipeline_name = "resources_limit_pipeline"
    tags = {"key": "value"}

    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)
        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            tags=tags,
            mode="k8s",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "k8s", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )
        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)

        result = wait_for_job_and_get_raw_logs(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

        updated_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run.run_id)
        assert updated_run.tags[DOCKER_IMAGE_TAG] == get_test_project_docker_image()


def test_execute_on_k8s_retry_pipeline(  # pylint: disable=redefined-outer-name
    dagster_instance_for_k8s_run_launcher, helm_namespace_for_k8s_run_launcher, dagster_docker_image
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": helm_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                        "env_config_maps": ["dagster-pipeline-env"]
                        + ([TEST_AWS_CONFIGMAP_NAME] if not IS_BUILDKITE else []),
                    }
                }
            },
        },
    )

    pipeline_name = "retry_pipeline"
    with get_test_project_external_pipeline_hierarchy(
        dagster_instance_for_k8s_run_launcher, pipeline_name
    ) as (
        workspace,
        location,
        _repo,
        external_pipeline,
    ):
        reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)

        run = create_run_for_test(
            dagster_instance_for_k8s_run_launcher,
            pipeline_name=pipeline_name,
            run_config=run_config,
            mode="k8s",
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=location.get_external_execution_plan(
                external_pipeline, run_config, "k8s", None, None
            ).execution_plan_snapshot,
            external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
            pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
        )

        dagster_instance_for_k8s_run_launcher.launch_run(run.run_id, workspace)

        result = wait_for_job_and_get_raw_logs(
            job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace_for_k8s_run_launcher
        )

        assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

        stats = dagster_instance_for_k8s_run_launcher.get_run_stats(run.run_id)
        assert stats.steps_succeeded == 1

        all_logs = dagster_instance_for_k8s_run_launcher.all_logs(run.run_id)

        assert DagsterEventType.STEP_START in [
            event.dagster_event.event_type for event in all_logs if event.is_dagster_event
        ]

        assert DagsterEventType.STEP_UP_FOR_RETRY in [
            event.dagster_event.event_type for event in all_logs if event.is_dagster_event
        ]

        assert DagsterEventType.STEP_RESTARTED in [
            event.dagster_event.event_type for event in all_logs if event.is_dagster_event
        ]

        assert DagsterEventType.STEP_SUCCESS in [
            event.dagster_event.event_type for event in all_logs if event.is_dagster_event
        ]

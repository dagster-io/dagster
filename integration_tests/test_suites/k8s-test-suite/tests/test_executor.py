import datetime
import os
import time
import uuid

import dagster._check as check
import pytest
from dagster._core.events import DagsterEventType
from dagster._core.storage.pipeline_run import DagsterRunStatus
from dagster._core.storage.tags import DOCKER_IMAGE_TAG
from dagster._utils.merger import deep_merge_dicts, merge_dicts
from dagster._utils.yaml_utils import load_yaml_from_path
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.job import get_k8s_job_name
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s_test_infra.helm import (
    TEST_CONFIGMAP_NAME,
    TEST_IMAGE_PULL_SECRET_NAME,
    TEST_OTHER_CONFIGMAP_NAME,
    TEST_OTHER_IMAGE_PULL_SECRET_NAME,
    TEST_OTHER_SECRET_NAME,
    TEST_SECRET_NAME,
)
from dagster_k8s_test_infra.integration_utils import (
    can_terminate_run_over_graphql,
    image_pull_policy,
    launch_run_over_graphql,
    terminate_run_over_graphql,
)
from dagster_test.test_project import (
    cleanup_memoized_results,
    get_test_project_docker_image,
    get_test_project_environments_path,
)
from dagster_test.test_project.test_pipelines.repo import define_memoization_pipeline


@pytest.mark.integration
def test_k8s_run_launcher_no_celery_pods(system_namespace_for_k8s_run_launcher):
    pods = DagsterKubernetesClient.production_client().core_api.list_namespaced_pod(
        namespace=system_namespace_for_k8s_run_launcher
    )
    celery_pod_names = [p.metadata.name for p in pods.items if "celery-workers" in p.metadata.name]
    check.invariant(not celery_pod_names)


@pytest.mark.integration
def test_k8s_run_launcher_default(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagster_docker_image,
    dagit_url_for_k8s_run_launcher,
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env.yaml")),
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": user_code_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                    }
                }
            },
        },
    )
    _launch_executor_run(
        dagit_url_for_k8s_run_launcher,
        run_config,
        dagster_instance_for_k8s_run_launcher,
        user_code_namespace_for_k8s_run_launcher,
    )


@pytest.mark.integration
def test_k8s_run_launcher_volume_mounts(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagster_docker_image,
    dagit_url_for_k8s_run_launcher,
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": user_code_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                    }
                }
            },
        },
    )
    _launch_executor_run(
        dagit_url_for_k8s_run_launcher,
        run_config,
        dagster_instance_for_k8s_run_launcher,
        user_code_namespace_for_k8s_run_launcher,
        pipeline_name="volume_mount_pipeline",
        num_steps=1,
        mode="k8s",
    )


@pytest.mark.integration
def test_k8s_executor_get_config_from_run_launcher(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagster_docker_image,
    dagit_url_for_k8s_run_launcher,
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
        dagit_url_for_k8s_run_launcher,
        run_config,
        dagster_instance_for_k8s_run_launcher,
        user_code_namespace_for_k8s_run_launcher,
    )


@pytest.mark.integration
def test_k8s_executor_combine_configs(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagster_docker_image,
    dagit_url_for_k8s_run_launcher,
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
                        "labels": {"executor_label_key": "executor_label_value"},
                    }
                }
            },
        },
    )
    run_id = _launch_executor_run(
        dagit_url_for_k8s_run_launcher,
        run_config,
        dagster_instance_for_k8s_run_launcher,
        user_code_namespace_for_k8s_run_launcher,
    )

    step_job_key = get_k8s_job_name(run_id, "count_letters")
    step_job_name = f"dagster-step-{step_job_key}"

    step_pods = DagsterKubernetesClient.production_client().get_pods_in_job(
        job_name=step_job_name, namespace=user_code_namespace_for_k8s_run_launcher
    )

    assert len(step_pods) == 1

    step_pod = step_pods[0]

    assert len(step_pod.spec.containers) == 1, str(step_pod)

    labels = step_pod.metadata.labels
    assert labels["run_launcher_label_key"] == "run_launcher_label_value"
    assert labels["executor_label_key"] == "executor_label_value"

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


def _get_step_execution_events(events):
    return [
        event
        for event in events
        if ("Executing step" in event.message and "in Kubernetes job" in event.message)
    ]


def _launch_executor_run(
    dagit_url,
    run_config,
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    pipeline_name="demo_k8s_executor_pipeline",
    num_steps=2,
    mode="default",
):
    run_id = launch_run_over_graphql(
        dagit_url, run_config=run_config, pipeline_name=pipeline_name, mode=mode
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run_id, namespace=user_code_namespace_for_k8s_run_launcher
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

    updated_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run_id)
    assert updated_run.tags[DOCKER_IMAGE_TAG] == get_test_project_docker_image()

    events = dagster_instance_for_k8s_run_launcher.all_logs(run_id)
    assert len(_get_step_execution_events(events)) == num_steps

    return run_id


@pytest.mark.integration
def test_k8s_run_launcher_image_from_origin(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagit_url_for_k8s_run_launcher,
):
    # Like the previous test, but the executor doesn't supply an image - it's pulled
    # from the origin on the run instead
    pods = DagsterKubernetesClient.production_client().core_api.list_namespaced_pod(
        namespace=user_code_namespace_for_k8s_run_launcher
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
                        "job_namespace": user_code_namespace_for_k8s_run_launcher,
                        "image_pull_policy": image_pull_policy(),
                    }
                }
            },
        },
    )

    pipeline_name = "demo_k8s_executor_pipeline"

    run_id = launch_run_over_graphql(
        dagit_url_for_k8s_run_launcher, run_config=run_config, pipeline_name=pipeline_name
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run_id, namespace=user_code_namespace_for_k8s_run_launcher
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

    updated_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run_id)
    assert updated_run.tags[DOCKER_IMAGE_TAG] == get_test_project_docker_image()


@pytest.mark.integration
def test_k8s_run_launcher_terminate(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagster_docker_image,
    dagit_url_for_k8s_run_launcher,
):
    pipeline_name = "slow_pipeline"

    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": user_code_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                    }
                }
            },
        },
    )

    run_id = launch_run_over_graphql(
        dagit_url_for_k8s_run_launcher,
        run_config=run_config,
        pipeline_name=pipeline_name,
        mode="k8s",
    )

    DagsterKubernetesClient.production_client().wait_for_job(
        job_name="dagster-run-%s" % run_id, namespace=user_code_namespace_for_k8s_run_launcher
    )
    timeout = datetime.timedelta(0, 30)
    start_time = datetime.datetime.now()
    while True:
        assert datetime.datetime.now() < start_time + timeout, "Timed out waiting for can_terminate"
        if can_terminate_run_over_graphql(dagit_url_for_k8s_run_launcher, run_id):
            break
        time.sleep(5)

    terminate_run_over_graphql(dagit_url_for_k8s_run_launcher, run_id=run_id)

    start_time = datetime.datetime.now()
    pipeline_run = None
    while True:
        assert datetime.datetime.now() < start_time + timeout, "Timed out waiting for termination"
        pipeline_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run_id)
        if pipeline_run.status == DagsterRunStatus.CANCELED:
            break

        time.sleep(5)

    # useful to have logs here, because the worker pods get deleted
    print(dagster_instance_for_k8s_run_launcher.all_logs(run_id))  # noqa: T201

    assert pipeline_run.status == DagsterRunStatus.CANCELED

    assert not can_terminate_run_over_graphql(dagit_url_for_k8s_run_launcher, run_id)


@pytest.mark.integration
def test_k8s_executor_resource_requirements(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagster_docker_image,
    dagit_url_for_k8s_run_launcher,
):
    # sanity check that we have a K8sRunLauncher
    pods = DagsterKubernetesClient.production_client().core_api.list_namespaced_pod(
        namespace=user_code_namespace_for_k8s_run_launcher
    )
    celery_pod_names = [p.metadata.name for p in pods.items if "celery-workers" in p.metadata.name]
    check.invariant(not celery_pod_names)

    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": user_code_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                    }
                }
            },
        },
    )

    pipeline_name = "resources_limit_pipeline"

    run_id = launch_run_over_graphql(
        dagit_url_for_k8s_run_launcher,
        run_config=run_config,
        pipeline_name=pipeline_name,
        mode="k8s",
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run_id, namespace=user_code_namespace_for_k8s_run_launcher
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

    updated_run = dagster_instance_for_k8s_run_launcher.get_run_by_id(run_id)
    assert updated_run.tags[DOCKER_IMAGE_TAG] == get_test_project_docker_image()


@pytest.mark.integration
def test_execute_on_k8s_retry_pipeline(  # pylint: disable=redefined-outer-name
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagster_docker_image,
    dagit_url_for_k8s_run_launcher,
):
    run_config = merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": user_code_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                    }
                }
            },
        },
    )

    pipeline_name = "retry_pipeline"

    run_id = launch_run_over_graphql(
        dagit_url_for_k8s_run_launcher,
        run_config=run_config,
        pipeline_name=pipeline_name,
        mode="k8s",
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run_id, namespace=user_code_namespace_for_k8s_run_launcher
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

    stats = dagster_instance_for_k8s_run_launcher.get_run_stats(run_id)
    assert stats.steps_succeeded == 1

    all_logs = dagster_instance_for_k8s_run_launcher.all_logs(run_id)

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


@pytest.mark.integration
def test_memoization_k8s_executor(
    dagster_instance_for_k8s_run_launcher,
    user_code_namespace_for_k8s_run_launcher,
    dagster_docker_image,
    dagit_url_for_k8s_run_launcher,
):
    ephemeral_path = str(uuid.uuid4())
    run_config = deep_merge_dicts(
        load_yaml_from_path(os.path.join(get_test_project_environments_path(), "env_s3.yaml")),
        {
            "execution": {
                "k8s": {
                    "config": {
                        "job_namespace": user_code_namespace_for_k8s_run_launcher,
                        "job_image": dagster_docker_image,
                        "image_pull_policy": image_pull_policy(),
                    }
                }
            },
        },
    )

    run_config = deep_merge_dicts(
        run_config,
        {"resources": {"io_manager": {"config": {"s3_prefix": ephemeral_path}}}},
    )

    # wrap in try-catch to ensure that memoized results are always cleaned from s3 bucket
    try:
        pipeline_name = "memoization_pipeline"

        run_ids = []
        for _ in range(2):
            run_id = launch_run_over_graphql(
                dagit_url_for_k8s_run_launcher,
                run_config=run_config,
                pipeline_name=pipeline_name,
                mode="k8s",
            )

            result = wait_for_job_and_get_raw_logs(
                job_name="dagster-run-%s" % run_id,
                namespace=user_code_namespace_for_k8s_run_launcher,
            )

            assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)

            run_ids.append(run_id)

        # We expect that first run should have to run the step, since it has not yet been
        # memoized.
        unmemoized_run_id = run_ids[0]
        events = dagster_instance_for_k8s_run_launcher.all_logs(unmemoized_run_id)
        assert len(_get_step_execution_events(events)) == 1

        # We expect that second run should not have to run the step, since it has been memoized.
        memoized_run_id = run_ids[1]
        events = dagster_instance_for_k8s_run_launcher.all_logs(memoized_run_id)
        assert len(_get_step_execution_events(events)) == 0
    finally:
        cleanup_memoized_results(
            define_memoization_pipeline(), "k8s", dagster_instance_for_k8s_run_launcher, run_config
        )

from unittest import mock

import pytest
from dagster import reconstructable
from dagster._check import CheckError
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.launcher import LaunchRunContext
from dagster._core.remote_representation import RepositoryHandle
from dagster._core.storage.tags import DOCKER_IMAGE_TAG
from dagster._core.test_utils import (
    create_run_for_test,
    environ,
    in_process_test_workspace,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.types import ExecuteRunArgs
from dagster._utils.hosted_user_process import remote_job_from_recon_job
from dagster._utils.merger import merge_dicts
from dagster_celery_k8s.config import get_celery_engine_config, get_celery_engine_job_config
from dagster_celery_k8s.executor import CELERY_K8S_CONFIG_KEY
from dagster_celery_k8s.launcher import (
    CeleryK8sRunLauncher,
    _get_validated_celery_k8s_executor_config,
)
from dagster_k8s.client import DEFAULT_WAIT_TIMEOUT
from dagster_test.test_project import get_test_project_workspace_and_remote_job


def test_empty_celery_config():
    res = _get_validated_celery_k8s_executor_config({"execution": {CELERY_K8S_CONFIG_KEY: None}})

    assert res == {
        "backend": "rpc://",
        "retries": {"enabled": {}},
        "volume_mounts": [],
        "volumes": [],
        "load_incluster_config": True,
        "per_step_k8s_config": {},
        "repo_location_name": "<<in_process>>",
        "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
    }


def test_get_validated_celery_k8s_executor_config():
    res = _get_validated_celery_k8s_executor_config(
        {"execution": {CELERY_K8S_CONFIG_KEY: {"config": {"job_image": "foo"}}}}
    )

    assert res == {
        "backend": "rpc://",
        "retries": {"enabled": {}},
        "job_image": "foo",
        "load_incluster_config": True,
        "per_step_k8s_config": {},
        "repo_location_name": "<<in_process>>",
        "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
        "volume_mounts": [],
        "volumes": [],
    }

    with pytest.raises(
        CheckError,
        match="Incorrect execution schema provided",
    ):
        _get_validated_celery_k8s_executor_config(
            {"execution": {"celery-k8s": {"config": {"foo": "bar"}}}}
        )

    with environ(
        {
            "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE": "my-namespace",
            "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP": "config-pipeline-env",
        }
    ):
        cfg = get_celery_engine_job_config()
        res = _get_validated_celery_k8s_executor_config(cfg)
        assert res == {
            "backend": "rpc://",
            "retries": {"enabled": {}},
            "env_config_maps": ["config-pipeline-env"],
            "per_step_k8s_config": {},
            "load_incluster_config": True,
            "job_namespace": "my-namespace",
            "repo_location_name": "<<in_process>>",
            "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
            "volume_mounts": [],
            "volumes": [],
        }

    # Test setting all possible config fields
    with environ(
        {
            "TEST_PIPELINE_RUN_NAMESPACE": "my-namespace",
            "TEST_CELERY_BROKER": "redis://some-redis-host:6379/0",
            "TEST_CELERY_BACKEND": "redis://some-redis-host:6379/0",
            "TEST_PIPELINE_RUN_IMAGE": "foo",
            "TEST_K8S_PULL_SECRET_1": "super-secret-1",
            "TEST_K8S_PULL_SECRET_2": "super-secret-2",
            "TEST_SERVICE_ACCOUNT_NAME": "my-cool-service-acccount",
            "TEST_PIPELINE_RUN_ENV_CONFIGMAP": "config-pipeline-env",
            "TEST_SECRET": "config-secret-env",
        }
    ):
        cfg = {
            "execution": {
                "config": {
                    "repo_location_name": "<<in_process>>",
                    "load_incluster_config": False,
                    "kubeconfig_file": "/some/kubeconfig/file",
                    "job_namespace": {"env": "TEST_PIPELINE_RUN_NAMESPACE"},
                    "broker": {"env": "TEST_CELERY_BROKER"},
                    "backend": {"env": "TEST_CELERY_BACKEND"},
                    "include": ["dagster", "dagster-webserver"],
                    "config_source": {
                        "task_annotations": """{'*': {'on_failure': my_on_failure}}"""
                    },
                    "retries": {"disabled": {}},
                    "job_image": {"env": "TEST_PIPELINE_RUN_IMAGE"},
                    "image_pull_policy": "IfNotPresent",
                    "image_pull_secrets": [
                        {"name": {"env": "TEST_K8S_PULL_SECRET_1"}},
                        {"name": {"env": "TEST_K8S_PULL_SECRET_2"}},
                    ],
                    "service_account_name": {"env": "TEST_SERVICE_ACCOUNT_NAME"},
                    "env_config_maps": [{"env": "TEST_PIPELINE_RUN_ENV_CONFIGMAP"}],
                    "env_secrets": [{"env": "TEST_SECRET"}],
                    "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
                    "volume_mounts": [],
                    "volumes": [],
                }
            }
        }

        res = _get_validated_celery_k8s_executor_config(cfg)
        assert res == {
            "repo_location_name": "<<in_process>>",
            "load_incluster_config": False,
            "kubeconfig_file": "/some/kubeconfig/file",
            "backend": "redis://some-redis-host:6379/0",
            "broker": "redis://some-redis-host:6379/0",
            "job_namespace": "my-namespace",
            "include": ["dagster", "dagster-webserver"],
            "config_source": {"task_annotations": """{'*': {'on_failure': my_on_failure}}"""},
            "retries": {"disabled": {}},
            "job_image": "foo",
            "per_step_k8s_config": {},
            "image_pull_policy": "IfNotPresent",
            "image_pull_secrets": [{"name": "super-secret-1"}, {"name": "super-secret-2"}],
            "service_account_name": "my-cool-service-acccount",
            "env_config_maps": ["config-pipeline-env"],
            "env_secrets": ["config-secret-env"],
            "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
            "volume_mounts": [],
            "volumes": [],
        }


def test_get_validated_celery_k8s_executor_config_for_job():
    res = _get_validated_celery_k8s_executor_config({"execution": {"config": {"job_image": "foo"}}})

    assert res == {
        "backend": "rpc://",
        "retries": {"enabled": {}},
        "job_image": "foo",
        "load_incluster_config": True,
        "per_step_k8s_config": {},
        "repo_location_name": "<<in_process>>",
        "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
        "volume_mounts": [],
        "volumes": [],
    }

    with pytest.raises(
        CheckError,
        match="Incorrect execution schema provided",
    ):
        _get_validated_celery_k8s_executor_config({"execution": {"config": {"foo": "bar"}}})

    with environ(
        {
            "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE": "my-namespace",
            "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP": "config-pipeline-env",
        }
    ):
        cfg = get_celery_engine_config()
        res = _get_validated_celery_k8s_executor_config(cfg)
        assert res == {
            "backend": "rpc://",
            "retries": {"enabled": {}},
            "env_config_maps": ["config-pipeline-env"],
            "load_incluster_config": True,
            "per_step_k8s_config": {},
            "job_namespace": "my-namespace",
            "repo_location_name": "<<in_process>>",
            "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
            "volume_mounts": [],
            "volumes": [],
        }

    # Test setting all possible config fields
    with environ(
        {
            "TEST_PIPELINE_RUN_NAMESPACE": "my-namespace",
            "TEST_CELERY_BROKER": "redis://some-redis-host:6379/0",
            "TEST_CELERY_BACKEND": "redis://some-redis-host:6379/0",
            "TEST_PIPELINE_RUN_IMAGE": "foo",
            "TEST_PIPELINE_RUN_IMAGE_PULL_POLICY": "Always",
            "TEST_K8S_PULL_SECRET_1": "super-secret-1",
            "TEST_K8S_PULL_SECRET_2": "super-secret-2",
            "TEST_SERVICE_ACCOUNT_NAME": "my-cool-service-acccount",
            "TEST_PIPELINE_RUN_ENV_CONFIGMAP": "config-pipeline-env",
            "TEST_SECRET": "config-secret-env",
        }
    ):
        cfg = {
            "execution": {
                CELERY_K8S_CONFIG_KEY: {
                    "config": {
                        "repo_location_name": "<<in_process>>",
                        "load_incluster_config": False,
                        "kubeconfig_file": "/some/kubeconfig/file",
                        "job_namespace": {"env": "TEST_PIPELINE_RUN_NAMESPACE"},
                        "broker": {"env": "TEST_CELERY_BROKER"},
                        "backend": {"env": "TEST_CELERY_BACKEND"},
                        "include": ["dagster", "dagster-webserver"],
                        "config_source": {
                            "task_annotations": """{'*': {'on_failure': my_on_failure}}"""
                        },
                        "retries": {"disabled": {}},
                        "job_image": {"env": "TEST_PIPELINE_RUN_IMAGE"},
                        "image_pull_policy": "IfNotPresent",
                        "image_pull_secrets": [
                            {"name": {"env": "TEST_K8S_PULL_SECRET_1"}},
                            {"name": {"env": "TEST_K8S_PULL_SECRET_2"}},
                        ],
                        "service_account_name": {"env": "TEST_SERVICE_ACCOUNT_NAME"},
                        "env_config_maps": [{"env": "TEST_PIPELINE_RUN_ENV_CONFIGMAP"}],
                        "env_secrets": [{"env": "TEST_SECRET"}],
                        "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
                        "volume_mounts": [],
                        "volumes": [],
                    }
                }
            }
        }

        res = _get_validated_celery_k8s_executor_config(cfg)
        assert res == {
            "repo_location_name": "<<in_process>>",
            "load_incluster_config": False,
            "kubeconfig_file": "/some/kubeconfig/file",
            "job_namespace": "my-namespace",
            "backend": "redis://some-redis-host:6379/0",
            "broker": "redis://some-redis-host:6379/0",
            "include": ["dagster", "dagster-webserver"],
            "config_source": {"task_annotations": """{'*': {'on_failure': my_on_failure}}"""},
            "retries": {"disabled": {}},
            "job_image": "foo",
            "per_step_k8s_config": {},
            "image_pull_policy": "IfNotPresent",
            "image_pull_secrets": [{"name": "super-secret-1"}, {"name": "super-secret-2"}],
            "service_account_name": "my-cool-service-acccount",
            "env_config_maps": ["config-pipeline-env"],
            "env_secrets": ["config-secret-env"],
            "job_wait_timeout": DEFAULT_WAIT_TIMEOUT,
            "volume_mounts": [],
            "volumes": [],
        }


def test_launcher_from_config(kubeconfig_file):
    default_config = {
        "instance_config_map": "dagster-instance",
        "postgres_password_secret": "dagster-postgresql-secret",
        "dagster_home": "/opt/dagster/dagster_home",
        "load_incluster_config": False,
        "kubeconfig_file": kubeconfig_file,
    }

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_celery_k8s",
                "class": "CeleryK8sRunLauncher",
                "config": default_config,
            }
        }
    ) as instance:
        run_launcher = instance.run_launcher
        assert isinstance(run_launcher, CeleryK8sRunLauncher)
        assert run_launcher._fail_pod_on_run_failure is None  # noqa: SLF001

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_celery_k8s",
                "class": "CeleryK8sRunLauncher",
                "config": merge_dicts(default_config, {"fail_pod_on_run_failure": True}),
            }
        }
    ) as instance:
        run_launcher = instance.run_launcher
        assert isinstance(run_launcher, CeleryK8sRunLauncher)
        assert run_launcher._fail_pod_on_run_failure  # noqa: SLF001


def test_user_defined_k8s_config_in_run_tags(kubeconfig_file):
    labels = {"foo_label_key": "bar_label_value"}

    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    celery_k8s_run_launcher = CeleryK8sRunLauncher(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        labels=labels,
    )

    # Construct Dagster run tags with user defined k8s config.
    expected_image = "different_image:tag"
    expected_resources = {
        "requests": {"cpu": "250m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "2560Mi"},
    }
    tags = {
        "dagster-k8s/config": {
            "container_config": {"image": expected_image, "resources": expected_resources},
            "pod_spec_config": {"scheduler_name": "test-scheduler-2"},
        }
    }
    # Create fake external job.
    recon_job = reconstructable(fake_job)
    recon_repo = recon_job.repository
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])

            repo_def = recon_repo.get_definition()
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            celery_k8s_run_launcher.register_instance(instance)
            job_name = "demo_job"
            run_config = {"execution": {"celery-k8s": {"config": {"job_image": "fake-image-name"}}}}
            run = create_run_for_test(
                instance,
                job_name=job_name,
                run_config=run_config,
                tags=tags,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=fake_remote_job.get_python_origin(),
            )
            celery_k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == expected_image  # pyright: ignore[reportOptionalMemberAccess]

            # Check that user defined k8s config was passed down to the k8s job.
            mock_method_calls = mock_k8s_client_batch_api.method_calls
            assert len(mock_method_calls) > 0
            method_name, _args, kwargs = mock_method_calls[0]
            assert method_name == "create_namespaced_job"

            container = kwargs["body"].spec.template.spec.containers[0]

            job_resources = container.resources
            resolved_resources = job_resources.to_dict()
            resolved_resources.pop("claims", None)  # remove claims if returned
            assert resolved_resources == expected_resources

            labels = kwargs["body"].spec.template.metadata.labels
            assert labels["foo_label_key"] == "bar_label_value"
            assert labels["dagster/code-location"] == "in_process"
            assert labels["dagster/job"] == "fake_job"
            assert labels["dagster/run-id"] == run.run_id

            args = container.args
            assert (
                args
                == ExecuteRunArgs(
                    job_origin=run.job_code_origin,  # pyright: ignore[reportArgumentType]
                    run_id=run.run_id,
                    instance_ref=instance.get_ref(),
                    set_exit_code_on_failure=None,
                ).get_command_args()
            )


def test_raise_on_error(kubeconfig_file):
    mock_k8s_client_batch_api = mock.MagicMock()
    celery_k8s_run_launcher = CeleryK8sRunLauncher(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        fail_pod_on_run_failure=True,
    )
    # Create fake external job.
    recon_job = reconstructable(fake_job)
    recon_repo = recon_job.repository
    loadable_target_origin = LoadableTargetOrigin(
        python_file=__file__,
    )
    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])

            repo_def = recon_repo.get_definition()
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            celery_k8s_run_launcher.register_instance(instance)
            job_name = "demo_job"
            run_config = {"execution": {"celery-k8s": {"config": {"job_image": "fake-image-name"}}}}
            run = create_run_for_test(
                instance,
                job_name=job_name,
                run_config=run_config,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=fake_remote_job.get_python_origin(),
            )
            celery_k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            # Check that user defined k8s config was passed down to the k8s job.
            mock_method_calls = mock_k8s_client_batch_api.method_calls
            assert len(mock_method_calls) > 0
            method_name, _args, kwargs = mock_method_calls[0]
            assert method_name == "create_namespaced_job"

            container = kwargs["body"].spec.template.spec.containers[0]

            args = container.args
            assert (
                args
                == ExecuteRunArgs(
                    job_origin=run.job_code_origin,  # pyright: ignore[reportArgumentType]
                    run_id=run.run_id,
                    instance_ref=instance.get_ref(),
                    set_exit_code_on_failure=True,
                ).get_command_args()
            )


def test_k8s_executor_config_override(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    celery_k8s_run_launcher = CeleryK8sRunLauncher(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    job_name = "demo_job"

    with instance_for_test() as instance:
        with get_test_project_workspace_and_remote_job(instance, job_name, "my_image:tag") as (
            workspace,
            remote_job,
        ):
            # Launch the run in a fake Dagster instance.
            celery_k8s_run_launcher.register_instance(instance)

            # Launch without custom job_image
            run = create_run_for_test(
                instance,
                job_name=job_name,
                run_config={"execution": {"celery-k8s": {}}},
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )
            celery_k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "my_image:tag"  # pyright: ignore[reportOptionalMemberAccess]

            # Launch with custom job_image
            run = create_run_for_test(
                instance,
                job_name=job_name,
                run_config={
                    "execution": {"celery-k8s": {"config": {"job_image": "fake-image-name"}}}
                },
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )
            celery_k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake-image-name"  # pyright: ignore[reportOptionalMemberAccess]

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0

        _, _args, kwargs = mock_method_calls[0]
        assert kwargs["body"].spec.template.spec.containers[0].image == "my_image:tag"

        _, _args, kwargs = mock_method_calls[1]
        assert kwargs["body"].spec.template.spec.containers[0].image == "fake-image-name"


@job
def fake_job():
    pass

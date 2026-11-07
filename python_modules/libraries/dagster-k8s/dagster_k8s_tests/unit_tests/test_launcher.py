from datetime import datetime
from unittest import mock

import kubernetes.client.rest
import pytest
from dagster import DagsterRunStatus, job, reconstructable
from dagster._core.launcher import LaunchRunContext
from dagster._core.launcher.base import WorkerStatus
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.tags import DOCKER_IMAGE_TAG
from dagster._core.test_utils import (
    create_run_for_test,
    in_process_test_workspace,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.types import ExecuteRunArgs
from dagster._utils.hosted_user_process import remote_job_from_recon_job
from dagster._utils.merger import merge_dicts
from dagster_k8s import (
    K8sRunLauncher,
    launcher as launcher_module,
)
from dagster_k8s.job import DAGSTER_PG_PASSWORD_ENV_VAR, get_job_name_from_run_id
from kubernetes import __version__ as kubernetes_version
from kubernetes.client.models.v1_job import V1Job
from kubernetes.client.models.v1_job_list import V1JobList
from kubernetes.client.models.v1_job_status import V1JobStatus
from kubernetes.client.models.v1_list_meta import V1ListMeta
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from kubernetes.client.models.v1_object_reference import V1ObjectReference

if kubernetes_version >= "13":
    from kubernetes.client.models.core_v1_event import CoreV1Event
else:
    # Ignore type error here due to differen module structures in
    # older kubernetes library versions.
    from kubernetes.client.models.v1_event import V1Event as CoreV1Event  # type: ignore


def test_launcher_from_config(kubeconfig_file):
    resources = {
        "requests": {"memory": "64Mi", "cpu": "250m"},
        "limits": {"memory": "128Mi", "cpu": "500m"},
    }

    default_config = {
        "service_account_name": "webserver-admin",
        "instance_config_map": "dagster-instance",
        "postgres_password_secret": "dagster-postgresql-secret",
        "dagster_home": "/opt/dagster/dagster_home",
        "job_image": "fake_job_image",
        "load_incluster_config": False,
        "kubeconfig_file": kubeconfig_file,
        "resources": resources,
    }

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_k8s",
                "class": "K8sRunLauncher",
                "config": default_config,
            }
        }
    ) as instance:
        run_launcher = instance.run_launcher
        assert isinstance(run_launcher, K8sRunLauncher)
        assert run_launcher.fail_pod_on_run_failure is None
        assert run_launcher.resources == resources
        assert run_launcher.scheduler_name is None
        assert run_launcher.only_allow_user_defined_k8s_config_fields is None
        assert run_launcher.only_allow_user_defined_env_vars is None

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_k8s",
                "class": "K8sRunLauncher",
                "config": merge_dicts(default_config, {"fail_pod_on_run_failure": True}),
            }
        }
    ) as instance:
        run_launcher = instance.run_launcher
        assert isinstance(run_launcher, K8sRunLauncher)
        assert run_launcher.fail_pod_on_run_failure

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_k8s",
                "class": "K8sRunLauncher",
                "config": merge_dicts(
                    default_config,
                    {
                        "only_allow_user_defined_k8s_config_fields": {},
                        "only_allow_user_defined_env_vars": [],
                    },
                ),
            }
        }
    ) as instance:
        run_launcher = instance.run_launcher
        assert isinstance(run_launcher, K8sRunLauncher)
        assert run_launcher.only_allow_user_defined_k8s_config_fields == {}
        assert run_launcher.only_allow_user_defined_env_vars == []

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_k8s",
                "class": "K8sRunLauncher",
                "config": merge_dicts(
                    default_config,
                    {
                        "only_allow_user_defined_k8s_config_fields": {
                            "pod_spec_config": {"image_pull_secrets": True}
                        },
                        "only_allow_user_defined_env_vars": ["FOO_ENV_VAR"],
                    },
                ),
            }
        }
    ) as instance:
        run_launcher = instance.run_launcher
        assert isinstance(run_launcher, K8sRunLauncher)
        assert run_launcher.only_allow_user_defined_k8s_config_fields == {
            "pod_spec_config": {"image_pull_secrets": True}
        }
        assert run_launcher.only_allow_user_defined_env_vars == ["FOO_ENV_VAR"]


def test_launcher_with_container_context(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        env_vars=["FOO_TEST=foo"],
        resources={
            "requests": {"memory": "64Mi", "cpu": "250m"},
            "limits": {"memory": "128Mi", "cpu": "500m"},
        },
        scheduler_name="test-scheduler",
    )

    container_context_config = {
        "k8s": {
            "env_vars": ["BAR_TEST=bar", "BAZ_TEST=baz"],
            "resources": {
                "limits": {"memory": "64Mi", "cpu": "250m"},
                "requests": {"memory": "32Mi", "cpu": "125m"},
            },
            "scheduler_name": "test-scheduler-2",
            "security_context": {"capabilities": {"add": ["SYS_PTRACE"]}},
        }
    }

    # Create fake external job.
    recon_job = reconstructable(fake_job)
    recon_repo = recon_job.repository
    repo_def = recon_repo.get_definition()

    python_origin = recon_job.get_python_origin()
    python_origin = python_origin._replace(
        repository_origin=python_origin.repository_origin._replace(
            container_context=container_context_config,
        )
    )
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            job_name = "demo_job"
            run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=python_origin,
            )
            k8s_run_launcher.register_instance(instance)
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake_job_image"  # ty: ignore[unresolved-attribute]

            # Check that user defined k8s config was passed down to the k8s job.
            mock_method_calls = mock_k8s_client_batch_api.method_calls
            assert len(mock_method_calls) > 0
            method_name, _args, kwargs = mock_method_calls[-1]
            assert method_name == "create_namespaced_job"

            container = kwargs["body"].spec.template.spec.containers[0]

            resources = container.resources.to_dict()
            resources.pop("claims", None)
            assert resources == {
                "limits": {"memory": "64Mi", "cpu": "250m"},
                "requests": {"memory": "32Mi", "cpu": "125m"},
            }
            assert container.security_context.capabilities.add == ["SYS_PTRACE"]

            assert kwargs["body"].spec.template.spec.scheduler_name == "test-scheduler-2"

            env_names = [env.name for env in container.env]

            assert "BAR_TEST" in env_names
            assert "BAZ_TEST" in env_names
            assert "FOO_TEST" in env_names

            args = container.args
            assert (
                args
                == ExecuteRunArgs(
                    job_origin=run.job_code_origin,
                    run_id=run.run_id,
                    instance_ref=instance.get_ref(),
                    set_exit_code_on_failure=None,
                ).get_command_args()
            )

            k8s_run_launcher._only_allow_user_defined_k8s_config_fields = {}  # noqa
            with pytest.raises(
                Exception,
                match="Attempted to create a pod with fields that violated the allowed list",
            ):
                k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            k8s_run_launcher._only_allow_user_defined_k8s_config_fields = {  # noqa
                "container_config": {
                    "resources": True,
                    "security_context": True,
                    "env": True,
                },
                "pod_spec_config": {"scheduler_name": True},
            }
            k8s_run_launcher._only_allow_user_defined_env_vars = ["BAR_TEST"]  # noqa

            run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=python_origin,
            )
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))
            mock_method_calls = mock_k8s_client_batch_api.method_calls
            method_name, _args, kwargs = mock_method_calls[-1]
            assert method_name == "create_namespaced_job"

            container = kwargs["body"].spec.template.spec.containers[0]
            env_names = [env.name for env in container.env]

            assert "BAR_TEST" in env_names
            assert "FOO_TEST" in env_names  # instance-level env vars still set
            assert "BAZ_TEST" not in env_names  # excluded by only_allow_user_defined_env_vars

            k8s_run_launcher._only_allow_user_defined_env_vars = []  # noqa
            run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=python_origin,
            )
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))
            mock_method_calls = mock_k8s_client_batch_api.method_calls
            method_name, _args, kwargs = mock_method_calls[-1]
            assert method_name == "create_namespaced_job"

            container = kwargs["body"].spec.template.spec.containers[0]
            env_names = [env.name for env in container.env]

            assert "FOO_TEST" in env_names
            assert "BAR_TEST" not in env_names  # all user-defined env vars excluded
            assert "BAZ_TEST" not in env_names


@pytest.mark.parametrize("deployment_name", ["test-deployment", None])
def test_launcher_with_k8s_config(kubeconfig_file, deployment_name: str):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        env_vars=[
            "FOO_TEST=foo",
            *(["DAGSTER_CLOUD_DEPLOYMENT_NAME=test-deployment"] if deployment_name else []),
        ],
        scheduler_name="test-scheduler",
        run_k8s_config={
            "container_config": {"command": ["echo", "RUN"], "tty": True},
            "pod_template_spec_metadata": {"namespace": "my_pod_namespace"},
            "pod_spec_config": {"dns_policy": "value"},
            "job_metadata": {
                "namespace": "my_job_value",
            },
            "job_spec_config": {"backoff_limit": 120},
        },
    )

    container_context_config = {
        "k8s": {
            "run_k8s_config": {
                "container_config": {"command": ["echo", "REPLACED"]},
            }
        }
    }

    run_tags = {"dagster-k8s/config": {"container_config": {"working_dir": "my_working_dir"}}}

    # Create fake external job.
    recon_job = reconstructable(fake_job)
    recon_repo = recon_job.repository
    repo_def = recon_repo.get_definition()

    python_origin = recon_job.get_python_origin()
    python_origin = python_origin._replace(
        repository_origin=python_origin.repository_origin._replace(
            container_context=container_context_config,
        )
    )
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            job_name = "demo_job"
            run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=python_origin,
                tags=run_tags,
            )
            k8s_run_launcher.register_instance(instance)
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake_job_image"  # ty: ignore[unresolved-attribute]

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"

        container = kwargs["body"].spec.template.spec.containers[0]

        # config from container context applied
        command = container.command
        assert command == ["echo", "REPLACED"]

        # config from run launcher applied
        assert container.tty

        # config from run tags applied
        assert container.working_dir == "my_working_dir"

        # appropriate labels applied
        labels = kwargs["body"].spec.template.metadata.labels
        assert labels["dagster/code-location"] == "in_process"
        assert labels["dagster/job"] == "fake_job"
        assert labels["dagster/run-id"] == run.run_id
        assert labels.get("dagster/deployment-name") == deployment_name


def test_user_defined_k8s_config_in_run_tags(kubeconfig_file):
    labels = {"foo_label_key": "bar_label_value"}

    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        labels=labels,
        resources={
            "requests": {"memory": "64Mi", "cpu": "250m"},
            "limits": {"memory": "128Mi", "cpu": "500m"},
        },
        scheduler_name="test-scheduler",
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
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            job_name = "demo_job"
            run = create_run_for_test(
                instance,
                job_name=job_name,
                tags=tags,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=fake_remote_job.get_python_origin(),
            )
            k8s_run_launcher.register_instance(instance)
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == expected_image  # ty: ignore[unresolved-attribute]

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

        assert DAGSTER_PG_PASSWORD_ENV_VAR in [env.name for env in container.env]
        assert "DAGSTER_RUN_JOB_NAME" in [env.name for env in container.env]

        assert kwargs["body"].spec.template.spec.scheduler_name == "test-scheduler-2"

        labels = kwargs["body"].spec.template.metadata.labels
        assert labels["foo_label_key"] == "bar_label_value"

        args = container.args
        assert (
            args
            == ExecuteRunArgs(
                job_origin=run.job_code_origin,
                run_id=run.run_id,
                instance_ref=instance.get_ref(),
                set_exit_code_on_failure=None,
            ).get_command_args()
        )


def test_raise_on_error(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        fail_pod_on_run_failure=True,
    )
    # Create fake external job.
    recon_job = reconstructable(fake_job)
    recon_repo = recon_job.repository
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            job_name = "demo_job"
            run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=fake_remote_job.get_python_origin(),
            )
            k8s_run_launcher.register_instance(instance)
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"

        container = kwargs["body"].spec.template.spec.containers[0]
        args = container.args
        assert (
            args
            == ExecuteRunArgs(
                job_origin=run.job_code_origin,
                run_id=run.run_id,
                instance_ref=instance.get_ref(),
                set_exit_code_on_failure=True,
            ).get_command_args()
        )


def test_no_postgres(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    # Create fake external job.
    recon_job = reconstructable(fake_job)
    recon_repo = recon_job.repository
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            job_name = "demo_job"
            run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=fake_remote_job.get_python_origin(),
            )
            k8s_run_launcher.register_instance(instance)
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake_job_image"  # ty: ignore[unresolved-attribute]

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        assert DAGSTER_PG_PASSWORD_ENV_VAR not in [
            env.name for env in kwargs["body"].spec.template.spec.containers[0].env
        ]


@job
def fake_job():
    pass


def test_check_run_health(kubeconfig_file):
    labels = {"foo_label_key": "bar_label_value"}

    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.Mock(spec_set=["read_namespaced_job_status"])

    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        labels=labels,
    )

    # Create fake external job.
    recon_job = reconstructable(fake_job)
    recon_repo = recon_job.repository
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            job_name = "demo_job"

            started_run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=fake_remote_job.get_python_origin(),
                status=DagsterRunStatus.STARTED,
            )
            finished_run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=fake_remote_job.get_python_origin(),
                status=DagsterRunStatus.FAILURE,
            )
            k8s_run_launcher.register_instance(instance)

            mock_k8s_client_batch_api.read_namespaced_job_status.return_value = V1Job(
                status=V1JobStatus(failed=0, succeeded=0, active=0)
            )

            health = k8s_run_launcher.check_run_worker_health(started_run)
            assert health.status == WorkerStatus.RUNNING, health.msg

            health = k8s_run_launcher.check_run_worker_health(finished_run)
            assert health.status == WorkerStatus.RUNNING, health.msg

            mock_k8s_client_batch_api.read_namespaced_job_status.return_value = V1Job(
                status=V1JobStatus(failed=0, succeeded=1, active=0)
            )

            health = k8s_run_launcher.check_run_worker_health(started_run)
            assert health.status == WorkerStatus.FAILED, health.msg

            health = k8s_run_launcher.check_run_worker_health(finished_run)
            assert health.status == WorkerStatus.SUCCESS, health.msg

            mock_k8s_client_batch_api.read_namespaced_job_status.return_value = V1Job(
                status=V1JobStatus(failed=1, succeeded=0, active=0)
            )

            health = k8s_run_launcher.check_run_worker_health(started_run)
            assert health.status == WorkerStatus.FAILED, health.msg

            health = k8s_run_launcher.check_run_worker_health(finished_run)
            assert health.status == WorkerStatus.FAILED, health.msg

            mock_k8s_client_batch_api.read_namespaced_job_status.return_value = V1Job(
                status=V1JobStatus(failed=1, succeeded=0, active=1)
            )

            health = k8s_run_launcher.check_run_worker_health(started_run)
            assert health.status == WorkerStatus.RUNNING, health.msg

            health = k8s_run_launcher.check_run_worker_health(finished_run)
            assert health.status == WorkerStatus.RUNNING, health.msg

            mock_k8s_client_batch_api.read_namespaced_job_status.return_value = V1Job(
                status=V1JobStatus(failed=1, succeeded=1, active=0)
            )

            health = k8s_run_launcher.check_run_worker_health(started_run)
            assert health.status == WorkerStatus.FAILED, health.msg

            health = k8s_run_launcher.check_run_worker_health(finished_run)
            assert health.status == WorkerStatus.SUCCESS, health.msg

            mock_k8s_client_batch_api.read_namespaced_job_status.side_effect = (
                kubernetes.client.rest.ApiException(status=404, reason="Not Found")
            )

            finished_k8s_job_name = get_job_name_from_run_id(finished_run.run_id)

            health = k8s_run_launcher.check_run_worker_health(finished_run)

            assert (
                health.status == WorkerStatus.UNKNOWN
                and health.msg == f"Job {finished_k8s_job_name} could not be found"
            )


def test_get_run_worker_debug_info(kubeconfig_file):
    labels = {"foo_label_key": "bar_label_value"}

    mock_k8s_client_batch_api = mock.Mock(
        spec_set=["read_namespaced_job_status", "list_namespaced_job"]
    )
    mock_k8s_client_core_api = mock.Mock(spec_set=["list_namespaced_pod", "list_namespaced_event"])

    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        k8s_client_core_api=mock_k8s_client_core_api,
        labels=labels,
    )

    # Launch the run in a fake Dagster instance.
    job_name = "demo_job"

    # Create fake external job.
    recon_job = reconstructable(fake_job)
    recon_repo = recon_job.repository
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    list_namespaced_pod_response = mock.Mock(spec_set=["items"])
    list_namespaced_pod_response.items = []
    mock_k8s_client_core_api.list_namespaced_pod.return_value = list_namespaced_pod_response

    list_namespaced_job_response = mock.Mock(spec_set=["items"])
    list_namespaced_job_response.items = [
        V1Job(
            metadata=V1ObjectMeta(name="hello-world"),
            status=V1JobStatus(
                failed=None,
                succeeded=None,
                active=None,
                start_time=datetime.now(),
            ),
        ),
    ]
    mock_k8s_client_batch_api.list_namespaced_job.return_value = list_namespaced_job_response

    list_namespaced_job_event_response = mock.Mock(spec_set=["items"])
    list_namespaced_job_event_response.items = [
        CoreV1Event(
            metadata=V1ObjectMeta(name="event/demo_job"),
            reason="Testing",
            message="test message",
            involved_object=V1ObjectReference(name=job_name),
        )
    ]
    mock_k8s_client_core_api.list_namespaced_event.return_value = list_namespaced_job_event_response

    with instance_for_test() as instance:
        k8s_run_launcher.register_instance(instance)

        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repo_handle = RepositoryHandle.from_location(
                repository_name=repo_def.name,
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )

            started_run = create_run_for_test(
                instance,
                job_name=job_name,
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=fake_remote_job.get_python_origin(),
                status=DagsterRunStatus.STARTING,
            )

            debug_info = k8s_run_launcher.get_run_worker_debug_info(started_run)
            running_job_name = get_job_name_from_run_id(started_run.run_id)
            assert f"Debug information for job {running_job_name}" in debug_info  # ty: ignore[unsupported-operator]
            assert "Job status:" in debug_info  # ty: ignore[unsupported-operator]
            assert "Testing: test message" in debug_info  # ty: ignore[unsupported-operator]


def _job_list(items, continue_token):
    return V1JobList(items=items, metadata=V1ListMeta(_continue=continue_token))


def _run_worker_job(job_name: str, status: V1JobStatus) -> V1Job:
    return V1Job(metadata=V1ObjectMeta(name=job_name), status=status)


def test_check_run_health_batch(kubeconfig_file):
    mock_k8s_client_batch_api = mock.Mock(
        spec_set=["list_namespaced_job", "read_namespaced_job_status"]
    )
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    with instance_for_test() as instance:
        k8s_run_launcher.register_instance(instance)
        running_run, failed_run, missing_run = (
            create_run_for_test(instance, job_name="demo_job", status=DagsterRunStatus.STARTED)
            for _ in range(3)
        )

        first_page = _job_list(
            items=[
                _run_worker_job(
                    get_job_name_from_run_id(running_run.run_id),
                    V1JobStatus(active=1, failed=0, succeeded=0),
                )
            ],
            continue_token="next-page",
        )
        second_page = _job_list(
            items=[
                _run_worker_job(
                    get_job_name_from_run_id(failed_run.run_id),
                    V1JobStatus(active=0, failed=1, succeeded=0),
                )
            ],
            continue_token=None,
        )
        mock_k8s_client_batch_api.list_namespaced_job.side_effect = [first_page, second_page]
        mock_k8s_client_batch_api.read_namespaced_job_status.side_effect = (
            kubernetes.client.rest.ApiException(status=404, reason="Not Found")
        )

        results = k8s_run_launcher.check_run_worker_health_batch(
            [running_run, failed_run, missing_run]
        )

        assert results[running_run.run_id].status == WorkerStatus.RUNNING
        assert results[failed_run.run_id].status == WorkerStatus.FAILED
        assert results[missing_run.run_id].status == WorkerStatus.UNKNOWN
        assert results[missing_run.run_id].msg == (
            f"Job {get_job_name_from_run_id(missing_run.run_id)} could not be found"
        )

        list_calls = mock_k8s_client_batch_api.list_namespaced_job.call_args_list
        assert len(list_calls) == 2, list_calls
        run_ids = ",".join(sorted(run.run_id for run in (running_run, failed_run, missing_run)))
        assert list_calls[0].kwargs["label_selector"] == (
            f"app.kubernetes.io/component=run_worker,dagster/run-id in ({run_ids})"
        )
        assert list_calls[0].kwargs["resource_version"] == "0"
        assert list_calls[1].kwargs["_continue"] == "next-page"
        assert "resource_version" not in list_calls[1].kwargs
        # Only the Job missing from the list is read individually.
        mock_k8s_client_batch_api.read_namespaced_job_status.assert_called_once_with(
            get_job_name_from_run_id(missing_run.run_id), namespace=mock.ANY
        )


def test_check_run_health_batch_list_error(kubeconfig_file):
    mock_k8s_client_batch_api = mock.Mock(
        spec_set=["list_namespaced_job", "read_namespaced_job_status"]
    )
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    with instance_for_test() as instance:
        k8s_run_launcher.register_instance(instance)
        runs = [
            create_run_for_test(instance, job_name="demo_job", status=DagsterRunStatus.STARTED)
            for _ in range(2)
        ]
        mock_k8s_client_batch_api.list_namespaced_job.side_effect = (
            kubernetes.client.rest.ApiException(status=403, reason="Forbidden")
        )

        mock_k8s_client_batch_api.read_namespaced_job_status.return_value = V1Job(
            status=V1JobStatus(active=1, failed=0, succeeded=0)
        )
        results = k8s_run_launcher.check_run_worker_health_batch(runs)
        assert results == {}

        # Monitoring callers check missing results individually. LIST permission is not
        # required for a deployment whose previous GET-based checks were healthy.
        fallback_results = [k8s_run_launcher.check_run_worker_health(run) for run in runs]
        assert all(result.status == WorkerStatus.RUNNING for result in fallback_results)
        assert mock_k8s_client_batch_api.read_namespaced_job_status.call_count == len(runs)


def test_check_run_health_batch_splits_run_ids(kubeconfig_file, monkeypatch):
    monkeypatch.setattr(launcher_module, "RUN_IDS_PER_JOB_LIST", 2)
    mock_k8s_client_batch_api = mock.Mock(spec_set=["list_namespaced_job"])
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    with instance_for_test() as instance:
        k8s_run_launcher.register_instance(instance)
        runs = [
            create_run_for_test(instance, job_name="demo_job", status=DagsterRunStatus.STARTED)
            for _ in range(5)
        ]
        mock_k8s_client_batch_api.list_namespaced_job.return_value = _job_list(
            items=[
                _run_worker_job(
                    get_job_name_from_run_id(run.run_id),
                    V1JobStatus(active=1, failed=0, succeeded=0),
                )
                for run in runs
            ],
            continue_token=None,
        )

        results = k8s_run_launcher.check_run_worker_health_batch(runs)

        assert {result.status for result in results.values()} == {WorkerStatus.RUNNING}
        assert set(results) == {run.run_id for run in runs}
        list_calls = mock_k8s_client_batch_api.list_namespaced_job.call_args_list
        assert len(list_calls) == 3
        selected_run_ids = [
            call.kwargs["label_selector"].split(" in (")[1].rstrip(")").split(",")
            for call in list_calls
        ]
        assert [len(ids) for ids in selected_run_ids] == [2, 2, 1]
        assert sorted(run_id for ids in selected_run_ids for run_id in ids) == sorted(
            run.run_id for run in runs
        )


class _CustomHealthK8sRunLauncher(K8sRunLauncher):
    def check_run_worker_health(self, run):
        return super().check_run_worker_health(run)


def test_check_run_health_batch_skipped_when_single_check_overridden(kubeconfig_file):
    mock_k8s_client_batch_api = mock.Mock(spec_set=["list_namespaced_job"])
    k8s_run_launcher = _CustomHealthK8sRunLauncher(
        service_account_name="webserver-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )
    with instance_for_test() as instance:
        k8s_run_launcher.register_instance(instance)
        run = create_run_for_test(instance, job_name="demo_job", status=DagsterRunStatus.STARTED)

        assert k8s_run_launcher.check_run_worker_health_batch([run]) == {}
        mock_k8s_client_batch_api.list_namespaced_job.assert_not_called()

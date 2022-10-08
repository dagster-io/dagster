import json
from unittest import mock

from dagster_k8s import K8sRunLauncher
from dagster_k8s.job import DAGSTER_PG_PASSWORD_ENV_VAR, UserDefinedDagsterK8sConfig
from kubernetes.client.models.v1_job import V1Job
from kubernetes.client.models.v1_job_status import V1JobStatus

from dagster import reconstructable
from dagster._core.host_representation import RepositoryHandle
from dagster._core.launcher import LaunchRunContext
from dagster._core.launcher.base import WorkerStatus
from dagster._core.storage.tags import DOCKER_IMAGE_TAG
from dagster._core.test_utils import (
    create_run_for_test,
    in_process_test_workspace,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.types import ExecuteRunArgs
from dagster._legacy import pipeline
from dagster._utils import merge_dicts
from dagster._utils.hosted_user_process import external_pipeline_from_recon_pipeline


def test_launcher_from_config(kubeconfig_file):

    resources = {
        "requests": {"memory": "64Mi", "cpu": "250m"},
        "limits": {"memory": "128Mi", "cpu": "500m"},
    }

    default_config = {
        "service_account_name": "dagit-admin",
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
        assert run_launcher.scheduler_name == None
        assert run_launcher.tolerations == []
        assert run_launcher.node_selector == {}
        assert run_launcher.pod_security_context == {}

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


def test_launcher_with_container_context(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="dagit-admin",
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
        tolerations=[
            {
                "key": "my_key1",
                "operator": "my_operator1",
                "effect": "my_effect1",
            }
        ],
    )

    container_context_config = {
        "k8s": {
            "env_vars": ["BAR_TEST=bar"],
            "resources": {
                "limits": {"memory": "64Mi", "cpu": "250m"},
                "requests": {"memory": "32Mi", "cpu": "125m"},
            },
            "scheduler_name": "test-scheduler-2",
            "tolerations": [
                {
                    "key": "my_key2",
                    "operator": "my_operator2",
                    "effect": "my_effect2",
                }
            ],
        }
    }

    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    repo_def = recon_repo.get_definition()

    python_origin = recon_pipeline.get_python_origin()
    python_origin = python_origin._replace(
        repository_origin=python_origin.repository_origin._replace(
            container_context=container_context_config,
        )
    )
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_repository_location(workspace.repository_location_names[0])
            repo_handle = RepositoryHandle(
                repository_name=repo_def.name,
                repository_location=location,
            )
            fake_external_pipeline = external_pipeline_from_recon_pipeline(
                recon_pipeline,
                solid_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=fake_external_pipeline.get_external_origin(),
                pipeline_code_origin=python_origin,
            )
            k8s_run_launcher.register_instance(instance)
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake_job_image"

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"

        container = kwargs["body"].spec.template.spec.containers[0]

        resources = container.resources
        assert resources.to_dict() == {
            "limits": {"memory": "64Mi", "cpu": "250m"},
            "requests": {"memory": "32Mi", "cpu": "125m"},
        }

        assert kwargs["body"].spec.template.spec.scheduler_name == "test-scheduler-2"

        tolerations = kwargs["body"].spec.template.spec.tolerations
        assert len(tolerations) == 2
        tolerations = sorted(tolerations, key=lambda t: t.key)  # stabilize list order

        assert tolerations[0].to_dict() == {
            "key": "my_key1",
            "operator": "my_operator1",
            "effect": "my_effect1",
            "toleration_seconds": None,
            "value": None,
        }

        assert tolerations[1].to_dict() == {
            "key": "my_key2",
            "operator": "my_operator2",
            "effect": "my_effect2",
            "toleration_seconds": None,
            "value": None,
        }

        env_names = [env.name for env in container.env]

        assert "BAR_TEST" in env_names
        assert "FOO_TEST" in env_names

        args = container.args
        assert (
            args
            == ExecuteRunArgs(
                pipeline_origin=run.pipeline_code_origin,
                pipeline_run_id=run.run_id,
                instance_ref=instance.get_ref(),
                set_exit_code_on_failure=None,
            ).get_command_args()
        )


def test_user_defined_k8s_config_in_run_tags(kubeconfig_file):

    labels = {"foo_label_key": "bar_label_value"}

    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="dagit-admin",
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
    expected_resources = {
        "requests": {"cpu": "250m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "2560Mi"},
    }
    user_defined_k8s_config = UserDefinedDagsterK8sConfig(
        container_config={"resources": expected_resources},
        pod_spec_config={"scheduler_name": "test-scheduler-2"},
    )
    user_defined_k8s_config_json = json.dumps(user_defined_k8s_config.to_dict())
    tags = {"dagster-k8s/config": user_defined_k8s_config_json}

    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_repository_location(workspace.repository_location_names[0])
            repo_handle = RepositoryHandle(
                repository_name=repo_def.name,
                repository_location=location,
            )
            fake_external_pipeline = external_pipeline_from_recon_pipeline(
                recon_pipeline,
                solid_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                tags=tags,
                external_pipeline_origin=fake_external_pipeline.get_external_origin(),
                pipeline_code_origin=fake_external_pipeline.get_python_origin(),
            )
            k8s_run_launcher.register_instance(instance)
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake_job_image"

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"

        container = kwargs["body"].spec.template.spec.containers[0]

        job_resources = container.resources
        assert job_resources.to_dict() == expected_resources
        assert DAGSTER_PG_PASSWORD_ENV_VAR in [env.name for env in container.env]

        assert kwargs["body"].spec.template.spec.scheduler_name == "test-scheduler-2"

        labels = kwargs["body"].spec.template.metadata.labels
        assert labels["foo_label_key"] == "bar_label_value"

        args = container.args
        assert (
            args
            == ExecuteRunArgs(
                pipeline_origin=run.pipeline_code_origin,
                pipeline_run_id=run.run_id,
                instance_ref=instance.get_ref(),
                set_exit_code_on_failure=None,
            ).get_command_args()
        )


def test_raise_on_error(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="dagit-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        fail_pod_on_run_failure=True,
    )
    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_repository_location(workspace.repository_location_names[0])
            repo_handle = RepositoryHandle(
                repository_name=repo_def.name,
                repository_location=location,
            )
            fake_external_pipeline = external_pipeline_from_recon_pipeline(
                recon_pipeline,
                solid_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=fake_external_pipeline.get_external_origin(),
                pipeline_code_origin=fake_external_pipeline.get_python_origin(),
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
                pipeline_origin=run.pipeline_code_origin,
                pipeline_run_id=run.run_id,
                instance_ref=instance.get_ref(),
                set_exit_code_on_failure=True,
            ).get_command_args()
        )


def test_no_postgres(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="dagit-admin",
        instance_config_map="dagster-instance",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_repository_location(workspace.repository_location_names[0])
            repo_handle = RepositoryHandle(
                repository_name=repo_def.name,
                repository_location=location,
            )
            fake_external_pipeline = external_pipeline_from_recon_pipeline(
                recon_pipeline,
                solid_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=fake_external_pipeline.get_external_origin(),
                pipeline_code_origin=fake_external_pipeline.get_python_origin(),
            )
            k8s_run_launcher.register_instance(instance)
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            updated_run = instance.get_run_by_id(run.run_id)
            assert updated_run.tags[DOCKER_IMAGE_TAG] == "fake_job_image"

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        assert DAGSTER_PG_PASSWORD_ENV_VAR not in [
            env.name for env in kwargs["body"].spec.template.spec.containers[0].env
        ]


@pipeline
def fake_pipeline():
    pass


def test_check_run_health(kubeconfig_file):

    labels = {"foo_label_key": "bar_label_value"}

    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.Mock(spec_set=["read_namespaced_job"])
    mock_k8s_client_batch_api.read_namespaced_job.side_effect = [
        V1Job(status=V1JobStatus(failed=0, succeeded=0)),
        V1Job(status=V1JobStatus(failed=0, succeeded=1)),
        V1Job(status=V1JobStatus(failed=1, succeeded=0)),
    ]
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="dagit-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        labels=labels,
    )

    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    repo_def = recon_repo.get_definition()
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__)

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_repository_location(workspace.repository_location_names[0])
            repo_handle = RepositoryHandle(
                repository_name=repo_def.name,
                repository_location=location,
            )
            fake_external_pipeline = external_pipeline_from_recon_pipeline(
                recon_pipeline,
                solid_selection=None,
                repository_handle=repo_handle,
            )

            # Launch the run in a fake Dagster instance.
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=fake_external_pipeline.get_external_origin(),
                pipeline_code_origin=fake_external_pipeline.get_python_origin(),
            )
            k8s_run_launcher.register_instance(instance)

            # same order as side effects
            assert k8s_run_launcher.check_run_worker_health(run).status == WorkerStatus.RUNNING
            assert k8s_run_launcher.check_run_worker_health(run).status == WorkerStatus.SUCCESS
            assert k8s_run_launcher.check_run_worker_health(run).status == WorkerStatus.FAILED

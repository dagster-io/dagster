import json
from unittest import mock

from dagster import pipeline, reconstructable
from dagster.core.host_representation import RepositoryHandle
from dagster.core.launcher import LaunchRunContext
from dagster.core.storage.tags import DOCKER_IMAGE_TAG
from dagster.core.test_utils import (
    create_run_for_test,
    in_process_test_workspace,
    instance_for_test,
)
from dagster.utils.hosted_user_process import external_pipeline_from_recon_pipeline
from dagster_k8s import K8sRunLauncher
from dagster_k8s.job import DAGSTER_PG_PASSWORD_ENV_VAR, UserDefinedDagsterK8sConfig
from dagster_test.test_project import ReOriginatedExternalPipelineForTest


def test_user_defined_k8s_config_in_run_tags(kubeconfig_file):
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
    )

    # Construct Dagster run tags with user defined k8s config.
    expected_resources = {
        "requests": {"cpu": "250m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "2560Mi"},
    }
    user_defined_k8s_config = UserDefinedDagsterK8sConfig(
        container_config={"resources": expected_resources},
    )
    user_defined_k8s_config_json = json.dumps(user_defined_k8s_config.to_dict())
    tags = {"dagster-k8s/config": user_defined_k8s_config_json}

    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    repo_def = recon_repo.get_definition()
    with instance_for_test() as instance:
        with in_process_test_workspace(instance, recon_repo) as workspace:
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
        job_resources = kwargs["body"].spec.template.spec.containers[0].resources
        assert job_resources == expected_resources
        assert DAGSTER_PG_PASSWORD_ENV_VAR in [
            env.name for env in kwargs["body"].spec.template.spec.containers[0].env
        ]


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

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, recon_repo) as workspace:
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


def test_k8s_executor_config_override(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    k8s_run_launcher = K8sRunLauncher(
        service_account_name="dagit-admin",
        instance_config_map="dagster-instance",
        dagster_home="/opt/dagster/dagster_home",
        job_image="fake_launcher_job_image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        env_config_maps=["fake_launcher_env_configmap"],
        env_secrets=["fake_launcher_env_secret"],
        env_vars=["FAKE_LAUNCHER_ENV_VAR"],
    )

    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    repo_def = recon_repo.get_definition()
    with instance_for_test() as instance:
        with in_process_test_workspace(instance, recon_repo) as workspace:
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
            reoriginated_pipeline = ReOriginatedExternalPipelineForTest(
                fake_external_pipeline, container_image="fake_repository_origin_image"
            )

            k8s_run_launcher.register_instance(instance)

            # Launch the run with the k8s_run_launcher job_image
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=fake_external_pipeline.get_external_origin(),
                pipeline_code_origin=fake_external_pipeline.get_python_origin(),
            )
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            # Launch the run with a custom repository_origin.container_image
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
                pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
            )
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            # Launch the run with the k8s_run_launcher job_image and a custom execution job_image
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=fake_external_pipeline.get_external_origin(),
                pipeline_code_origin=fake_external_pipeline.get_python_origin(),
                run_config={
                    "execution": {
                        "k8s": {
                            "config": {
                                "job_image": "fake_execution_job_image",
                            }
                        }
                    }
                },
            )
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            # Launch the run with a custom repository_origin.container_image and a custom execution job_image
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=reoriginated_pipeline.get_external_origin(),
                pipeline_code_origin=reoriginated_pipeline.get_python_origin(),
                run_config={
                    "execution": {
                        "k8s": {
                            "config": {
                                "job_image": "fake_execution_job_image",
                            }
                        }
                    }
                },
            )
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

            # Launch the run with the env from the execution config.
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_name,
                external_pipeline_origin=fake_external_pipeline.get_external_origin(),
                pipeline_code_origin=fake_external_pipeline.get_python_origin(),
                run_config={
                    "execution": {
                        "k8s": {
                            "config": {
                                "env_config_maps": ["fake_execution_env_configmap"],
                                "env_secrets": ["fake_execution_env_secret"],
                                "env_vars": ["FAKE_EXECUTION_ENV_VAR"],
                            }
                        }
                    }
                },
            )
            k8s_run_launcher.launch_run(LaunchRunContext(run, workspace))

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0

        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        assert kwargs["body"].spec.template.spec.containers[0].image == "fake_launcher_job_image"

        method_name, _args, kwargs = mock_method_calls[1]
        assert method_name == "create_namespaced_job"
        assert (
            kwargs["body"].spec.template.spec.containers[0].image == "fake_repository_origin_image"
        )

        method_name, _args, kwargs = mock_method_calls[2]
        assert method_name == "create_namespaced_job"
        assert kwargs["body"].spec.template.spec.containers[0].image == "fake_execution_job_image"

        method_name, _args, kwargs = mock_method_calls[3]
        assert method_name == "create_namespaced_job"
        assert kwargs["body"].spec.template.spec.containers[0].image == "fake_execution_job_image"

        method_name, _args, kwargs = mock_method_calls[4]
        assert method_name == "create_namespaced_job"
        env_from = kwargs["body"].spec.template.spec.containers[0].env_from
        config_map_names = {env.config_map_ref.name for env in env_from if env.config_map_ref}
        secret_names = {env.secret_ref.name for env in env_from if env.secret_ref}
        env_var_names = [env.name for env in kwargs["body"].spec.template.spec.containers[0].env]
        assert "fake_launcher_env_configmap" in config_map_names
        assert "fake_execution_env_configmap" in config_map_names
        assert "fake_launcher_env_secret" in secret_names
        assert "fake_execution_env_secret" in secret_names
        assert "FAKE_LAUNCHER_ENV_VAR" in env_var_names
        assert "FAKE_EXECUTION_ENV_VAR" in env_var_names


@pipeline
def fake_pipeline():
    pass

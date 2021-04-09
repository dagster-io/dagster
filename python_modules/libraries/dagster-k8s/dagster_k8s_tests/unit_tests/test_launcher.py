import json
from unittest import mock

from dagster import pipeline, reconstructable
from dagster.core.host_representation import InProcessRepositoryLocationOrigin, RepositoryHandle
from dagster.core.storage.tags import DOCKER_IMAGE_TAG
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.utils.hosted_user_process import external_pipeline_from_recon_pipeline
from dagster_k8s import K8sRunLauncher
from dagster_k8s.job import DAGSTER_PG_PASSWORD_ENV_VAR, UserDefinedDagsterK8sConfig


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
    location_origin = InProcessRepositoryLocationOrigin(recon_repo)
    with location_origin.create_location() as location:
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
        with instance_for_test() as instance:
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(instance, pipeline_name=pipeline_name, tags=tags)
            k8s_run_launcher.register_instance(instance)
            run = k8s_run_launcher.launch_run(run, fake_external_pipeline)

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
    location_origin = InProcessRepositoryLocationOrigin(recon_repo)
    with location_origin.create_location() as location:
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
        with instance_for_test() as instance:
            pipeline_name = "demo_pipeline"
            run = create_run_for_test(instance, pipeline_name=pipeline_name)
            k8s_run_launcher.register_instance(instance)
            run = k8s_run_launcher.launch_run(run, fake_external_pipeline)

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

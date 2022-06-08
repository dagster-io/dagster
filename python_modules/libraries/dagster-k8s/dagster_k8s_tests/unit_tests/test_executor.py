# pylint: disable=redefined-outer-name
import json
from unittest import mock

import pytest
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.executor import K8sStepHandler, k8s_job_executor
from dagster_k8s.job import UserDefinedDagsterK8sConfig

from dagster import execute_pipeline, pipeline, solid
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.definitions.reconstruct import reconstructable
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.executor.init import InitExecutorContext
from dagster.core.executor.step_delegating.step_handler.base import StepHandlerContext
from dagster.core.storage.fs_io_manager import fs_io_manager
from dagster.core.test_utils import create_run_for_test, environ, instance_for_test
from dagster.grpc.types import ExecuteStepArgs


@solid
def foo():
    return 1


@pipeline(
    mode_defs=[
        ModeDefinition(
            executor_defs=[k8s_job_executor], resource_defs={"io_manager": fs_io_manager}
        )
    ]
)
def bar():
    foo()


@pytest.fixture
def python_origin_with_container_context():
    container_context_config = {
        "k8s": {
            "env_vars": ["BAZ_TEST"],
            "resources": {
                "requests": {"cpu": "256m", "memory": "128Mi"},
                "limits": {"cpu": "1000m", "memory": "2000Mi"},
            },
        }
    }

    python_origin = reconstructable(bar).get_python_origin()
    return python_origin._replace(
        repository_origin=python_origin.repository_origin._replace(
            container_context=container_context_config,
        )
    )


def test_requires_k8s_launcher_fail():
    with instance_for_test() as instance:
        with pytest.raises(
            DagsterUnmetExecutorRequirementsError,
            match="This engine is only compatible with a K8sRunLauncher",
        ):
            execute_pipeline(reconstructable(bar), instance=instance)


def test_executor_init(k8s_run_launcher_instance):

    resources = {
        "requests": {"memory": "64Mi", "cpu": "250m"},
        "limits": {"memory": "128Mi", "cpu": "500m"},
    }

    executor = k8s_job_executor.executor_creation_fn(
        InitExecutorContext(
            job=InMemoryPipeline(bar),
            executor_def=k8s_job_executor,
            executor_config={
                "env_vars": ["FOO_TEST"],
                "retries": {},
                "resources": resources,
            },
            instance=k8s_run_launcher_instance,
        )
    )

    run = create_run_for_test(
        k8s_run_launcher_instance,
        pipeline_name="bar",
        pipeline_code_origin=reconstructable(bar).get_python_origin(),
    )

    step_handler_context = StepHandlerContext(
        k8s_run_launcher_instance,
        ExecuteStepArgs(reconstructable(bar).get_python_origin(), run.run_id, ["foo_solid"]),
        {"foo_solid": {}},
    )

    # env vars from both launcher and the executor
    # pylint: disable=protected-access
    assert sorted(
        executor._step_handler._get_container_context(step_handler_context).env_vars
    ) == sorted(
        [
            "FOO_TEST",
            "BAR_TEST",
        ]
    )

    assert sorted(
        executor._step_handler._get_container_context(step_handler_context).resources
    ) == sorted(resources)


def test_executor_init_container_context(
    k8s_run_launcher_instance, python_origin_with_container_context
):
    executor = k8s_job_executor.executor_creation_fn(
        InitExecutorContext(
            job=InMemoryPipeline(bar),
            executor_def=k8s_job_executor,
            executor_config={"env_vars": ["FOO_TEST"], "retries": {}, "max_concurrent": 4},
            instance=k8s_run_launcher_instance,
        )
    )

    run = create_run_for_test(
        k8s_run_launcher_instance,
        pipeline_name="bar",
        pipeline_code_origin=python_origin_with_container_context,
    )

    step_handler_context = StepHandlerContext(
        k8s_run_launcher_instance,
        ExecuteStepArgs(reconstructable(bar).get_python_origin(), run.run_id, ["foo_solid"]),
        {"foo_solid": {}},
    )

    # env vars from both launcher and the executor
    # pylint: disable=protected-access
    assert sorted(
        executor._step_handler._get_container_context(step_handler_context).env_vars
    ) == sorted(
        [
            "BAR_TEST",
            "FOO_TEST",
            "BAZ_TEST",
        ]
    )
    assert executor._max_concurrent == 4
    assert sorted(
        executor._step_handler._get_container_context(step_handler_context).resources
    ) == sorted(
        python_origin_with_container_context.repository_origin.container_context["k8s"]["resources"]
    )


@pytest.fixture
def k8s_instance(kubeconfig_file):
    default_config = {
        "service_account_name": "dagit-admin",
        "instance_config_map": "dagster-instance",
        "postgres_password_secret": "dagster-postgresql-secret",
        "dagster_home": "/opt/dagster/dagster_home",
        "job_image": "fake_job_image",
        "load_incluster_config": False,
        "kubeconfig_file": kubeconfig_file,
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
        yield instance


def test_step_handler(kubeconfig_file, k8s_instance):

    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sStepHandler(
        image="bizbuz",
        container_context=K8sContainerContext(
            namespace="foo",
        ),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    run = create_run_for_test(
        k8s_instance,
        pipeline_name="bar",
        pipeline_code_origin=reconstructable(bar).get_python_origin(),
    )
    handler.launch_step(
        StepHandlerContext(
            k8s_instance,
            ExecuteStepArgs(reconstructable(bar).get_python_origin(), run.run_id, ["foo_solid"]),
            {"foo_solid": {}},
        )
    )

    # Check that user defined k8s config was passed down to the k8s job.
    mock_method_calls = mock_k8s_client_batch_api.method_calls
    assert len(mock_method_calls) > 0
    method_name, _args, kwargs = mock_method_calls[0]
    assert method_name == "create_namespaced_job"
    assert kwargs["body"].spec.template.spec.containers[0].image == "bizbuz"


def test_step_handler_user_defined_config(kubeconfig_file, k8s_instance):

    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sStepHandler(
        image="bizbuz",
        container_context=K8sContainerContext(
            namespace="foo",
            env_vars=["FOO_TEST"],
            resources={
                "requests": {"cpu": "128m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "1000Mi"},
            },
        ),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    # Construct Dagster solid tags with user defined k8s config.
    expected_resources = {
        "limits": {"cpu": "500m", "memory": "2560Mi"},
        "requests": {"cpu": "250m", "memory": "64Mi"},
    }
    user_defined_k8s_config = UserDefinedDagsterK8sConfig(
        container_config={"resources": expected_resources},
    )
    user_defined_k8s_config_json = json.dumps(user_defined_k8s_config.to_dict())
    tags = {"dagster-k8s/config": user_defined_k8s_config_json}

    with environ({"FOO_TEST": "bar"}):
        run = create_run_for_test(
            k8s_instance,
            pipeline_name="bar",
            pipeline_code_origin=reconstructable(bar).get_python_origin(),
        )
        handler.launch_step(
            StepHandlerContext(
                k8s_instance,
                ExecuteStepArgs(
                    reconstructable(bar).get_python_origin(), run.run_id, ["foo_solid"]
                ),
                {"foo_solid": tags},
            )
        )

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        assert kwargs["body"].spec.template.spec.containers[0].image == "bizbuz"
        job_resources = kwargs["body"].spec.template.spec.containers[0].resources
        assert job_resources.to_dict() == expected_resources

        env_vars = {
            env.name: env.value for env in kwargs["body"].spec.template.spec.containers[0].env
        }
        assert env_vars["FOO_TEST"] == "bar"


def test_step_handler_image_override(kubeconfig_file, k8s_instance):

    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sStepHandler(
        image="bizbuz",
        container_context=K8sContainerContext(namespace="foo"),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    # Construct Dagster solid tags with user defined k8s config.
    user_defined_k8s_config = UserDefinedDagsterK8sConfig(
        container_config={"image": "new-image"},
    )
    user_defined_k8s_config_json = json.dumps(user_defined_k8s_config.to_dict())
    tags = {"dagster-k8s/config": user_defined_k8s_config_json}

    run = create_run_for_test(
        k8s_instance,
        pipeline_name="bar",
        pipeline_code_origin=reconstructable(bar).get_python_origin(),
    )
    handler.launch_step(
        StepHandlerContext(
            k8s_instance,
            ExecuteStepArgs(reconstructable(bar).get_python_origin(), run.run_id, ["foo_solid"]),
            {"foo_solid": tags},
        )
    )

    # Check that user defined k8s config was passed down to the k8s job.
    mock_method_calls = mock_k8s_client_batch_api.method_calls
    assert len(mock_method_calls) > 0
    method_name, _args, kwargs = mock_method_calls[0]
    assert method_name == "create_namespaced_job"
    assert kwargs["body"].spec.template.spec.containers[0].image == "new-image"


def test_step_handler_with_container_context(
    kubeconfig_file, k8s_instance, python_origin_with_container_context
):
    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sStepHandler(
        image="bizbuz",
        container_context=K8sContainerContext(
            namespace="foo",
            env_vars=["FOO_TEST"],
        ),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    with environ({"FOO_TEST": "bar", "BAZ_TEST": "blergh"}):
        # Additional env vars come from container context on the run
        run = create_run_for_test(
            k8s_instance,
            pipeline_name="bar",
            pipeline_code_origin=python_origin_with_container_context,
        )
        handler.launch_step(
            StepHandlerContext(
                k8s_instance,
                ExecuteStepArgs(python_origin_with_container_context, run.run_id, ["foo_solid"]),
                {"foo_solid": {}},
            )
        )

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        assert kwargs["body"].spec.template.spec.containers[0].image == "bizbuz"

        envs = {env.name: env.value for env in kwargs["body"].spec.template.spec.containers[0].env}

        assert envs["FOO_TEST"] == "bar"
        assert envs["BAZ_TEST"] == "blergh"

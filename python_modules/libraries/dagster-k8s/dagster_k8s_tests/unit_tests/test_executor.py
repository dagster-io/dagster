import json
from unittest import mock

import pytest
from dagster import execute_pipeline, pipeline, solid
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.reconstructable import reconstructable
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.executor.step_delegating.step_handler.base import StepHandlerContext
from dagster.core.storage.fs_io_manager import fs_io_manager
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.grpc.types import ExecuteStepArgs
from dagster_k8s.executor import K8sStepHandler, k8s_job_executor
from dagster_k8s.job import DagsterK8sJobConfig, UserDefinedDagsterK8sConfig


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


def test_requires_k8s_launcher_fail():
    with instance_for_test() as instance:
        with pytest.raises(
            DagsterUnmetExecutorRequirementsError,
            match="This engine is only compatible with a K8sRunLauncher",
        ):
            execute_pipeline(reconstructable(bar), instance=instance)


def test_step_handler(kubeconfig_file):

    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sStepHandler(
        job_config=DagsterK8sJobConfig(instance_config_map="foobar", job_image="bizbuz"),
        job_namespace="foo",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    with instance_for_test() as instance:
        run = create_run_for_test(
            instance,
            pipeline_name="bar",
        )
        handler.launch_step(
            StepHandlerContext(
                instance,
                ExecuteStepArgs(
                    reconstructable(bar).get_python_origin(), run.run_id, ["foo_solid"]
                ),
                {"foo_solid": {}},
            )
        )

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        assert kwargs["body"].spec.template.spec.containers[0].image == "bizbuz"


def test_step_handler_user_defined_config(kubeconfig_file):

    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sStepHandler(
        job_config=DagsterK8sJobConfig(instance_config_map="foobar", job_image="bizbuz"),
        job_namespace="foo",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    # Construct Dagster solid tags with user defined k8s config.
    expected_resources = {
        "requests": {"cpu": "250m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "2560Mi"},
    }
    user_defined_k8s_config = UserDefinedDagsterK8sConfig(
        container_config={"resources": expected_resources},
    )
    user_defined_k8s_config_json = json.dumps(user_defined_k8s_config.to_dict())
    tags = {"dagster-k8s/config": user_defined_k8s_config_json}

    with instance_for_test() as instance:
        run = create_run_for_test(
            instance,
            pipeline_name="bar",
        )
        handler.launch_step(
            StepHandlerContext(
                instance,
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
        assert job_resources == expected_resources

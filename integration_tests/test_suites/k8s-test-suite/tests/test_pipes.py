import json
from contextlib import contextmanager

import kubernetes
import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.pipes.client import (
    PipesContextInjector,
)
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session
from dagster_k8s import execute_k8s_job
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.pipes import PipesK8sClient, PipesK8sPodLogsMessageReader
from dagster_pipes import PipesContextData, PipesDefaultContextLoader
from dagster_test.test_project import (
    get_test_project_docker_image,
)


@pytest.mark.default
def test_pipes_client(namespace, cluster_provider):
    docker_image = get_test_project_docker_image()

    @asset
    def number_y(
        context: AssetExecutionContext,
        pipes_client: PipesK8sClient,
    ):
        return pipes_client.run(
            context=context,
            namespace=namespace,
            image=docker_image,
            command=[
                "python",
                "-m",
                "numbers_example.number_y",
            ],
            extras={
                "storage_root": "/tmp/",
            },
            env={
                "PYTHONPATH": "/dagster_test/toys/external_execution/",
                "NUMBER_Y": "2",
            },
        ).get_results()

    result = materialize(
        [number_y],
        resources={
            "pipes_client": PipesK8sClient(
                load_incluster_config=False,
                kubeconfig_file=cluster_provider.kubeconfig_file,
            )
        },
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_y.op.name)
    assert "is_even" in mats[0].metadata
    assert mats[0].metadata["is_even"].value is True


class PipesConfigMapContextInjector(PipesContextInjector):
    def __init__(
        self,
        k8s_client: DagsterKubernetesClient,
        namespace: str,
    ):
        self._client = k8s_client
        self._namespace = namespace
        self._cm_name = "dagster-pipes-cm"

    def no_messages_debug_text(self) -> str:
        return "Attempted to inject context via volume mounted config map."

    @contextmanager
    def inject_context(
        self,
        context_data: "PipesContextData",
    ):
        context_config_map_body = kubernetes.client.V1ConfigMap(
            metadata=kubernetes.client.V1ObjectMeta(
                name=self._cm_name,
            ),
            data={
                "context.json": json.dumps(context_data),
            },
        )
        self._client.core_api.create_namespaced_config_map(self._namespace, context_config_map_body)
        try:
            yield {PipesDefaultContextLoader.FILE_PATH_KEY: "/mnt/dagster/context.json"}
        finally:
            self._client.core_api.delete_namespaced_config_map(self._cm_name, self._namespace)

    def build_pod_spec(self, image, command):
        return {
            "containers": [
                {
                    "image": image,
                    "command": [
                        "python",
                        "-m",
                        "numbers_example.number_y",
                    ],
                    "volume_mounts": [
                        {
                            "mountPath": "/mnt/dagster/",
                            "name": "dagster-pipes-context",
                        }
                    ],
                }
            ],
            "volumes": [
                {
                    "name": "dagster-pipes-context",
                    "configMap": {
                        "name": self._cm_name,
                    },
                }
            ],
        }


@pytest.mark.default
def test_pipes_client_file_inject(namespace, cluster_provider):
    # a convoluted test to
    # - vet base_pod_spec works for setting volumes & mounts
    # - preserve file injection via config map code

    docker_image = get_test_project_docker_image()
    kubernetes.config.load_kube_config(cluster_provider.kubeconfig_file)
    client = DagsterKubernetesClient.production_client()
    injector = PipesConfigMapContextInjector(client, namespace)

    @asset
    def number_y(
        context: AssetExecutionContext,
        pipes_client: PipesK8sClient,
    ):
        pod_spec = injector.build_pod_spec(
            image=docker_image,
            command=[
                "python",
                "-m",
                "numbers_example.number_y",
            ],
        )

        return pipes_client.run(
            context=context,
            namespace=namespace,
            extras={
                "storage_root": "/tmp/",
            },
            env={
                "PYTHONPATH": "/dagster_test/toys/external_execution/",
                "NUMBER_Y": "2",
            },
            base_pod_spec=pod_spec,
        ).get_results()

    result = materialize(
        [number_y],
        resources={
            "pipes_client": PipesK8sClient(
                context_injector=injector,
                load_incluster_config=False,
                kubeconfig_file=cluster_provider.kubeconfig_file,
            )
        },
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_y.op.name)
    assert "is_even" in mats[0].metadata
    assert mats[0].metadata["is_even"].value is True


def test_use_execute_k8s_job(namespace, cluster_provider):
    docker_image = get_test_project_docker_image()

    @asset
    def number_y_job(context: AssetExecutionContext):
        core_api = kubernetes.client.CoreV1Api()
        reader = PipesK8sPodLogsMessageReader()
        with open_pipes_session(
            context,
            PipesEnvContextInjector(),
            reader,
            extras={"storage_root": "/tmp/"},
        ) as pipes_session:
            job_name = "number_y_asset_job"

            # stand-in for any means of creating kubernetes work
            execute_k8s_job(
                context=context,
                image=docker_image,
                command=[
                    "python",
                    "-m",
                    "numbers_example.number_y",
                ],
                env_vars=[
                    f"{k}={v}"
                    for k, v in {
                        "PYTHONPATH": "/dagster_test/toys/external_execution/",
                        "NUMBER_Y": "2",
                        **pipes_session.get_bootstrap_env_vars(),
                    }.items()
                ],
                k8s_job_name=job_name,
            )
            reader.consume_pod_logs(core_api, job_name, namespace)
        yield from pipes_session.get_results()

    result = materialize(
        [number_y_job],
        resources={
            "pipes_client": PipesK8sClient(
                load_incluster_config=False,
                kubeconfig_file=cluster_provider.kubeconfig_file,
            )
        },
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_y_job.op.name)
    assert "is_even" in mats[0].metadata
    assert mats[0].metadata["is_even"].value is True

import json
from contextlib import contextmanager

import kubernetes
import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.ext.client import (
    ExtContextInjector,
)
from dagster._core.ext.utils import ExtEnvContextInjector, ext_protocol
from dagster_ext import ExtContextData, ExtDefaultContextLoader
from dagster_k8s import execute_k8s_job
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.ext import ExtK8sPod, K8sPodLogsMessageReader
from dagster_test.test_project import (
    get_test_project_docker_image,
)


@pytest.mark.default
def test_ext_k8s_pod(namespace, cluster_provider):
    docker_image = get_test_project_docker_image()

    @asset
    def number_y(
        context: AssetExecutionContext,
        ext_k8s_pod: ExtK8sPod,
    ):
        return ext_k8s_pod.run(
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
        )

    result = materialize(
        [number_y],
        resources={"ext_k8s_pod": ExtK8sPod()},
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_y.op.name)
    assert "is_even" in mats[0].metadata
    assert mats[0].metadata["is_even"].value is True


class ExtConfigMapContextInjector(ExtContextInjector):
    def __init__(
        self,
        k8s_client: DagsterKubernetesClient,
        namespace: str,
    ):
        self._client = k8s_client
        self._namespace = namespace
        self._cm_name = "dagster-ext-cm"

    @contextmanager
    def inject_context(
        self,
        context_data: "ExtContextData",
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
            yield {ExtDefaultContextLoader.FILE_PATH_KEY: "/mnt/dagster/context.json"}
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
                            "name": "dagster-ext-context",
                        }
                    ],
                }
            ],
            "volumes": [
                {
                    "name": "dagster-ext-context",
                    "configMap": {
                        "name": self._cm_name,
                    },
                }
            ],
        }


@pytest.mark.default
def test_ext_k8s_pod_file_inject(namespace, cluster_provider):
    # a convoluted test to
    # - vet base_pod_spec works for setting volumes & mounts
    # - preserve file injection via config map code

    docker_image = get_test_project_docker_image()
    kubernetes.config.load_kube_config(cluster_provider.kubeconfig_file)
    client = DagsterKubernetesClient.production_client()
    injector = ExtConfigMapContextInjector(client, namespace)

    @asset
    def number_y(
        context: AssetExecutionContext,
        ext_k8s_pod: ExtK8sPod,
    ):
        pod_spec = injector.build_pod_spec(
            image=docker_image,
            command=[
                "python",
                "-m",
                "numbers_example.number_y",
            ],
        )

        return ext_k8s_pod.run(
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
        )

    result = materialize(
        [number_y],
        resources={"ext_k8s_pod": ExtK8sPod(context_injector=injector)},
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_y.op.name)
    assert "is_even" in mats[0].metadata
    assert mats[0].metadata["is_even"].value is True


def test_use_excute_k8s_job(namespace, cluster_provider):
    docker_image = get_test_project_docker_image()

    @asset
    def number_y_job(context: AssetExecutionContext):
        core_api = kubernetes.client.CoreV1Api()
        reader = K8sPodLogsMessageReader()
        with ext_protocol(
            context,
            ExtEnvContextInjector(),
            reader,
            extras={"storage_root": "/tmp/"},
        ) as ext_context:
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
                        **ext_context.get_external_process_env_vars(),
                    }.items()
                ],
                k8s_job_name=job_name,
            )
            reader.consume_pod_logs(core_api, job_name, namespace)
        return ext_context.get_materialize_results()

    result = materialize(
        [number_y_job],
        resources={"ext_k8s_pod": ExtK8sPod()},
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_y_job.op.name)
    assert "is_even" in mats[0].metadata
    assert mats[0].metadata["is_even"].value is True

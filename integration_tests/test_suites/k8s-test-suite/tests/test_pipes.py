import json
from contextlib import contextmanager

import kubernetes
import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.instance import DagsterInstance
from dagster._core.pipes.client import PipesContextInjector
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session
from dagster._core.test_utils import environ
from dagster_k8s import execute_k8s_job
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.pipes import PipesK8sClient, PipesK8sPodLogsMessageReader
from dagster_pipes import PipesContextData, PipesDefaultContextLoader
from dagster_test.test_project import get_test_project_docker_image

POLL_INTERVAL = 0.5


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
                poll_interval=POLL_INTERVAL,
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
                poll_interval=POLL_INTERVAL,
            )
        },
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_y.op.name)
    assert "is_even" in mats[0].metadata
    assert mats[0].metadata["is_even"].value is True


@pytest.mark.default
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
            job_name = "number-y-asset-job"

            # stand-in for any means of creating kubernetes work
            execute_k8s_job(
                context=context.op_execution_context,
                namespace=namespace,
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
                load_incluster_config=False,
                kubeconfig_file=cluster_provider.kubeconfig_file,
                image_pull_policy="IfNotPresent",
            )

            api_client = DagsterKubernetesClient.production_client()
            pod_names = api_client.get_pod_names_in_job(job_name=job_name, namespace=namespace)
            pod_name = pod_names[0]

            reader.consume_pod_logs(context, core_api, pod_name, namespace)
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


@pytest.mark.default
def test_pipes_error(namespace, cluster_provider):
    docker_image = get_test_project_docker_image()

    @asset
    def check_failure(
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
                "error_example.sleep_and_fail",
            ],
            extras={
                "sleep_seconds": 3 * POLL_INTERVAL,
            },
            env={
                "PYTHONPATH": "/dagster_test/toys/external_execution/",
            },
        ).get_results()

    instance = DagsterInstance.ephemeral()
    result = materialize(
        [check_failure],
        resources={
            "pipes_client": PipesK8sClient(
                load_incluster_config=False,
                kubeconfig_file=cluster_provider.kubeconfig_file,
                poll_interval=POLL_INTERVAL,
            )
        },
        instance=instance,
        raise_on_error=False,
    )
    assert not result.success
    conn = instance.get_records_for_run(result.run_id)
    pipes_msgs = [
        record.event_log_entry.user_message
        for record in conn.records
        if record.event_log_entry.user_message.startswith("[pipes]")
    ]
    assert len(pipes_msgs) == 2
    assert "successfully opened" in pipes_msgs[0]
    assert "external process pipes closed with exception" in pipes_msgs[1]


@pytest.mark.default
def test_pipes_client_ignore_init_container(namespace, cluster_provider):
    """Test that PipesK8sClient works with an init container listed in ignore_containers.

    This test is expected to fail due to a logic bug in wait_for_pod where ignored
    init containers can cause a StopIteration when the init container status is present
    but the regular container statuses have not yet been populated.
    """
    docker_image = get_test_project_docker_image()

    @asset
    def number_y(
        context: AssetExecutionContext,
        pipes_client: PipesK8sClient,
    ):
        return pipes_client.run(
            context=context,
            namespace=namespace,
            extras={
                "storage_root": "/tmp/",
            },
            base_pod_spec={
                "init_containers": [
                    {
                        "name": "init-setup",
                        "image": "busybox",
                        "command": ["sh", "-c", "echo 'init done'"],
                    }
                ],
                "containers": [
                    {
                        "name": "dagster-pipes",
                        "image": docker_image,
                        "command": [
                            "python",
                            "-m",
                            "numbers_example.number_y",
                        ],
                        "env": [
                            {
                                "name": "PYTHONPATH",
                                "value": "/dagster_test/toys/external_execution/",
                            },
                            {"name": "NUMBER_Y", "value": "2"},
                        ],
                    }
                ],
            },
            ignore_containers={"init-setup"},
        ).get_results()

    result = materialize(
        [number_y],
        resources={
            "pipes_client": PipesK8sClient(
                load_incluster_config=False,
                kubeconfig_file=cluster_provider.kubeconfig_file,
                poll_interval=POLL_INTERVAL,
            )
        },
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_y.op.name)
    assert "is_even" in mats[0].metadata
    assert mats[0].metadata["is_even"].value is True


@pytest.mark.default
def test_pipes_client_read_timeout(namespace, cluster_provider):
    # despite a strict request timeout causing frequent interruptions,
    # the pipes client can still complete.
    # also implicitly verifies that messages are deduped since otherwise
    # the same pipe control messages would be logged multiple times and the
    # run would fail.
    with environ({"DAGSTER_PIPES_K8S_CONSUME_POD_LOGS_REQUEST_TIMEOUT": "1"}):
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
                    poll_interval=POLL_INTERVAL,
                )
            },
            raise_on_error=False,
        )
        assert result.success
        mats = result.asset_materializations_for_node(number_y.op.name)
        assert "is_even" in mats[0].metadata
        assert mats[0].metadata["is_even"].value is True

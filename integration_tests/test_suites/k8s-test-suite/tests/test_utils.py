import time

import kubernetes
import pytest
from dagster_k8s.client import DagsterK8sError, DagsterKubernetesClient, WaitForPodState

pytest_plugins = ["dagster_k8s_test_infra.helm"]


def construct_pod_spec(name, cmd, image="busybox", container_kwargs=None):
    return kubernetes.client.V1PodSpec(
        restart_policy="Never",
        containers=[
            kubernetes.client.V1Container(
                name=name,
                image=image,
                args=["/bin/sh", "-c", cmd],
                **(container_kwargs or {}),
            )
        ],
    )


def construct_pod_manifest(name, cmd, image="busybox", container_kwargs=None):
    return kubernetes.client.V1Pod(
        metadata=kubernetes.client.V1ObjectMeta(name=name),
        spec=construct_pod_spec(name, cmd, image=image, container_kwargs=container_kwargs),
    )


def construct_job_manifest(name, cmd, image="busybox", container_kwargs=None):
    return kubernetes.client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=kubernetes.client.V1ObjectMeta(name=name),
        spec=kubernetes.client.V1JobSpec(
            template=kubernetes.client.V1PodTemplateSpec(
                spec=construct_pod_spec(name, cmd, image=image, container_kwargs=container_kwargs)
            ),
            backoff_limit=0,
        ),
    )


@pytest.mark.default
def test_wait_for_pod(cluster_provider, namespace):
    api_client = DagsterKubernetesClient.production_client()

    # Without this sleep, we get the following error on kind:
    # HTTP response body:
    # {"kind":"Status","apiVersion":"v1","metadata":{},"status":"Failure","message":"No API
    # token found for service account \"default\", retry after the token is automatically
    # created and added to the service
    # account","reason":"ServerTimeout","details":{"name":"create
    # pod","kind":"serviceaccounts","retryAfterSeconds":1},"code":500}
    time.sleep(5)

    try:
        api_client.core_api.create_namespaced_pod(
            body=construct_pod_manifest("waitforpod1", 'echo "hello world"'), namespace=namespace
        )
        api_client.wait_for_pod("waitforpod1", namespace=namespace)
        assert api_client.retrieve_pod_logs("waitforpod1", namespace=namespace) == "hello world\n"

        api_client.core_api.create_namespaced_pod(
            body=construct_pod_manifest("sayhi2", 'echo "hello world"'), namespace=namespace
        )
        api_client.wait_for_pod(
            "sayhi2", namespace=namespace, wait_for_state=WaitForPodState.Terminated
        )

        with pytest.raises(
            DagsterK8sError, match="Timed out while waiting for pod to get to status READY"
        ):
            api_client.core_api.create_namespaced_pod(
                body=construct_pod_manifest("sayhi3", 'sleep 5; echo "hello world"'),
                namespace=namespace,
            )
            api_client.wait_for_pod("sayhi3", namespace=namespace, wait_timeout=1)

        with pytest.raises(DagsterK8sError):
            api_client.core_api.create_namespaced_pod(
                body=construct_pod_manifest("failwaitforpod", 'echo "whoops!"; exit 1'),
                namespace=namespace,
            )
            api_client.wait_for_pod(
                "failwaitforpod", namespace=namespace, wait_for_state=WaitForPodState.Terminated
            )

    finally:
        for pod_name in ["waitforpod1", "sayhi2", "sayhi3", "failwaitforpod"]:
            try:
                api_client.core_api.delete_namespaced_pod(pod_name, namespace=namespace)
            except kubernetes.client.rest.ApiException:
                pass


@pytest.mark.default
def test_pod_debug_info_failure(cluster_provider, namespace, should_cleanup):
    time.sleep(5)
    api_client = DagsterKubernetesClient.production_client()

    try:
        # test case where the pod can't be scheduled due to an unworkable resource request
        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest(
                "resourcelimit",
                'echo "hello world"',
                container_kwargs={
                    "resources": kubernetes.client.V1ResourceRequirements(
                        requests={"memory": "4000000M"}, limits={"memory": "4000000M"}
                    ),
                },
            ),
            namespace=namespace,
        )
        api_client.wait_for_job("resourcelimit", namespace=namespace)
        api_client.wait_for_job_to_have_pods("resourcelimit", namespace=namespace)

        pod_names = api_client.get_pod_names_in_job("resourcelimit", namespace=namespace)

        pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)

        print(str(pod_debug_info))  # noqa

        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Pending

No logs for container 'resourcelimit'.

Warning events for pod:
FailedScheduling: 0/1 nodes are available: 1 Insufficient memory."""
        )

        # Test case where the pod is still running
        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest(
                "waitforever", 'echo "time for sleep"; sleep 3600; echo "hello world"'
            ),
            namespace=namespace,
        )
        api_client.wait_for_job("waitforever", namespace=namespace)

        start_time = time.time()
        while True:
            if time.time() - start_time > 60:
                raise Exception("No error state after 60 seconds")

            pod_names = api_client.get_pod_names_in_job("waitforever", namespace=namespace)
            if pod_names:
                pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)
                if "time for sleep" in pod_debug_info:
                    break

            time.sleep(5)

        print(str(pod_debug_info))  # noqa

        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Running
Container 'waitforever' status: Ready

Last 25 log lines for container 'waitforever':"""
        )

        assert "No warning events for pod." in pod_debug_info

        # Test case where logs have an exec format error (simulated)
        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest(
                "execformaterror", 'echo "exec /usr/local/bin/dagster: exec format error"; exit 1'
            ),
            namespace=namespace,
        )

        with pytest.raises(
            DagsterK8sError,
            match="Encountered failed job pods for job execformaterror with status:",
        ):
            api_client.wait_for_job_success("execformaterror", namespace=namespace)

        pod_names = api_client.get_pod_names_in_job("execformaterror", namespace=namespace)

        pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)

        print(str(pod_debug_info))  # noqa

        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Failed
Container 'execformaterror' status: Terminated with exit code 1: Error

Logs for container 'execformaterror' contained `exec format error`, which usually means that your Docker image was built using the wrong architecture.
Try rebuilding your docker image with the `--platform linux/amd64` flag set.

Last 25 log lines for container 'execformaterror':
"""
        )

        assert "exec /usr/local/bin/dagster: exec format error" in pod_debug_info
        assert "No warning events for pod." in pod_debug_info

        # Test case where a non-existant secret is used
        bad_secret_config = [
            kubernetes.client.V1EnvFromSource(
                secret_ref=kubernetes.client.V1SecretEnvSource(name="missing-secret")
            )
        ]

        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest(
                "missingsecret",
                'echo "hello world"',
                container_kwargs={"env_from": bad_secret_config},
            ),
            namespace=namespace,
        )

        api_client.wait_for_job("missingsecret", namespace=namespace)

        start_time = time.time()
        while True:
            if time.time() - start_time > 60:
                raise Exception("No error state after 60 seconds")

            pod_names = api_client.get_pod_names_in_job("missingsecret", namespace=namespace)

            if pod_names:
                pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)
                if "CreateContainerConfigError" in pod_debug_info:
                    break

            time.sleep(5)

        pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)

        print(str(pod_debug_info))  # noqa

        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Pending
Container 'missingsecret' status: Waiting: CreateContainerConfigError: secret "missing-secret" not found

No logs for container 'missingsecret'.

Warning events for pod:"""
        )

        # Test case where an unpullable image is used
        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest("pullfail", 'echo "should not reach"', image="fakeimage"),
            namespace=namespace,
        )

        api_client.wait_for_job("pullfail", namespace=namespace)

        start_time = time.time()
        while True:
            if time.time() - start_time > 60:
                raise Exception("No error state after 60 seconds")

            pod_names = api_client.get_pod_names_in_job("pullfail", namespace=namespace)

            if pod_names:
                pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)
                if "ImagePullBackOff" in pod_debug_info:
                    break

            time.sleep(5)

        print(str(pod_debug_info))  # noqa
        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Pending
Container 'pullfail' status: Waiting: ErrImagePull: rpc error: code = Unknown desc = failed to pull and unpack image "docker.io/library/fakeimage:latest": failed to resolve reference "docker.io/library/fakeimage:latest": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed

No logs for container 'pullfail'.

Warning events for pod:"""
        )
        assert "Failed: Error: ErrImagePull" in pod_debug_info
        assert "Failed: Error: ImagePullBackOff" in pod_debug_info

        # Test case where the pod unexpectedly terminates
        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest("failpoddebug", 'echo "whoops!"; exit 1'),
            namespace=namespace,
        )

        with pytest.raises(
            DagsterK8sError,
            match="Encountered failed job pods for job failpoddebug with status:",
        ):
            api_client.wait_for_job_success("failpoddebug", namespace=namespace)

        pod_names = api_client.get_pod_names_in_job("failpoddebug", namespace=namespace)

        pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)

        print(pod_debug_info)  # noqa

        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Failed
Container 'failpoddebug' status: Terminated with exit code 1: Error

Last 25 log lines for container 'failpoddebug':"""
        )
        assert " whoops!\n" in pod_debug_info
        assert pod_debug_info.endswith("No warning events for pod.")

        # Test case where the pod unexpectedly terminates and logs collection is skipped
        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest("failpoddebugnologs", 'echo "whoopsies!"; exit 1'),
            namespace=namespace,
        )

        with pytest.raises(
            DagsterK8sError,
            match="Encountered failed job pods for job failpoddebugnologs with status:",
        ):
            api_client.wait_for_job_success("failpoddebugnologs", namespace=namespace)

        pod_names = api_client.get_pod_names_in_job("failpoddebugnologs", namespace=namespace)

        pod_debug_info = api_client.get_pod_debug_info(
            pod_names[0], namespace=namespace, include_container_logs=False
        )

        print(pod_debug_info)  # noqa

        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Failed
Container 'failpoddebugnologs' status: Terminated with exit code 1: Error
            """.strip()
        )
        assert " whoopsies!\n" not in pod_debug_info
        assert pod_debug_info.endswith("No warning events for pod.")

        # Test case where the pod completes successfully
        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest("goodpod1", 'echo "hello world"'), namespace=namespace
        )
        api_client.wait_for_job_success("goodpod1", namespace=namespace)

        pod_names = api_client.get_pod_names_in_job("goodpod1", namespace=namespace)

        pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)
        print(pod_debug_info)  # noqa

        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Succeeded
Container 'goodpod1' status: Terminated with exit code 0: Completed

Last 25 log lines for container 'goodpod1':"""
        )
        assert "hello world" in pod_debug_info
        assert "No warning events for pod." in pod_debug_info

        # Test sidecars
        api_client.batch_api.create_namespaced_job(
            body=kubernetes.client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=kubernetes.client.V1ObjectMeta(name="goodpod2"),
                spec=kubernetes.client.V1JobSpec(
                    template=kubernetes.client.V1PodTemplateSpec(
                        spec=kubernetes.client.V1PodSpec(
                            restart_policy="Never",
                            containers=[
                                kubernetes.client.V1Container(
                                    name="goodcontainer1",
                                    image="busybox",
                                    args=["/bin/sh", "-c", 'echo "hello world"'],
                                ),
                                kubernetes.client.V1Container(
                                    name="goodcontainer2",
                                    image="busybox",
                                    args=["/bin/sh", "-c", 'echo "hello again world"'],
                                ),
                            ],
                        )
                    ),
                    backoff_limit=0,
                ),
            ),
            namespace=namespace,
        )
        api_client.wait_for_job_success("goodpod2", namespace=namespace)

        pod_names = api_client.get_pod_names_in_job("goodpod2", namespace=namespace)

        pod_debug_info = api_client.get_pod_debug_info(pod_names[0], namespace=namespace)
        print(pod_debug_info)  # noqa

        assert pod_debug_info.startswith(
            f"""Debug information for pod {pod_names[0]}:

Pod status: Succeeded
Container 'goodcontainer1' status: Terminated with exit code 0: Completed
Container 'goodcontainer2' status: Terminated with exit code 0: Completed"""
        )

        assert "Last 25 log lines for container 'goodcontainer1':" in pod_debug_info
        assert "Last 25 log lines for container 'goodcontainer2':" in pod_debug_info

        assert "hello world" in pod_debug_info
        assert "hello again world" in pod_debug_info

    finally:
        if should_cleanup:
            for job in [
                "failpoddebug",
                "pullfail",
                "missingsecret",
                "goodpod1",
                "goodpod2" "waitforever",
                "execformaterror",
                "resourcelimit",
            ]:
                try:
                    api_client.batch_api.delete_namespaced_job(
                        job, namespace=namespace, propagation_policy="Foreground"
                    )
                except kubernetes.client.rest.ApiException:
                    pass


@pytest.mark.default
def test_wait_for_job(cluster_provider, namespace, should_cleanup):
    # Without this sleep, we get the following error on kind:
    # HTTP response body:
    # {"kind":"Status","apiVersion":"v1","metadata":{},"status":"Failure","message":"No API
    # token found for service account \"default\", retry after the token is automatically
    # created and added to the service
    # account","reason":"ServerTimeout","details":{"name":"create
    # pod","kind":"serviceaccounts","retryAfterSeconds":1},"code":500}
    time.sleep(5)

    try:
        api_client = DagsterKubernetesClient.production_client()

        api_client.batch_api.create_namespaced_job(
            body=construct_job_manifest("waitforjob", 'echo "hello world"'), namespace=namespace
        )
        api_client.wait_for_job_success("waitforjob", namespace=namespace)

        with pytest.raises(
            DagsterK8sError, match="Timed out while waiting for job sayhi2 to complete"
        ):
            api_client.batch_api.create_namespaced_job(
                body=construct_job_manifest("sayhi2", 'sleep 5; echo "hello world"'),
                namespace=namespace,
            )
            api_client.wait_for_job_success("sayhi2", namespace=namespace, wait_timeout=1)

        with pytest.raises(
            DagsterK8sError,
            match="Encountered failed job pods for job failwaitforjob with status:",
        ):
            api_client.batch_api.create_namespaced_job(
                body=construct_job_manifest("failwaitforjob", 'echo "whoops!"; exit 1'),
                namespace=namespace,
            )
            api_client.wait_for_job_success("failwaitforjob", namespace=namespace)

    finally:
        if should_cleanup:
            for job in ["waitforjob", "sayhi2", "failwaitforjob"]:
                try:
                    api_client.batch_api.delete_namespaced_job(
                        job, namespace=namespace, propagation_policy="Foreground"
                    )
                except kubernetes.client.rest.ApiException:
                    pass

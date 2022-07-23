import pytest
from dagster_k8s import k8s_job_op
from dagster_k8s.client import DagsterK8sError

from dagster import job


@pytest.mark.default
def test_k8s_job_op(namespace, cluster_provider):
    first_op = k8s_job_op.configured(
        {
            "image": "busybox",
            "command": ["/bin/sh", "-c"],
            "args": ["echo HI"],
            "namespace": namespace,
            "load_incluster_config": False,
            "kubeconfig_file": cluster_provider.kubeconfig_file,
        },
        name="first_op",
    )
    second_op = k8s_job_op.configured(
        {
            "image": "busybox",
            "command": ["/bin/sh", "-c"],
            "args": ["echo GOODBYE"],
            "namespace": namespace,
            "load_incluster_config": False,
            "kubeconfig_file": cluster_provider.kubeconfig_file,
        },
        name="second_op",
    )

    @job
    def my_full_job():
        second_op(first_op())

    my_full_job.execute_in_process()


@pytest.mark.default
def test_k8s_job_op_with_timeout(namespace, cluster_provider):
    timeout_op = k8s_job_op.configured(
        {
            "image": "busybox",
            "command": ["/bin/sh", "-c"],
            "args": ["sleep 15 && echo HI"],
            "namespace": namespace,
            "load_incluster_config": False,
            "kubeconfig_file": cluster_provider.kubeconfig_file,
            "timeout": 5,
        },
        name="timeout_op",
    )

    @job
    def timeout_job():
        timeout_op()

    with pytest.raises(DagsterK8sError, match="Timed out while waiting for pod to become ready"):
        timeout_job.execute_in_process()


@pytest.mark.default
def test_k8s_job_op_with_failure(namespace, cluster_provider):
    failure_op = k8s_job_op.configured(
        {
            "image": "busybox",
            "command": ["/bin/sh", "-c"],
            "args": ["sleep 10 && exit 1"],
            "namespace": namespace,
            "load_incluster_config": False,
            "kubeconfig_file": cluster_provider.kubeconfig_file,
            "timeout": 5,
        },
        name="failure_op",
    )

    @job
    def failure_job():
        failure_op()

    with pytest.raises(DagsterK8sError, match="Timed out while waiting for pod to become ready"):
        failure_job.execute_in_process()

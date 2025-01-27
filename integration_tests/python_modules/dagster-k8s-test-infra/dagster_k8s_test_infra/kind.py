# ruff: noqa: T201

import os
import subprocess
import time
import uuid
from contextlib import contextmanager

import dagster._check as check
import kubernetes
from dagster._utils import safe_tempfile_path

from dagster_k8s_test_infra.cluster import ClusterConfig
from dagster_k8s_test_infra.integration_utils import check_output, which_, within_docker

CLUSTER_INFO_DUMP_DIR = "kind-info-dump"


def kind_load_images(cluster_name, local_dagster_test_image, additional_images=None):
    check.str_param(cluster_name, "cluster_name")
    check.str_param(local_dagster_test_image, "local_dagster_test_image")
    additional_images = check.opt_list_param(additional_images, "additional_images", of_type=str)

    print("Loading images into kind cluster...")

    # Pull rabbitmq/pg images
    for image in additional_images:
        print(f"kind: Loading image {image} into kind cluster {cluster_name}")
        check_output(["docker", "pull", image])
        check_output(["kind", "load", "docker-image", "--name", cluster_name, image])

    print(f"kind: Loading image {local_dagster_test_image} into kind cluster {cluster_name}")
    check_output(["kind", "load", "docker-image", "--name", cluster_name, local_dagster_test_image])


def kind_cluster_exists(cluster_name):
    running_clusters = check_output(["kind", "get", "clusters"]).decode("utf-8").split("\n")
    cluster_exists = cluster_name in running_clusters
    return cluster_exists


@contextmanager
def create_kind_cluster(cluster_name, should_cleanup=True):
    check.str_param(cluster_name, "cluster_name")
    check.bool_param(should_cleanup, "should_cleanup")

    try:
        print(f"--- \033[32m:k8s: Running kind cluster setup for cluster {cluster_name}\033[0m")

        p = subprocess.Popen(
            ["kind", "create", "cluster", "--name", cluster_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()

        print("Kind create cluster command completed with stdout: ", stdout)
        print("Kind create cluster command completed with stderr: ", stderr)

        assert p.returncode == 0
        yield cluster_name

    finally:
        # ensure cleanup happens on error or normal exit
        if should_cleanup:
            print(f"--- Cleaning up kind cluster {cluster_name}")
            check_output(["kind", "delete", "cluster", "--name", cluster_name])


@contextmanager
def kind_kubeconfig(cluster_name, use_internal_address=True):
    """For kind clusters, we need to write our own kubeconfig file to leave the user's existing
    kubeconfig alone.
    """
    check.str_param(cluster_name, "cluster_name")
    check.bool_param(use_internal_address, "use_internal_address")

    old_kubeconfig = os.getenv("KUBECONFIG")
    try:
        kubeconfig_call = ["kind", "get", "kubeconfig", "--name", cluster_name]
        if use_internal_address:
            kubeconfig_call += ["--internal"]

        with safe_tempfile_path() as kubeconfig_file:
            print(f"Writing kubeconfig to file {kubeconfig_file}")

            with open(kubeconfig_file, "wb") as f:
                subprocess.check_call(kubeconfig_call, stdout=f)

            os.environ["KUBECONFIG"] = kubeconfig_file

            yield kubeconfig_file

    finally:
        print("Cleaning up kubeconfig")
        if "KUBECONFIG" in os.environ:
            del os.environ["KUBECONFIG"]

        if old_kubeconfig is not None:
            os.environ["KUBECONFIG"] = old_kubeconfig


def kind_sync_dockerconfig():
    """Copies docker config to kind cluster node(s) for private registry auth.

    See: https://kind.sigs.k8s.io/docs/user/private-registries/#use-an-access-token
    """
    print("--- Syncing docker config to nodes...")

    docker_exe = which_("docker")

    nodes = kubernetes.client.CoreV1Api().list_node().items
    for node in nodes:
        node_name = node.metadata.name

        # copy the config to where kubelet will look
        cmd = os.path.expandvars(
            f"{docker_exe} cp $HOME/.docker/config.json {node_name}:/var/lib/kubelet/config.json"
        )
        print(f"Running cmd: {cmd}")
        check_output(cmd, shell=True)

        # restart kubelet to pick up the config
        print("Restarting node kubelets...")
        check_output(f"docker exec {node_name} systemctl restart kubelet.service", shell=True)


@contextmanager
def kind_cluster(cluster_name=None, should_cleanup=False, kind_ready_timeout=60.0):
    cluster_name = cluster_name or f"cluster-{uuid.uuid4().hex}"

    # We need to use an internal address in a DinD context like Buildkite
    use_internal_address = within_docker()

    if kind_cluster_exists(cluster_name):
        print(f"Using existing cluster {cluster_name}")

        with kind_kubeconfig(cluster_name, use_internal_address) as kubeconfig_file:
            kubernetes.config.load_kube_config(config_file=kubeconfig_file)
            yield ClusterConfig(cluster_name, kubeconfig_file)

            if should_cleanup:
                print(
                    "WARNING: should_cleanup is true, but won't delete your existing cluster. If"
                    " you'd like to delete this cluster, please manually remove by running the"
                    f" command:\nkind delete cluster --name {cluster_name}"
                )
    else:
        with create_kind_cluster(cluster_name, should_cleanup=should_cleanup):
            with kind_kubeconfig(cluster_name, use_internal_address) as kubeconfig_file:
                kubernetes.config.load_kube_config(config_file=kubeconfig_file)
                kind_sync_dockerconfig()

                try:
                    # Ensure cluster is up by listing svc accounts in the default namespace
                    # Otherwise if not ready yet, pod creation on kind cluster will fail with error
                    # like:
                    #
                    # pods "dagster.demo-error-pipeline.error-solid-e748d5c2" is forbidden: error
                    # looking up service account default/default: serviceaccount "default" not found
                    print("Testing service account listing...")
                    start = time.time()
                    while True:
                        if time.time() - start > kind_ready_timeout:
                            raise Exception("Timed out while waiting for kind cluster to be ready")

                        api = kubernetes.client.CoreV1Api()
                        service_accounts = [
                            s.metadata.name
                            for s in api.list_namespaced_service_account("default").items
                        ]
                        print("Service accounts: ", service_accounts)
                        if "default" in service_accounts:
                            break

                        time.sleep(1)

                    yield ClusterConfig(cluster_name, kubeconfig_file)

                finally:
                    IS_BUILDKITE = os.getenv("BUILDKITE") is not None
                    if IS_BUILDKITE:
                        cluster_info_dump()


def cluster_info_dump():
    print(f"Writing out cluster info to {CLUSTER_INFO_DUMP_DIR}")

    p = subprocess.Popen(
        [
            "kubectl",
            "cluster-info",
            "dump",
            "--all-namespaces=true",
            f"--output-directory={CLUSTER_INFO_DUMP_DIR}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = p.communicate()
    print("Cluster info dumped with stdout: ", stdout)
    print("Cluster info dumped with stderr: ", stderr)
    assert p.returncode == 0

    p = subprocess.Popen(
        [
            "buildkite-agent",
            "artifact",
            "upload",
            f"{CLUSTER_INFO_DUMP_DIR}/**/*",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = p.communicate()
    print("Buildkite artifact added with stdout: ", stdout)
    print("Buildkite artifact added with stderr: ", stderr)
    assert p.returncode == 0

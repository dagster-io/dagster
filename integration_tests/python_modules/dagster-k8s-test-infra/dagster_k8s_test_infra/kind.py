# ruff: noqa: T201

import os
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import dagster._check as check
import kubernetes
from dagster._utils import safe_tempfile_path

from dagster_k8s_test_infra.cluster import ClusterConfig
from dagster_k8s_test_infra.integration_utils import (
    IS_BUILDKITE,
    check_output,
    which_,
    within_docker,
)

CLUSTER_INFO_DUMP_DIR = "kind-info-dump"

# kind-registry is a docker.io pull-through cache that runs as a sibling
# container to the kind cluster (in the dind sidecar's docker daemon).
# kind's containerd is configured via containerdConfigPatches to use it as
# the docker.io mirror, so kubelet inside kind never talks to docker.io
# directly. Eliminates rate-limit pressure on shared NAT egress IPs without
# requiring kind_load_images to preload every supporting image.
KIND_REGISTRY_NAME = "kind-registry"
KIND_REGISTRY_PORT = 5000
KIND_NETWORK_NAME = "kind"

# On Buildkite, chain through the EKS-level dockerhub-mirror so the cache
# is shared across all agent pods on the cluster (one cluster-wide
# `registry:2` Deployment in the buildkite-agent namespace, see
# infra/k8s/buildkite/overlays/buildkite-eks/dockerhub-mirror.yaml).
# Locally, fall back to pulling direct from docker.io.
_BUILDKITE_DOCKERHUB_MIRROR = "http://dockerhub-mirror.buildkite-agent.svc.cluster.local:5000"
_DOCKERHUB_UPSTREAM = "https://registry-1.docker.io"


def _docker_pull_with_retry(image, attempts=3, backoff_seconds=5):
    # Docker Hub intermittently returns 5xx from its blob CDN; a couple of retries with
    # backoff is enough to mask transient failures without masking real auth/404 errors
    # (those will still fail every attempt).
    for attempt in range(1, attempts + 1):
        try:
            check_output(["docker", "pull", image])
            return
        except subprocess.CalledProcessError:
            if attempt == attempts:
                raise
            print(f"docker pull {image} failed (attempt {attempt}/{attempts}); retrying...")
            time.sleep(backoff_seconds)


def _registry_proxy_remote_url() -> str:
    return _BUILDKITE_DOCKERHUB_MIRROR if IS_BUILDKITE else _DOCKERHUB_UPSTREAM


def _ensure_kind_registry() -> None:
    """Start (or reuse) the docker.io pull-through registry-proxy container.

    Idempotent: safe to call repeatedly. The container persists for the lifetime
    of the dind sidecar so subsequent kind clusters in the same pod reuse its
    cache.
    """
    # subprocess.run directly so we can inspect returncode without the
    # integration_utils.check_output wrapper re-raising CalledProcessError
    # as a generic Exception.
    inspect = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", KIND_REGISTRY_NAME],
        capture_output=True,
        check=False,
    )
    if inspect.returncode == 0:
        if inspect.stdout.decode("utf-8").strip() == "true":
            print(f"kind: registry {KIND_REGISTRY_NAME} already running")
            return
        # Container exists but is stopped -- start it.
        subprocess.run(["docker", "start", KIND_REGISTRY_NAME], check=True)
        print(f"kind: restarted existing registry container {KIND_REGISTRY_NAME}")
        return

    remote_url = _registry_proxy_remote_url()
    print(f"kind: creating registry container {KIND_REGISTRY_NAME} -> {remote_url}")
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            KIND_REGISTRY_NAME,
            "--restart=always",
            "-e",
            f"REGISTRY_PROXY_REMOTEURL={remote_url}",
            "-p",
            f"{KIND_REGISTRY_PORT}:{KIND_REGISTRY_PORT}",
            "registry:2",
        ],
        check=True,
    )


def _attach_registry_to_kind_network() -> None:
    """Connect kind-registry to the kind docker network.

    Required so kind nodes can resolve `kind-registry:5000` via docker's
    embedded DNS. Idempotent: if the registry is already attached, docker
    network connect returns nonzero with `already exists` in stderr -- treat
    that as success.
    """
    result = subprocess.run(
        ["docker", "network", "connect", KIND_NETWORK_NAME, KIND_REGISTRY_NAME],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        print(f"kind: connected {KIND_REGISTRY_NAME} to {KIND_NETWORK_NAME} network")
        return
    stderr = result.stderr.decode("utf-8", errors="replace")
    if "already exists" in stderr:
        return
    print(f"kind: warning: failed to attach registry to {KIND_NETWORK_NAME} network: {stderr}")


def kind_load_images(cluster_name, local_dagster_test_image, additional_images=None):
    check.str_param(cluster_name, "cluster_name")
    check.str_param(local_dagster_test_image, "local_dagster_test_image")
    additional_images = check.opt_list_param(additional_images, "additional_images", of_type=str)

    print(f"Loading images into kind cluster {cluster_name}...")

    def _load(image: str, pull_first: bool) -> None:
        if pull_first:
            _docker_pull_with_retry(image)
        print(f"kind: Loading image {image} into kind cluster {cluster_name}")
        check_output(["kind", "load", "docker-image", "--name", cluster_name, image])

    # Parallelize pull + kind-load. `kind load docker-image` is bounded by
    # `docker save` -> tar streaming -> kind node's containerd import. The
    # per-image steps overlap well enough that 4 concurrent loads cut total
    # wall time from sum() to ~max() on the EBS-backed dind storage.
    work = [(image, True) for image in additional_images]
    work.append((local_dagster_test_image, False))

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda args: _load(*args), work))


def kind_cluster_exists(cluster_name):
    running_clusters = check_output(["kind", "get", "clusters"]).decode("utf-8").split("\n")
    cluster_exists = cluster_name in running_clusters
    return cluster_exists


_KIND_CONFIG_TEMPLATE = """\
apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster
# Configure kind's containerd to use a sibling registry-proxy container as
# the docker.io mirror. Eliminates kubelet pulls from hitting docker.io
# directly (and the rate limits that come with shared NAT egress IPs).
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
    endpoint = ["http://{registry_name}:{registry_port}"]
"""


@contextmanager
def create_kind_cluster(cluster_name, should_cleanup=True):
    check.str_param(cluster_name, "cluster_name")
    check.bool_param(should_cleanup, "should_cleanup")

    # Start the docker.io pull-through registry-proxy. Must exist before
    # `kind create cluster` so that kind's containerd, which is configured to
    # mirror docker.io through it, has a working endpoint by the time kubelet
    # starts pulling pod images. The container itself runs in the dind
    # sidecar's docker daemon (sibling to the kind node containers).
    _ensure_kind_registry()

    config_yaml = _KIND_CONFIG_TEMPLATE.format(
        registry_name=KIND_REGISTRY_NAME, registry_port=KIND_REGISTRY_PORT
    )

    try:
        print(f"--- \033[32m:k8s: Running kind cluster setup for cluster {cluster_name}\033[0m")

        with safe_tempfile_path() as config_path:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_yaml)
            p = subprocess.Popen(
                [
                    "kind",
                    "create",
                    "cluster",
                    "--name",
                    cluster_name,
                    "--config",
                    config_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = p.communicate()

        print("Kind create cluster command completed with stdout: ", stdout)
        print("Kind create cluster command completed with stderr: ", stderr)

        assert p.returncode == 0

        # Attach registry to the kind docker network so kind nodes can resolve
        # `kind-registry:5000` via docker's embedded DNS. Has to happen *after*
        # cluster creation -- the kind network only exists once the control-
        # plane container is up.
        _attach_registry_to_kind_network()

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

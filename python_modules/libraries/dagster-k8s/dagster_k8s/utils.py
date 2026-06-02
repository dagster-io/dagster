import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import kubernetes
from dagster import (
    __version__ as dagster_version,
    _check as check,
)

if TYPE_CHECKING:
    from dagster_k8s.job import UserDefinedDagsterK8sConfig


def load_kubernetes_config(
    *,
    load_incluster_config: bool,
    kubeconfig_file: str | None = None,
    k8s_api_ssl_ca_cert_file: str | None = None,
) -> None:
    """Load kubernetes client configuration and apply dagster-k8s workarounds.

    If ``load_incluster_config`` is True, load from the in-cluster service account
    token; otherwise load from ``kubeconfig_file``. When ``k8s_api_ssl_ca_cert_file``
    is provided, it is applied to the default Configuration after load.
    """
    if load_incluster_config:
        check.invariant(
            kubeconfig_file is None,
            "`kubeconfig_file` is set but `load_incluster_config` is True.",
        )
        kubernetes.config.load_incluster_config()
    else:
        kubernetes.config.load_kube_config(config_file=kubeconfig_file)

    no_proxy = _get_no_proxy_env()
    if not (no_proxy or k8s_api_ssl_ca_cert_file):
        return
    config = kubernetes.client.Configuration.get_default_copy()
    changed = False
    if no_proxy and hasattr(config, "no_proxy") and config.no_proxy is None:
        config.no_proxy = no_proxy
        changed = True
    if k8s_api_ssl_ca_cert_file:
        config.ssl_ca_cert = k8s_api_ssl_ca_cert_file
        changed = True
    if changed:
        kubernetes.client.Configuration.set_default(config)


def apply_no_proxy_env_workaround() -> None:
    # Works around https://github.com/kubernetes-client/python/issues/2520:
    # kubernetes.client.Configuration.__init__ reads NO_PROXY/no_proxy from the env
    # and then immediately overwrites self.no_proxy with None, so proxy-bypass rules
    # from the environment are silently dropped and all traffic is routed through
    # the configured proxy. We re-apply the env var onto the default Configuration
    # after kubeconfig load — but only when the default is still None, so this
    # becomes a true no-op on client versions where the bug is fixed. Client versions
    # that predate the `no_proxy` attribute never honored the env var at all, so
    # there is nothing to work around on those either.
    no_proxy = _get_no_proxy_env()
    if not no_proxy:
        return
    config = kubernetes.client.Configuration.get_default_copy()
    if not hasattr(config, "no_proxy") or config.no_proxy is not None:
        return
    config.no_proxy = no_proxy
    kubernetes.client.Configuration.set_default(config)


def _get_no_proxy_env() -> str | None:
    return os.environ.get("NO_PROXY") or os.environ.get("no_proxy")


def sanitize_k8s_label(label_name: str):
    # Truncate too long label values to fit into 63-characters limit and avoid invalid characters.
    # https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set
    label_name = label_name[:63]
    return re.sub(r"[^a-zA-Z0-9\-_\.]", "-", label_name).strip("-").strip("_").strip(".")


def get_common_labels():
    # See: https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/
    return {
        "app.kubernetes.io/name": "dagster",
        "app.kubernetes.io/instance": "dagster",
        "app.kubernetes.io/version": sanitize_k8s_label(dagster_version),
        "app.kubernetes.io/part-of": "dagster",
    }


def get_deployment_id_label(user_defined_k8s_config: "UserDefinedDagsterK8sConfig"):
    env = user_defined_k8s_config.container_config.get("env")
    deployment_name_env_var = (
        next((entry for entry in env if entry["name"] == "DAGSTER_CLOUD_DEPLOYMENT_NAME"), None)
        if env
        else None
    )
    return deployment_name_env_var["value"] if deployment_name_env_var else None


_NAMESPACE_SECRET_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")


def detect_current_namespace(
    kubeconfig_file: str | None, namespace_secret_path: Path = _NAMESPACE_SECRET_PATH
) -> str | None:
    """Get the current in-cluster namespace when operating within the cluster.

    First attempt to read it from the `serviceaccount` secret or get it from the kubeconfig_file if it is possible.
    It will attempt to take from the active context if it exists and returns None if it does not exist.
    """
    if namespace_secret_path.exists():
        with namespace_secret_path.open() as f:
            # We only need to read the first line, this guards us against bad input.
            return f.read().strip()

    if not kubeconfig_file:
        return None

    try:
        _, active_context = kubernetes.config.list_kube_config_contexts(kubeconfig_file)
        return active_context["context"]["namespace"]
    except KeyError:
        return None

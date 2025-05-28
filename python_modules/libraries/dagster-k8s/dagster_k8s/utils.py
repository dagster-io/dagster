import re
from typing import TYPE_CHECKING

from dagster import __version__ as dagster_version

if TYPE_CHECKING:
    from dagster_k8s.job import UserDefinedDagsterK8sConfig


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

import re

from dagster import __version__ as dagster_version


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

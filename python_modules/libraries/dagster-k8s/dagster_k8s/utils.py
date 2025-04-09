import functools
import os
import re

import kubernetes
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


class TimeoutConfigurableK8sAPIClient(kubernetes.client.CoreV1Api):
    def __init__(self, base_client):
        # explicitly do not call the super constructor, since we're just wrapping the base client
        pass

    def __new__(cls, base_client: kubernetes.client.CoreV1Api):
        instance = super().__new__(cls)

        try:
            timeout_str = os.getenv("KUBERNETES_API_REQUEST_TIMEOUT")
            timeout = int(timeout_str) if timeout_str else None
        except ValueError:
            timeout = None

        for attr_name in dir(base_client):
            if not attr_name.startswith("_"):
                attr = getattr(base_client, attr_name)
                if callable(attr) and timeout is not None:

                    @functools.wraps(attr)
                    def wrapped_method(method_name=attr_name):
                        original_method = getattr(base_client, method_name)

                        def method_with_timeout(*args, **kwargs):
                            if "_request_timeout" not in kwargs:
                                kwargs["_request_timeout"] = timeout
                            return original_method(*args, **kwargs)

                        return method_with_timeout

                    setattr(instance, attr_name, wrapped_method())
                else:
                    setattr(instance, attr_name, attr)

        return instance

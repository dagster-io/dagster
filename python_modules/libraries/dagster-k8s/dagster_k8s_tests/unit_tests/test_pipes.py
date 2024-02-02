from pathlib import Path

import pytest
from dagster._core.errors import DagsterInvariantViolationError
from dagster_k8s.pipes import _detect_current_namespace, build_pod_body


def test_pod_building():
    test_image = "my_test_image"
    # min info
    pod = build_pod_body(
        pod_name="test",
        image=test_image,
        command=None,  # image provides default entrypoint
        env_vars={},
        base_pod_spec=None,
        base_pod_meta=None,
    )
    assert pod.spec.containers[0].image == test_image
    assert pod.spec.restart_policy == "Never"

    # expected common case
    pod = build_pod_body(
        pod_name="test",
        image=test_image,
        command=["echo", "hello"],
        env_vars={},
        base_pod_spec=None,
        base_pod_meta=None,
    )
    assert pod.spec.containers[0].image == test_image

    # spec provided
    pod = build_pod_body(
        pod_name="test",
        image=None,
        command=None,
        env_vars={},
        base_pod_spec={
            "containers": [
                {
                    "image": test_image,
                }
            ]
        },
        base_pod_meta=None,
    )
    assert pod.spec.containers[0].image == test_image

    # no image
    with pytest.raises(DagsterInvariantViolationError):
        build_pod_body(
            pod_name="test",
            image=None,
            command=None,
            env_vars={},
            base_pod_spec=None,
            base_pod_meta=None,
        )

    # invalid other containers
    with pytest.raises(ValueError):
        build_pod_body(
            pod_name="test",
            image=test_image,
            command=None,
            env_vars={},
            base_pod_spec={
                "containers": [
                    {},
                    {},
                    {},
                ],
            },
            base_pod_meta=None,
        )

    # metadata provided
    pod = build_pod_body(
        pod_name="test",
        image=test_image,
        command=None,
        env_vars={},
        base_pod_spec=None,
        base_pod_meta={
            "labels": {
                "foo": "bar",
            },
            "annotations": {
                "fizz": "buzz",
            },
        },
    )
    assert pod.metadata.labels["foo"] == "bar"
    assert pod.metadata.annotations["fizz"] == "buzz"

    # env overrides
    pod = build_pod_body(
        pod_name="test",
        image=test_image,
        command=None,
        env_vars={
            "from_arg": "arg",
            "collide": "arg",
        },
        base_pod_spec={
            "containers": [
                {
                    "image": test_image,
                    "env": [
                        {"name": "from_spec", "value": "spec"},
                        {"name": "collide", "value": "spec"},
                    ],
                }
            ]
        },
        base_pod_meta=None,
    )
    assert len(pod.spec.containers[0].env) == 4
    resolved_env_vars = {pair.name: pair.value for pair in pod.spec.containers[0].env}
    assert len(resolved_env_vars) == 3
    assert resolved_env_vars["collide"] == "arg"

    # snake case camel case mix
    pod = build_pod_body(
        pod_name="test",
        image=None,
        command=None,
        env_vars={},
        base_pod_meta=None,
        base_pod_spec={
            "containers": [
                {
                    "image": test_image,
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
                        "name": "cm",
                    },
                }
            ],
        },
    )
    assert pod  # cases coerced correctly and passed internal validation

    # common labels dont override
    pod = build_pod_body(
        pod_name="test",
        image=test_image,
        command=["echo", "hello"],
        env_vars={},
        base_pod_spec=None,
        base_pod_meta={"labels": {"app.kubernetes.io/name": "custom"}},
    )
    assert pod.metadata.labels["app.kubernetes.io/name"] == "custom"
    assert pod.metadata.labels["app.kubernetes.io/instance"] == "dagster"

    # restart policy
    pod = build_pod_body(
        pod_name="test",
        image=test_image,
        command=["echo", "hello"],
        env_vars={},
        base_pod_spec={"restartPolicy": "OnFailure"},
        base_pod_meta=None,
    )
    assert pod.spec.restart_policy == "OnFailure"

    with pytest.raises(DagsterInvariantViolationError):
        build_pod_body(
            pod_name="test",
            image=test_image,
            command=["echo", "hello"],
            env_vars={},
            base_pod_spec={"restart_policy": "Always"},
            base_pod_meta=None,
        )


def _kubeconfig(tmpdir: str, current_context: str) -> str:
    kubeconfig = Path(tmpdir) / "kubeconfig"
    kubeconfig.write_text(
        f"""\
---
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: deadbeef==
    server: https://127.0.0.1:8888
  name: ctx
contexts:
- context:
    cluster: ctx
    user: ctx
  name: ctx
- context:
    cluster: ctx
    user: ctx
    namespace: my-namespace
  name: ctx-with-namespace
current-context: {current_context}
kind: Config
preferences: {{}}
users:
- name: ctx
  user:
    client-certificate-data: deadbeef==
    client-key-data: deadbeef==
"""
    )
    return str(kubeconfig)


@pytest.fixture
def kubeconfig_dummy(tmpdir) -> str:
    return _kubeconfig(tmpdir, "ctx")


@pytest.fixture
def kubeconfig_with_namespace(tmpdir) -> str:
    return _kubeconfig(tmpdir, "ctx-with-namespace")


def test_namespace_autodetect_fails(kubeconfig_dummy):
    got = _detect_current_namespace(kubeconfig_dummy)
    assert got is None


def test_namespace_autodetect_from_kubeconfig_active_context(kubeconfig_with_namespace):
    got = _detect_current_namespace(kubeconfig_with_namespace)
    assert got == "my-namespace"


def test_pipes_client_namespace_autodetection_from_secret(tmpdir, kubeconfig_dummy):
    namespace_secret_path = Path(tmpdir) / "namespace_secret"
    namespace_secret_path.write_text("my-namespace-from-secret")
    got = _detect_current_namespace(kubeconfig_with_namespace, namespace_secret_path)
    assert got == "my-namespace-from-secret"

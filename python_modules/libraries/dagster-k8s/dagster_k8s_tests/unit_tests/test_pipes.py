from pathlib import Path

import pytest
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.utils import make_new_run_id
from dagster.components.core.tree import ComponentTree
from dagster_k8s.component import PipesK8sComponent
from dagster_k8s.pipes import (
    _DEV_NULL_MESSAGE_WRITER,
    _detect_current_namespace,
    build_pod_body,
    get_pod_name,
)
from dagster_pipes import DAGSTER_PIPES_CONTEXT_ENV_VAR, DAGSTER_PIPES_MESSAGES_ENV_VAR


@pytest.fixture
def test_image():
    return "my_test_image"


def test_pod_building_min_info(test_image):
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


def test_pod_building_common(test_image):
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


def test_pod_building_with_spec(test_image):
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


def test_pod_building_no_image_failure(test_image):
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


def test_pod_building_multiple_containers_must_specify_image_and_name(test_image):
    # specifying other containers means we need to specify image and name
    with pytest.raises(DagsterInvariantViolationError):
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


def test_pod_building_multiple_containers_ok(test_image):
    # valid other containers
    pod = build_pod_body(
        pod_name="test",
        image=None,
        command=None,
        env_vars={},
        base_pod_spec={
            "containers": [
                {"name": "foo", "image": test_image},
                {"name": "bar", "image": test_image},
            ],
            "init_containers": [
                {"name": "init_foo", "image": test_image},
            ],
        },
        base_pod_meta=None,
    )

    assert pod.spec.containers[0].image == test_image
    assert pod.spec.containers[1].image == test_image
    assert pod.spec.init_containers[0].image == test_image


def test_pod_building_with_metadata(test_image):
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


def test_pod_building_env_overrides(test_image):
    # env overrides
    pod = build_pod_body(
        pod_name="test",
        image=None,
        command=None,
        env_vars={
            "from_arg": "arg",
            "collide": "arg",
        },
        base_pod_spec={
            "containers": [
                {
                    "name": "main",
                    "image": test_image,
                    "env": [
                        {"name": "from_spec", "value": "spec"},
                        {"name": "collide", "value": "spec"},
                    ],
                },
                {
                    "name": "second",
                    "image": test_image,
                    "env": [
                        {"name": "from_spec", "value": "spec"},
                        {"name": "collide", "value": "spec"},
                    ],
                },
            ]
        },
        base_pod_meta=None,
    )

    assert {
        container.name: [env.to_dict() for env in container.env]
        for container in pod.spec.containers
    } == {
        "main": [
            {"name": "from_spec", "value": "spec", "value_from": None},
            {"name": "collide", "value": "spec", "value_from": None},
            {"name": "from_arg", "value": "arg", "value_from": None},
            {"name": "collide", "value": "arg", "value_from": None},
        ],
        "second": [
            {"name": "from_spec", "value": "spec", "value_from": None},
            {"name": "collide", "value": "spec", "value_from": None},
        ],
    }


def test_pod_building_pipes_session_env_overrides(test_image):
    # env overrides
    pod = build_pod_body(
        pod_name="test",
        image=None,
        command=None,
        env_vars={
            DAGSTER_PIPES_CONTEXT_ENV_VAR: "context-var",
            DAGSTER_PIPES_MESSAGES_ENV_VAR: "pipes-message-var",
        },
        base_pod_spec={
            "init_containers": [
                {
                    "name": "init",
                    "image": test_image,
                },
            ],
            "containers": [
                {
                    "name": "main",
                    "image": test_image,
                    "env": [
                        {"name": "from_spec", "value": "spec"},
                        {"name": "collide", "value": "spec"},
                    ],
                },
                {
                    "name": "second",
                    "image": test_image,
                },
            ],
        },
        base_pod_meta=None,
    )

    assert {
        container.name: [env.to_dict() for env in container.env]
        for container in pod.spec.init_containers + pod.spec.containers
    } == {
        "init": [
            {"name": "DAGSTER_PIPES_CONTEXT", "value": "context-var", "value_from": None},
            {
                "name": "DAGSTER_PIPES_MESSAGES",
                "value": _DEV_NULL_MESSAGE_WRITER,
                "value_from": None,
            },
        ],
        "main": [
            {"name": "from_spec", "value": "spec", "value_from": None},
            {"name": "collide", "value": "spec", "value_from": None},
            {"name": "DAGSTER_PIPES_CONTEXT", "value": "context-var", "value_from": None},
            {"name": "DAGSTER_PIPES_MESSAGES", "value": "pipes-message-var", "value_from": None},
        ],
        "second": [
            {"name": "DAGSTER_PIPES_CONTEXT", "value": "context-var", "value_from": None},
            {
                "name": "DAGSTER_PIPES_MESSAGES",
                "value": _DEV_NULL_MESSAGE_WRITER,
                "value_from": None,
            },
        ],
    }


def test_pod_building_pipes_session_env_overrides_with_custom_pipes_message_writer(test_image):
    # env overrides
    pod = build_pod_body(
        pod_name="test",
        image=None,
        command=None,
        env_vars={
            DAGSTER_PIPES_CONTEXT_ENV_VAR: "context-var",
            DAGSTER_PIPES_MESSAGES_ENV_VAR: "pipes-message-var",
        },
        base_pod_spec={
            "init_containers": [
                {
                    "name": "init",
                    "image": test_image,
                },
            ],
            "containers": [
                {
                    "name": "main",
                    "image": test_image,
                    "env": [
                        {"name": "from_spec", "value": "spec"},
                        {"name": "collide", "value": "spec"},
                    ],
                },
                {
                    "name": "second",
                    "image": test_image,
                    "env": [
                        {"name": "DAGSTER_PIPES_MESSAGES", "value": "custom"},
                    ],
                },
            ],
        },
        base_pod_meta=None,
    )

    assert {
        container.name: [env.to_dict() for env in container.env]
        for container in pod.spec.init_containers + pod.spec.containers
    } == {
        "init": [
            {"name": "DAGSTER_PIPES_CONTEXT", "value": "context-var", "value_from": None},
            {
                "name": "DAGSTER_PIPES_MESSAGES",
                "value": _DEV_NULL_MESSAGE_WRITER,
                "value_from": None,
            },
        ],
        "main": [
            {"name": "from_spec", "value": "spec", "value_from": None},
            {"name": "collide", "value": "spec", "value_from": None},
            {"name": "DAGSTER_PIPES_CONTEXT", "value": "context-var", "value_from": None},
            {"name": "DAGSTER_PIPES_MESSAGES", "value": "pipes-message-var", "value_from": None},
        ],
        "second": [
            {"name": "DAGSTER_PIPES_MESSAGES", "value": "custom", "value_from": None},
            {"name": "DAGSTER_PIPES_CONTEXT", "value": "context-var", "value_from": None},
        ],
    }


def test_pod_building_snake_camel_case_mix(test_image):
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


def test_pod_building_common_labels_no_overrides(test_image):
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


def test_pod_building_restart_policy(test_image):
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


def test_pod_building_cannot_set_restart_policy_always(test_image):
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
    got = _detect_current_namespace(kubeconfig_with_namespace, namespace_secret_path)  # pyright: ignore[reportArgumentType]
    assert got == "my-namespace-from-secret"


def test_pipes_pod_name_sanitization():
    capital_op_name = "WHY_ARE&_YOU!_YELLING_AND_WHY_IS_THIS_OP_NAME_SO_LONG"
    run_id = make_new_run_id()
    capital_pod_name = get_pod_name(run_id, capital_op_name)
    assert capital_pod_name.startswith(f"dagster-{run_id[:18]}-why-are-you-yelling--")
    assert len(capital_pod_name) <= 63


def test_component():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="specify image property or provide base_pod_spec with one set",
    ):
        c = PipesK8sComponent.resolve_from_yaml("""
name: oops
assets:
  - key: oops
""")

    c = PipesK8sComponent.resolve_from_yaml("""
name: foo
assets:
  - key: foo
image: my_foo_image:latest
""")
    defs = c.build_defs(ComponentTree.for_test().load_context)
    assert defs
    assert len(defs.resolve_all_asset_specs()) == 1

    c = PipesK8sComponent.resolve_from_yaml("""
name: multi
assets:
  - key: bar
  - key: baz

base_pod_spec:
  containers:
    - name: main
      image: my_multi_image:1
      resources:
        requests:
          memory: "64Mi"
          cpu: "250m"
        limits:
          memory: "128Mi"
          cpu: "500m"
""")
    defs = c.build_defs(ComponentTree.for_test().load_context)
    assert defs
    assert len(defs.resolve_all_asset_specs()) == 2

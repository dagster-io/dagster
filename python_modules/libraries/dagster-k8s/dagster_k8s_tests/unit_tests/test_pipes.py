import pytest
from dagster._core.errors import DagsterInvariantViolationError
from dagster_k8s.pipes import build_pod_body


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

# pylint: disable=redefined-outer-name

import pytest
from dagster_k8s.container_context import K8sContainerContext

from dagster._utils import make_readonly_value
from dagster._core.errors import DagsterInvalidConfigError


@pytest.fixture
def container_context_config():
    return {
        "env_vars": [
            "SHARED_KEY=SHARED_VAL",
        ],
        "k8s": {
            "image_pull_policy": "Always",
            "image_pull_secrets": [{"name": "my_secret"}],
            "service_account_name": "my_service_account",
            "env_config_maps": ["my_config_map"],
            "env_secrets": ["my_secret"],
            "env_vars": ["MY_ENV_VAR"],
            "volume_mounts": [
                {
                    "mount_path": "my_mount_path",
                    "mount_propagation": "my_mount_propagation",
                    "name": "a_volume_mount_one",
                    "read_only": False,
                    "sub_path": "path/",
                }
            ],
            "volumes": [{"name": "foo", "config_map": {"name": "settings-cm"}}],
            "labels": {"foo_label": "bar_value"},
            "namespace": "my_namespace",
            "resources": {
                "requests": {"memory": "64Mi", "cpu": "250m"},
                "limits": {"memory": "128Mi", "cpu": "500m"},
            },
        },
    }


@pytest.fixture
def other_container_context_config():
    return {
        "env_vars": [
            "SHARED_OTHER_KEY=SHARED_OTHER_VAL",
        ],
        "k8s": {
            "image_pull_policy": "Never",
            "image_pull_secrets": [{"name": "your_secret"}],
            "service_account_name": "your_service_account",
            "env_config_maps": ["your_config_map"],
            "env_secrets": ["your_secret"],
            "env_vars": ["YOUR_ENV_VAR"],
            "volume_mounts": [
                {
                    "mount_path": "your_mount_path",
                    "mount_propagation": "your_mount_propagation",
                    "name": "b_volume_mount_one",
                    "read_only": True,
                    "sub_path": "your_path/",
                }
            ],
            "volumes": [{"name": "bar", "config_map": {"name": "your-settings-cm"}}],
            "labels": {"bar_label": "baz_value"},
            "namespace": "your_namespace",
            "resources": {
                "limits": {"memory": "64Mi", "cpu": "250m"},
            },
        },
    }


@pytest.fixture
def container_context_config_camel_case_volumes():
    return {
        "k8s": {
            "image_pull_policy": "Always",
            "image_pull_secrets": [{"name": "my_secret"}],
            "service_account_name": "my_service_account",
            "env_config_maps": ["my_config_map"],
            "env_secrets": ["my_secret"],
            "env_vars": ["MY_ENV_VAR"],
            "volume_mounts": [
                {
                    "mountPath": "my_mount_path",
                    "mountPropagation": "my_mount_propagation",
                    "name": "a_volume_mount_one",
                    "readOnly": False,
                    "subPath": "path/",
                }
            ],
            "volumes": [{"name": "foo", "configMap": {"name": "settings-cm"}}],
            "labels": {"foo_label": "bar_value"},
            "namespace": "my_namespace",
            "resources": {
                "requests": {"memory": "64Mi", "cpu": "250m"},
                "limits": {"memory": "128Mi", "cpu": "500m"},
            },
        }
    }


@pytest.fixture(name="empty_container_context")
def empty_container_context_fixture():
    return K8sContainerContext()


@pytest.fixture(name="container_context")
def container_context_fixture(container_context_config):
    return K8sContainerContext.create_from_config(container_context_config)


@pytest.fixture(name="other_container_context")
def other_container_context_fixture(other_container_context_config):
    return K8sContainerContext.create_from_config(other_container_context_config)


@pytest.fixture(name="container_context_camel_case_volumes")
def container_context_camel_case_volumes_fixture(container_context_config_camel_case_volumes):
    return K8sContainerContext.create_from_config(container_context_config_camel_case_volumes)


def test_empty_container_context(empty_container_context):
    assert empty_container_context.image_pull_policy == None
    assert empty_container_context.image_pull_secrets == []
    assert empty_container_context.service_account_name == None
    assert empty_container_context.env_config_maps == []
    assert empty_container_context.env_secrets == []
    assert empty_container_context.env_vars == []
    assert empty_container_context.volume_mounts == []
    assert empty_container_context.volumes == []
    assert empty_container_context.labels == {}
    assert empty_container_context.namespace == None
    assert empty_container_context.resources == {}


def test_invalid_config():
    with pytest.raises(
        DagsterInvalidConfigError, match="Errors while parsing k8s container context"
    ):
        K8sContainerContext.create_from_config(
            {"k8s": {"image_push_policy": {"foo": "bar"}}}
        )  # invalid formatting


def _check_same_sorted(list1, list2):
    assert sorted(
        [make_readonly_value(val) for val in list1], key=lambda val: val.__hash__()
    ) == sorted([make_readonly_value(val) for val in list2], key=lambda val: val.__hash__())


def test_camel_case_volumes(container_context_camel_case_volumes, container_context):
    assert container_context.volume_mounts == container_context_camel_case_volumes.volume_mounts
    assert container_context.volumes == container_context_camel_case_volumes.volumes


def test_merge(empty_container_context, container_context, other_container_context):
    assert container_context.image_pull_policy == "Always"
    assert container_context.image_pull_secrets == [{"name": "my_secret"}]
    assert container_context.service_account_name == "my_service_account"
    assert container_context.env_config_maps == ["my_config_map"]
    assert container_context.env_secrets == ["my_secret"]
    _check_same_sorted(
        container_context.env_vars,
        [
            "MY_ENV_VAR",
            "SHARED_KEY=SHARED_VAL",
        ],
    )
    assert container_context.volume_mounts == [
        {
            "mount_path": "my_mount_path",
            "mount_propagation": "my_mount_propagation",
            "name": "a_volume_mount_one",
            "read_only": False,
            "sub_path": "path/",
        }
    ]
    assert container_context.volumes == [{"name": "foo", "config_map": {"name": "settings-cm"}}]
    assert container_context.labels == {"foo_label": "bar_value"}
    assert container_context.namespace == "my_namespace"
    assert container_context.resources == {
        "requests": {"memory": "64Mi", "cpu": "250m"},
        "limits": {"memory": "128Mi", "cpu": "500m"},
    }

    merged = container_context.merge(other_container_context)

    assert merged.image_pull_policy == "Never"
    _check_same_sorted(
        merged.image_pull_secrets,
        [
            {"name": "your_secret"},
            {"name": "my_secret"},
        ],
    )
    assert merged.service_account_name == "your_service_account"
    _check_same_sorted(
        merged.env_config_maps,
        [
            "your_config_map",
            "my_config_map",
        ],
    )
    _check_same_sorted(
        merged.env_secrets,
        [
            "your_secret",
            "my_secret",
        ],
    )
    _check_same_sorted(
        merged.env_vars,
        [
            "YOUR_ENV_VAR",
            "MY_ENV_VAR",
            "SHARED_OTHER_KEY=SHARED_OTHER_VAL",
            "SHARED_KEY=SHARED_VAL",
        ],
    )
    _check_same_sorted(
        merged.volume_mounts,
        [
            {
                "mount_path": "your_mount_path",
                "mount_propagation": "your_mount_propagation",
                "name": "b_volume_mount_one",
                "read_only": True,
                "sub_path": "your_path/",
            },
            {
                "mount_path": "my_mount_path",
                "mount_propagation": "my_mount_propagation",
                "name": "a_volume_mount_one",
                "read_only": False,
                "sub_path": "path/",
            },
        ],
    )
    _check_same_sorted(
        merged.volumes,
        [
            {"name": "bar", "config_map": {"name": "your-settings-cm"}},
            {"name": "foo", "config_map": {"name": "settings-cm"}},
        ],
    )
    assert merged.labels == {"foo_label": "bar_value", "bar_label": "baz_value"}
    assert merged.namespace == "your_namespace"
    assert merged.resources == {
        "limits": {"memory": "64Mi", "cpu": "250m"},
    }

    assert container_context.merge(empty_container_context) == container_context
    assert empty_container_context.merge(container_context) == container_context

import pytest
from dagster._core.errors import DagsterInvalidConfigError
from dagster._utils import hash_collection
from dagster_k8s.container_context import K8sContainerContext


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
            "scheduler_name": "my_scheduler",
            "server_k8s_config": {
                "container_config": {"command": ["echo", "SERVER"]},
                "pod_template_spec_metadata": {"namespace": "my_pod_server_amespace"},
            },
            "run_k8s_config": {
                "container_config": {"command": ["echo", "RUN"], "tty": True},
                "pod_template_spec_metadata": {"namespace": "my_pod_namespace"},
                "pod_spec_config": {"dns_policy": "value"},
                "job_metadata": {
                    "namespace": "my_job_value",
                },
                "job_spec_config": {"backoff_limit": 120},
            },
            "env": [
                {
                    "name": "DD_AGENT_HOST",
                    "value_from": {"field_ref": {"field_path": "status.hostIP"}},
                },
            ],
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
            "labels": {"bar_label": "baz_value", "foo_label": "override_value"},
            "namespace": "your_namespace",
            "resources": {
                "limits": {"memory": "64Mi", "cpu": "250m"},
            },
            "scheduler_name": "my_other_scheduler",
            "run_k8s_config": {
                "container_config": {
                    "command": ["REPLACED"],
                    "stdin": True,
                },  # container_config is merged shallowly
                "pod_template_spec_metadata": {"namespace": "my_other_namespace"},
                "pod_spec_config": {
                    "dnsPolicy": "other_value"
                },  # camel case and snake case are reconciled and merged
                "job_metadata": {
                    "namespace": "my_other_job_value",
                },
                "job_spec_config": {"backoffLimit": 240},
            },
            "env": [{"name": "FOO", "value": "BAR"}],
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
    assert empty_container_context.image_pull_policy is None
    assert empty_container_context.image_pull_secrets == []
    assert empty_container_context.service_account_name is None
    assert empty_container_context.env_config_maps == []
    assert empty_container_context.env_secrets == []
    assert empty_container_context.env_vars == []
    assert empty_container_context.volume_mounts == []
    assert empty_container_context.volumes == []
    assert empty_container_context.labels == {}
    assert empty_container_context.namespace is None
    assert empty_container_context.resources == {}
    assert empty_container_context.scheduler_name is None
    assert all(
        empty_container_context.server_k8s_config[key] == {}
        for key in empty_container_context.server_k8s_config
    )
    assert all(
        empty_container_context.run_k8s_config[key] == {}
        for key in empty_container_context.run_k8s_config
    )
    assert empty_container_context.env == []


def test_invalid_config():
    with pytest.raises(
        DagsterInvalidConfigError, match="Errors while parsing k8s container context"
    ):
        K8sContainerContext.create_from_config(
            {"k8s": {"image_push_policy": {"foo": "bar"}}}
        )  # invalid formatting


def _check_same_sorted(list1, list2):
    key_fn = lambda x: hash_collection(x) if isinstance(x, (list, dict)) else hash(x)
    sorted1 = sorted(list1, key=key_fn)
    sorted2 = sorted(list2, key=key_fn)
    assert sorted1 == sorted2


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
    assert container_context.scheduler_name == "my_scheduler"

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
    assert merged.labels == {"foo_label": "override_value", "bar_label": "baz_value"}
    assert merged.namespace == "your_namespace"
    assert merged.resources == {
        "limits": {"memory": "64Mi", "cpu": "250m"},
    }
    assert merged.scheduler_name == "my_other_scheduler"

    assert merged.run_k8s_config == {
        "container_config": {
            "command": ["REPLACED"],
            "stdin": True,
            "tty": True,
        },
        "pod_template_spec_metadata": {"namespace": "my_other_namespace"},
        "pod_spec_config": {"dns_policy": "other_value"},
        "job_metadata": {
            "namespace": "my_other_job_value",
        },
        "job_spec_config": {"backoff_limit": 240},
        "job_config": {},
    }
    _check_same_sorted(
        merged.env,
        [
            {"name": "FOO", "value": "BAR"},
            {"name": "DD_AGENT_HOST", "value_from": {"field_ref": {"field_path": "status.hostIP"}}},
        ],
    )

    assert container_context.merge(empty_container_context) == container_context
    assert empty_container_context.merge(container_context) == container_context
    assert other_container_context.merge(empty_container_context) == other_container_context

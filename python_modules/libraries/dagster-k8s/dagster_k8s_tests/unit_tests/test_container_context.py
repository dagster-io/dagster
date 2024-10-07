import pytest
from dagster._core.errors import DagsterInvalidConfigError
from dagster._utils import hash_collection
from dagster_k8s.container_context import K8sConfigMergeBehavior, K8sContainerContext
from dagster_k8s.job import (
    DagsterK8sJobConfig,
    UserDefinedDagsterK8sConfig,
    construct_dagster_k8s_job,
)


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
            "env_vars": ["MY_ENV_VAR=my_val"],
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
                "service_metadata": {"annotations": {"foo_service": "bar"}},
                "deployment_metadata": {"annotations": {"foo_deployment": "baz"}},
            },
            "run_k8s_config": {
                "container_config": {"command": ["echo", "RUN"], "tty": True},
                "pod_template_spec_metadata": {
                    "namespace": "my_pod_namespace",
                    "labels": {"baz": "quux", "norm": "boo"},
                },
                "pod_spec_config": {
                    "dns_policy": "value",
                    "imagePullSecrets": [
                        {"name": "image-secret-1"},
                        {"name": "image-secret-2"},
                    ],
                    "securityContext": {
                        "supplementalGroups": [
                            1234,
                        ]
                    },
                },
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
            "env_vars": ["YOUR_ENV_VAR=your_val"],
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
                "pod_template_spec_metadata": {
                    "namespace": "my_other_namespace",
                    "labels": {"foo": "bar", "norm": "abc"},
                },
                "pod_spec_config": {
                    "dnsPolicy": "other_value",
                    "imagePullSecrets": [
                        {"name": "image-secret-2"},
                        {"name": "image-secret-3"},
                    ],
                    "securityContext": {
                        "supplementalGroups": [
                            5678,
                        ]
                    },
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
            "env_vars": ["MY_ENV_VAR=my_val"],
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
    assert empty_container_context.namespace is None

    assert empty_container_context.run_k8s_config == UserDefinedDagsterK8sConfig(
        container_config={},
        pod_template_spec_metadata={},
        pod_spec_config={},
        job_config={},
        job_metadata={},
        job_spec_config={},
        merge_behavior=K8sConfigMergeBehavior.DEEP,
    )
    assert empty_container_context.server_k8s_config == UserDefinedDagsterK8sConfig(
        container_config={},
        pod_template_spec_metadata={},
        pod_spec_config={},
        job_config={},
        job_metadata={},
        job_spec_config={},
        merge_behavior=K8sConfigMergeBehavior.DEEP,
    )


def test_container_context(container_context):
    assert container_context.run_k8s_config == UserDefinedDagsterK8sConfig(
        container_config={
            "env": [
                {"name": "SHARED_KEY", "value": "SHARED_VAL"},
                {"name": "MY_ENV_VAR", "value": "my_val"},
                {
                    "name": "DD_AGENT_HOST",
                    "value_from": {"field_ref": {"field_path": "status.hostIP"}},
                },
            ],
            "volume_mounts": [
                {
                    "name": "a_volume_mount_one",
                    "mount_path": "my_mount_path",
                    "mount_propagation": "my_mount_propagation",
                    "read_only": False,
                    "sub_path": "path/",
                }
            ],
            "resources": {
                "limits": {"memory": "128Mi", "cpu": "500m"},
                "requests": {"memory": "64Mi", "cpu": "250m"},
            },
            "image_pull_policy": "Always",
            "env_from": [
                {"config_map_ref": {"name": "my_config_map"}},
                {"secret_ref": {"name": "my_secret"}},
            ],
            "command": ["echo", "RUN"],
            "tty": True,
        },
        pod_template_spec_metadata={
            "labels": {"foo_label": "bar_value", "baz": "quux", "norm": "boo"},
            "namespace": "my_pod_namespace",
        },
        pod_spec_config={
            "image_pull_secrets": [
                {"name": "my_secret"},
                {"name": "image-secret-1"},
                {"name": "image-secret-2"},
            ],
            "volumes": [{"name": "foo", "config_map": {"name": "settings-cm"}}],
            "service_account_name": "my_service_account",
            "scheduler_name": "my_scheduler",
            "dns_policy": "value",
            "security_context": {"supplemental_groups": [1234]},
        },
        job_config={},
        job_metadata={"labels": {"foo_label": "bar_value"}, "namespace": "my_job_value"},
        job_spec_config={"backoff_limit": 120},
        merge_behavior=K8sConfigMergeBehavior.DEEP,
    )

    assert container_context.server_k8s_config == UserDefinedDagsterK8sConfig(
        container_config={
            "env": [
                {"name": "SHARED_KEY", "value": "SHARED_VAL"},
                {"name": "MY_ENV_VAR", "value": "my_val"},
                {
                    "name": "DD_AGENT_HOST",
                    "value_from": {"field_ref": {"field_path": "status.hostIP"}},
                },
            ],
            "volume_mounts": [
                {
                    "name": "a_volume_mount_one",
                    "mount_path": "my_mount_path",
                    "mount_propagation": "my_mount_propagation",
                    "read_only": False,
                    "sub_path": "path/",
                }
            ],
            "resources": {
                "limits": {"memory": "128Mi", "cpu": "500m"},
                "requests": {"memory": "64Mi", "cpu": "250m"},
            },
            "image_pull_policy": "Always",
            "env_from": [
                {"config_map_ref": {"name": "my_config_map"}},
                {"secret_ref": {"name": "my_secret"}},
            ],
            "command": ["echo", "SERVER"],
        },
        pod_template_spec_metadata={
            "labels": {"foo_label": "bar_value"},
            "namespace": "my_pod_server_amespace",
        },
        pod_spec_config={
            "image_pull_secrets": [{"name": "my_secret"}],
            "volumes": [{"name": "foo", "config_map": {"name": "settings-cm"}}],
            "service_account_name": "my_service_account",
            "scheduler_name": "my_scheduler",
        },
        job_config={},
        job_metadata={},
        job_spec_config={},
        deployment_metadata={
            "labels": {"foo_label": "bar_value"},
            "annotations": {"foo_deployment": "baz"},
        },
        service_metadata={
            "labels": {"foo_label": "bar_value"},
            "annotations": {"foo_service": "bar"},
        },
        merge_behavior=K8sConfigMergeBehavior.DEEP,
    )


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
    assert container_context.run_k8s_config.pod_spec_config["volumes"]
    assert container_context.run_k8s_config.container_config["volume_mounts"]

    assert (
        container_context.run_k8s_config.pod_spec_config["volumes"]
        == container_context_camel_case_volumes.run_k8s_config.pod_spec_config["volumes"]
    )
    assert (
        container_context.run_k8s_config.container_config["volume_mounts"]
        == container_context_camel_case_volumes.run_k8s_config.container_config["volume_mounts"]
    )


def test_merge(empty_container_context, container_context, other_container_context):
    merged = container_context.merge(other_container_context)

    assert merged.run_k8s_config == UserDefinedDagsterK8sConfig(
        container_config={
            "env": [
                {"name": "SHARED_KEY", "value": "SHARED_VAL"},
                {"name": "MY_ENV_VAR", "value": "my_val"},
                {
                    "name": "DD_AGENT_HOST",
                    "value_from": {"field_ref": {"field_path": "status.hostIP"}},
                },
                {"name": "SHARED_OTHER_KEY", "value": "SHARED_OTHER_VAL"},
                {"name": "YOUR_ENV_VAR", "value": "your_val"},
                {"name": "FOO", "value": "BAR"},
            ],
            "volume_mounts": [
                {
                    "name": "a_volume_mount_one",
                    "mount_path": "my_mount_path",
                    "mount_propagation": "my_mount_propagation",
                    "read_only": False,
                    "sub_path": "path/",
                },
                {
                    "name": "b_volume_mount_one",
                    "mount_path": "your_mount_path",
                    "mount_propagation": "your_mount_propagation",
                    "read_only": True,
                    "sub_path": "your_path/",
                },
            ],
            "resources": {
                "limits": {"memory": "64Mi", "cpu": "250m"},
                "requests": {"memory": "64Mi", "cpu": "250m"},
            },
            "image_pull_policy": "Never",
            "env_from": [
                {"config_map_ref": {"name": "my_config_map"}},
                {"secret_ref": {"name": "my_secret"}},
                {"config_map_ref": {"name": "your_config_map"}},
                {"secret_ref": {"name": "your_secret"}},
            ],
            "command": ["REPLACED"],
            "tty": True,
            "stdin": True,
        },
        pod_template_spec_metadata={
            "labels": {
                "foo_label": "override_value",
                "baz": "quux",
                "norm": "abc",
                "bar_label": "baz_value",
                "foo": "bar",
            },
            "namespace": "my_other_namespace",
        },
        pod_spec_config={
            "image_pull_secrets": [
                {"name": "my_secret"},
                {"name": "image-secret-1"},
                {"name": "image-secret-2"},
                {"name": "your_secret"},
                {"name": "image-secret-3"},
            ],
            "volumes": [
                {"name": "foo", "config_map": {"name": "settings-cm"}},
                {"name": "bar", "config_map": {"name": "your-settings-cm"}},
            ],
            "service_account_name": "your_service_account",
            "scheduler_name": "my_other_scheduler",
            "dns_policy": "other_value",
            "security_context": {"supplemental_groups": [1234, 5678]},
        },
        job_config={},
        job_metadata={
            "labels": {"foo_label": "override_value", "bar_label": "baz_value"},
            "namespace": "my_other_job_value",
        },
        job_spec_config={"backoff_limit": 240},
        merge_behavior=K8sConfigMergeBehavior.DEEP,
    )

    assert container_context.merge(empty_container_context) == container_context
    assert empty_container_context.merge(container_context) == container_context
    assert other_container_context.merge(empty_container_context) == other_container_context

    shallow_merged_container_context = container_context.merge(
        other_container_context._replace(
            run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                {
                    **other_container_context.run_k8s_config.to_dict(),
                    "merge_behavior": K8sConfigMergeBehavior.SHALLOW.value,
                }
            )
        ),
    )

    assert shallow_merged_container_context.run_k8s_config == UserDefinedDagsterK8sConfig(
        container_config={
            "env": [
                {"name": "SHARED_OTHER_KEY", "value": "SHARED_OTHER_VAL"},
                {"name": "YOUR_ENV_VAR", "value": "your_val"},
                {"name": "FOO", "value": "BAR"},
            ],
            "volume_mounts": [
                {
                    "name": "b_volume_mount_one",
                    "mount_path": "your_mount_path",
                    "mount_propagation": "your_mount_propagation",
                    "read_only": True,
                    "sub_path": "your_path/",
                }
            ],
            "resources": {"limits": {"memory": "64Mi", "cpu": "250m"}},
            "image_pull_policy": "Never",
            "env_from": [
                {"config_map_ref": {"name": "your_config_map"}},
                {"secret_ref": {"name": "your_secret"}},
            ],
            "command": ["REPLACED"],
            "tty": True,
            "stdin": True,
        },
        pod_template_spec_metadata={
            "labels": {
                "bar_label": "baz_value",
                "foo_label": "override_value",
                "foo": "bar",
                "norm": "abc",
            },
            "namespace": "my_other_namespace",
        },
        pod_spec_config={
            "image_pull_secrets": [
                {"name": "your_secret"},
                {"name": "image-secret-2"},
                {"name": "image-secret-3"},
            ],
            "volumes": [{"name": "bar", "config_map": {"name": "your-settings-cm"}}],
            "service_account_name": "your_service_account",
            "scheduler_name": "my_other_scheduler",
            "dns_policy": "other_value",
            "security_context": {"supplemental_groups": [5678]},
        },
        job_config={},
        job_metadata={
            "labels": {"bar_label": "baz_value", "foo_label": "override_value"},
            "namespace": "my_other_job_value",
        },
        job_spec_config={"backoff_limit": 240},
        merge_behavior=K8sConfigMergeBehavior.SHALLOW,
    )


@pytest.mark.parametrize(
    "only_allow_user_defined_k8s_config_fields",
    [
        {"pod_spec_config": {"image_pull_secrets": True}},
        {"pod_spec_config": {"imagePullSecrets": True}},
    ],
)
def test_only_allow_pod_spec_config(only_allow_user_defined_k8s_config_fields):
    # can set on run_k8s_config.pod_spec_config
    K8sContainerContext(
        run_k8s_config=UserDefinedDagsterK8sConfig(
            pod_spec_config={"image_pull_secrets": [{"name": "foo"}]}
        )
    ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)

    # can set image_pull_secrets as top-level field on K8sContainerContext
    K8sContainerContext(image_pull_secrets=[{"name": "foo"}]).validate_user_k8s_config_for_run(
        only_allow_user_defined_k8s_config_fields, None
    )

    # can set on server_k8s_config
    K8sContainerContext(
        server_k8s_config=UserDefinedDagsterK8sConfig(
            pod_spec_config={"image_pull_secrets": [{"name": "foo"}]}
        )
    ).validate_user_k8s_config_for_code_server(only_allow_user_defined_k8s_config_fields, None)

    # Cannot set other top-level fields on K8sContainerContext
    with pytest.raises(
        Exception, match="Attempted to create a pod with fields that violated the allowed list"
    ):
        K8sContainerContext(namespace="foo").validate_user_k8s_config_for_run(
            only_allow_user_defined_k8s_config_fields, None
        )

    # Cannot set other server_k8s_config fields on K8sContainerContext
    with pytest.raises(
        Exception, match="Attempted to create a pod with fields that violated the allowed list"
    ):
        K8sContainerContext(
            server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                {"container_config": {"command": ["echo", "HI"]}}
            )
        ).validate_user_k8s_config_for_code_server(only_allow_user_defined_k8s_config_fields, None)

    # Run validation passes since the offending field is only on server_k8s_config
    K8sContainerContext(
        server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {"container_config": {"command": ["echo", "HI"]}}
        )
    ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)

    # Cannot set other run_k8s_config fields on K8sContainerContext
    with pytest.raises(
        Exception, match="Attempted to create a pod with fields that violated the allowed list"
    ):
        K8sContainerContext(
            run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                {"container_config": {"command": ["echo", "HI"]}}
            )
        ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)


def test_only_allow_container_config():
    only_allow_user_defined_k8s_config_fields = {"container_config": {"resources": True}}

    resources = {"limits": {"cpu": "500m"}}

    # can set on run_k8s_config.pod_spec_config
    K8sContainerContext(
        run_k8s_config=UserDefinedDagsterK8sConfig(container_config={"resources": resources})
    ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)

    # can set as top-level field on K8sContainerContext
    K8sContainerContext(resources=resources).validate_user_k8s_config_for_run(
        only_allow_user_defined_k8s_config_fields, None
    )

    # can set on server_k8s_config
    K8sContainerContext(
        server_k8s_config=UserDefinedDagsterK8sConfig(container_config={"resources": resources})
    ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)

    # Cannot set other top-level fields on K8sContainerContext
    with pytest.raises(
        Exception, match="Attempted to create a pod with fields that violated the allowed list"
    ):
        K8sContainerContext(namespace="foo").validate_user_k8s_config_for_run(
            only_allow_user_defined_k8s_config_fields, None
        )

    # Cannot set other server_k8s_config fields on K8sContainerContext
    with pytest.raises(
        Exception, match="Attempted to create a pod with fields that violated the allowed list"
    ):
        K8sContainerContext(
            server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                {"container_config": {"command": ["echo", "HI"]}}
            )
        ).validate_user_k8s_config_for_code_server(only_allow_user_defined_k8s_config_fields, None)

    # validation only affects code server, not run, since it is only set on server_k8s_config
    K8sContainerContext(
        server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {"container_config": {"command": ["echo", "HI"]}}
        )
    ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)

    # Cannot set other run_k8s_config fields on K8sContainerContext
    with pytest.raises(
        Exception, match="Attempted to create a pod with fields that violated the allowed list"
    ):
        K8sContainerContext(
            run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                {"container_config": {"command": ["echo", "HI"]}}
            )
        ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)

    # validation only affects run, not code server, since it is only set on server_k8s_config
    K8sContainerContext(
        run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {"container_config": {"command": ["echo", "HI"]}}
        )
    ).validate_user_k8s_config_for_code_server(only_allow_user_defined_k8s_config_fields, None)


def test_only_allows_pod_template_spec_metadata():
    only_allow_user_defined_k8s_config_fields = {"pod_template_spec_metadata": {"labels": True}}
    labels = {"foo": "bar"}

    # can set on run_k8s_config.pod_spec_config
    K8sContainerContext(
        run_k8s_config=UserDefinedDagsterK8sConfig(pod_template_spec_metadata={"labels": labels})
    ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)

    # cannot set as top-level field on K8sContainerContext becuase it also sets job_metadata
    with pytest.raises(
        Exception, match="Attempted to create a pod with fields that violated the allowed list"
    ):
        K8sContainerContext(labels=labels).validate_user_k8s_config_for_run(
            only_allow_user_defined_k8s_config_fields, None
        )

    K8sContainerContext(labels=labels).validate_user_k8s_config_for_run(
        {
            **only_allow_user_defined_k8s_config_fields,
            "job_metadata": {"labels": True},
        },
        None,
    )

    # can set on server_k8s_config
    K8sContainerContext(
        server_k8s_config=UserDefinedDagsterK8sConfig(pod_template_spec_metadata={"labels": labels})
    ).validate_user_k8s_config_for_run(only_allow_user_defined_k8s_config_fields, None)

    # Cannot set other top-level fields on K8sContainerContext
    with pytest.raises(
        Exception, match="Attempted to create a pod with fields that violated the allowed list"
    ):
        K8sContainerContext(namespace="foo").validate_user_k8s_config_for_run(
            only_allow_user_defined_k8s_config_fields, None
        )


@pytest.mark.parametrize(
    "container_context_with_top_level_field,bad_field",
    [
        (K8sContainerContext(image_pull_policy="Never"), "container_config.image_pull_policy"),
        (
            K8sContainerContext(image_pull_secrets=[{"name": "your_secret"}]),
            "pod_spec_config.image_pull_secrets",
        ),
        (
            K8sContainerContext(
                service_account_name="your_service_account",
            ),
            "pod_spec_config.service_account_name",
        ),
        (K8sContainerContext(env_config_maps=["your_config_map"]), "container_config.env_from"),
        (
            K8sContainerContext(
                env_secrets=["your_secret"],
            ),
            "container_config.env_from",
        ),
        (
            K8sContainerContext(
                env_vars=["YOUR_ENV_VAR=your_val"],
            ),
            "container_config.env",
        ),
        (
            K8sContainerContext(
                volume_mounts=[
                    {
                        "mount_path": "your_mount_path",
                        "mount_propagation": "your_mount_propagation",
                        "name": "b_volume_mount_one",
                        "read_only": True,
                        "sub_path": "your_path/",
                    }
                ]
            ),
            "container_config.volume_mounts",
        ),
        (
            K8sContainerContext(
                volumes=[{"name": "bar", "config_map": {"name": "your-settings-cm"}}]
            ),
            "pod_spec_config.volumes",
        ),
        (
            K8sContainerContext(labels={"bar_label": "baz_value", "foo_label": "override_value"}),
            "pod_template_spec_metadata.labels",
        ),
        (K8sContainerContext(namespace="your_namespace"), "namespace"),
        (
            K8sContainerContext(
                resources={
                    "limits": {"memory": "64Mi", "cpu": "250m"},
                }
            ),
            "container_config.resources",
        ),
        (
            K8sContainerContext(scheduler_name="my_other_scheduler"),
            "pod_spec_config.scheduler_name",
        ),
        (
            K8sContainerContext(security_context={"capabilities": {"add": ["SYS_PTRACE"]}}),
            "container_config.security_context",
        ),
    ],
)
def test_top_level_fields_considered(
    container_context_with_top_level_field: K8sContainerContext, bad_field: str
):
    nothing_allowed = {}

    all_top_level_fields_allowed = {
        "container_config": {
            "image_pull_policy": True,
            "env_from": True,
            "volume_mounts": True,
            "security_context": True,
            "env": True,
            "resources": True,
        },
        "pod_spec_config": {
            "image_pull_secrets": True,
            "service_account_name": True,
            "volumes": True,
            "scheduler_name": True,
        },
        "pod_template_spec_metadata": {
            "labels": True,
        },
        "job_metadata": {
            "labels": True,
        },
        "namespace": True,
    }
    container_context_with_top_level_field.validate_user_k8s_config_for_run(
        all_top_level_fields_allowed, None
    )

    with pytest.raises(Exception, match=bad_field):
        container_context_with_top_level_field.validate_user_k8s_config_for_run(
            nothing_allowed, None
        )


def test_only_allow_user_defined_env_vars():
    allowed_env_vars = ["foo"]

    validated_context = K8sContainerContext(
        env_vars=["foo=foo_val", "bar=bar_val"],
        env=[
            {"name": "foo", "value": "baz"},
            {"name": "zup", "value": "quul"},
        ],
    ).validate_user_k8s_config_for_run(None, allowed_env_vars)

    assert validated_context.run_k8s_config.container_config["env"] == [
        {"name": "foo", "value": "foo_val"},
        {"name": "foo", "value": "baz"},
    ]

    validated_context = K8sContainerContext(
        server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {
                "container_config": {
                    "env": [
                        {"name": "foo", "value": "baz"},
                        {"name": "zup", "value": "quul"},
                    ]
                }
            }
        ),
        run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {
                "container_config": {
                    "env": [
                        {"name": "foo", "value": "gling"},
                        {"name": "lorp", "value": "quul"},
                    ]
                }
            }
        ),
    ).validate_user_k8s_config_for_run(None, allowed_env_vars)

    assert validated_context.run_k8s_config == UserDefinedDagsterK8sConfig.from_dict(
        {
            "container_config": {
                "env": [
                    {"name": "foo", "value": "gling"},
                ]
            }
        }
    )
    assert validated_context.server_k8s_config == UserDefinedDagsterK8sConfig.from_dict(
        {
            "container_config": {
                "env": [
                    {"name": "foo", "value": "baz"},
                ]
            }
        }
    )


def test_env_var_precedence():
    outer_container_context = K8sContainerContext(
        run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {"container_config": {"env": [{"name": "FOO", "value": "outercontainerconfig"}]}}
        )
    )

    inner_container_context = K8sContainerContext(
        env_vars=["FOO=innerenvvars"],
    )

    merged = outer_container_context.merge(inner_container_context)

    k8s_job_config = DagsterK8sJobConfig(
        job_image="my_image",
        dagster_home=None,
    )

    job = construct_dagster_k8s_job(
        job_config=k8s_job_config,
        args=[],
        job_name="job_name",
        pod_name="pod_name",
        component="unit_test",
        user_defined_k8s_config=merged.run_k8s_config,
    ).to_dict()

    # Inner env var is applied after the outer
    assert job["spec"]["template"]["spec"]["containers"][0]["env"] == [
        {"name": "FOO", "value": "outercontainerconfig", "value_from": None},
        {"name": "FOO", "value": "innerenvvars", "value_from": None},
    ]

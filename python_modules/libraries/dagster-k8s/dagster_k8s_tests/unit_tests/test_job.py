import re

import pytest
from dagster import (
    __version__ as dagster_version,
    graph,
    job,
    op,
)
from dagster._core.test_utils import environ
from dagster_k8s import DagsterK8sJobConfig, construct_dagster_k8s_job
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.job import (
    DAGSTER_PG_PASSWORD_ENV_VAR,
    DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED,
    USER_DEFINED_K8S_CONFIG_KEY,
    K8sConfigMergeBehavior,
    UserDefinedDagsterK8sConfig,
    get_user_defined_k8s_config,
)
from dagster_k8s.utils import sanitize_k8s_label
from dagster_shared.utils import remove_none_recursively


def test_job_serialization():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        image_pull_policy="Always",
        image_pull_secrets=[{"name": "my_secret"}],
        service_account_name=None,
        instance_config_map="some-instance-configmap",
        postgres_password_secret="some-secret-name",
        env_config_maps=None,
        env_secrets=None,
    )
    assert DagsterK8sJobConfig.from_dict(cfg.to_dict()) == cfg


def test_user_defined_k8s_config_serialization():
    cfg = UserDefinedDagsterK8sConfig(
        container_config={
            "resources": {
                "requests": {"cpu": "250m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "2560Mi"},
            }
        },
        pod_template_spec_metadata={"namespace": "value"},
        pod_spec_config={"dns_policy": "value"},
        job_config={"status": {"active": 1}},
        job_metadata={"namespace": "value"},
        job_spec_config={"backoff_limit": 120},
    )

    assert UserDefinedDagsterK8sConfig.from_dict(cfg.to_dict()) == cfg


def test_construct_dagster_k8s_job():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        image_pull_policy="Always",
        image_pull_secrets=[{"name": "my_secret"}],
        service_account_name=None,
        instance_config_map="some-instance-configmap",
        postgres_password_secret="postgres-bizbuz",
        env_config_maps=None,
        env_secrets=None,
    )
    job = construct_dagster_k8s_job(cfg, ["foo", "bar"], "job123").to_dict()
    assert job["kind"] == "Job"
    assert job["metadata"]["name"] == "job123"
    assert job["spec"]["template"]["spec"]["containers"][0]["image"] == "test/foo:latest"
    assert job["spec"]["template"]["spec"]["automount_service_account_token"]
    assert DAGSTER_PG_PASSWORD_ENV_VAR in [
        env["name"] for env in job["spec"]["template"]["spec"]["containers"][0]["env"]
    ]


def test_construct_dagster_k8s_job_no_postgres():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        image_pull_policy="Always",
        image_pull_secrets=[{"name": "my_secret"}],
        service_account_name=None,
        instance_config_map="some-instance-configmap",
        postgres_password_secret=None,
        env_config_maps=None,
        env_secrets=None,
    )
    job = construct_dagster_k8s_job(cfg, ["foo", "bar"], "job123").to_dict()
    assert job["kind"] == "Job"
    assert job["metadata"]["name"] == "job123"
    assert job["spec"]["template"]["spec"]["containers"][0]["image"] == "test/foo:latest"
    assert DAGSTER_PG_PASSWORD_ENV_VAR not in [
        env["name"] for env in job["spec"]["template"]["spec"]["containers"][0]["env"]
    ]


def test_construct_dagster_k8s_job_with_mounts():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        image_pull_policy="Always",
        image_pull_secrets=[{"name": "my_secret"}],
        service_account_name=None,
        instance_config_map="some-instance-configmap",
        postgres_password_secret=None,
        env_config_maps=None,
        env_secrets=None,
        volume_mounts=[{"name": "foo", "mountPath": "biz/buz", "subPath": "file.txt"}],
        volumes=[
            {"name": "foo", "configMap": {"name": "settings-cm"}},
        ],
    )
    job = construct_dagster_k8s_job(cfg, ["foo", "bar"], "job123").to_dict()

    assert len(job["spec"]["template"]["spec"]["volumes"]) == 1
    foo_volumes = [
        volume for volume in job["spec"]["template"]["spec"]["volumes"] if volume["name"] == "foo"
    ]
    assert len(foo_volumes) == 1
    assert foo_volumes[0]["config_map"]["name"] == "settings-cm"

    assert len(job["spec"]["template"]["spec"]["containers"][0]["volume_mounts"]) == 1
    foo_volumes_mounts = [
        volume
        for volume in job["spec"]["template"]["spec"]["containers"][0]["volume_mounts"]
        if volume["name"] == "foo"
    ]
    assert len(foo_volumes_mounts) == 1

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        image_pull_policy="Always",
        image_pull_secrets=[{"name": "my_secret"}],
        service_account_name=None,
        instance_config_map="some-instance-configmap",
        postgres_password_secret=None,
        env_config_maps=None,
        env_secrets=None,
        volume_mounts=[{"name": "foo", "mountPath": "biz/buz", "subPath": "file.txt"}],
        volumes=[
            {"name": "foo", "secret": {"secretName": "settings-secret"}},
        ],
    )
    job = construct_dagster_k8s_job(cfg, ["foo", "bar"], "job123").to_dict()
    assert len(job["spec"]["template"]["spec"]["volumes"]) == 1
    foo_volumes = [
        volume for volume in job["spec"]["template"]["spec"]["volumes"] if volume["name"] == "foo"
    ]
    assert len(foo_volumes) == 1
    assert foo_volumes[0]["secret"]["secret_name"] == "settings-secret"

    with pytest.raises(Exception, match="Unexpected keys in model class V1Volume: {'invalidKey'}"):
        DagsterK8sJobConfig(
            job_image="test/foo:latest",
            dagster_home="/opt/dagster/dagster_home",
            image_pull_policy="Always",
            image_pull_secrets=[{"name": "my_secret"}],
            service_account_name=None,
            instance_config_map="some-instance-configmap",
            postgres_password_secret=None,
            env_config_maps=None,
            env_secrets=None,
            volume_mounts=[{"name": "foo", "mountPath": "biz/buz", "subPath": "file.txt"}],
            volumes=[
                {"name": "foo", "invalidKey": "settings-secret"},
            ],
        )


def test_construct_dagster_k8s_job_with_env():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
        env_vars=["ENV_VAR_1", "ENV_VAR_2=two"],
    )
    with environ({"ENV_VAR_1": "one"}):
        job = construct_dagster_k8s_job(cfg, ["foo", "bar"], "job").to_dict()

        env = job["spec"]["template"]["spec"]["containers"][0]["env"]
        env_mapping = {env_var["name"]: env_var for env_var in env}

        # Has DAGSTER_HOME and two additional env vars
        assert len(env_mapping) == 3
        assert env_mapping["ENV_VAR_1"]["value"] == "one"
        assert env_mapping["ENV_VAR_2"]["value"] == "two"

    with pytest.raises(
        Exception, match="Tried to load environment variable ENV_VAR_1, but it was not set"
    ):
        construct_dagster_k8s_job(cfg, ["foo", "bar"], "job").to_dict()


def test_construct_dagster_k8s_job_with_user_defined_env_camelcase():
    @graph
    def user_defined_k8s_env_tags_graph():
        pass

    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_env_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "env": [
                            {"name": "ENV_VAR_1", "value": "one"},
                            {"name": "ENV_VAR_2", "value": "two"},
                            {
                                "name": "DD_AGENT_HOST",
                                "valueFrom": {"fieldRef": {"fieldPath": "status.hostIP"}},
                            },
                        ]
                    }
                }
            }
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
    )

    job = construct_dagster_k8s_job(
        cfg, ["foo", "bar"], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    env = job["spec"]["template"]["spec"]["containers"][0]["env"]
    env_mapping = remove_none_recursively({env_var["name"]: env_var for env_var in env})

    # Has DAGSTER_HOME and three additional env vars
    assert len(env_mapping) == 4
    assert env_mapping["ENV_VAR_1"]["value"] == "one"
    assert env_mapping["ENV_VAR_2"]["value"] == "two"
    assert env_mapping["DD_AGENT_HOST"]["value_from"] == {
        "field_ref": {"field_path": "status.hostIP"}
    }


def test_construct_dagster_k8s_job_with_user_defined_command():
    @graph
    def user_defined_k8s_env_tags_graph():
        pass

    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_env_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "command": ["echo", "hi"],
                    }
                }
            }
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
    )

    job = construct_dagster_k8s_job(
        cfg, ["foo", "bar"], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    command = job["spec"]["template"]["spec"]["containers"][0]["command"]
    assert command == ["echo", "hi"]


def test_construct_dagster_k8s_job_with_user_defined_env_snake_case():
    @graph
    def user_defined_k8s_env_from_tags_graph():
        pass

    # These fields still work even when using underscore keys
    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_env_from_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "env_from": [
                            {
                                "config_map_ref": {
                                    "name": "user_config_map_ref",
                                    "optional": "True",
                                }
                            },
                            {"secret_ref": {"name": "user_secret_ref_one", "optional": "True"}},
                            {
                                "secret_ref": {
                                    "name": "user_secret_ref_two",
                                    "optional": "False",
                                },
                                "prefix": "with_prefix",
                            },
                        ]
                    }
                }
            }
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
        env_config_maps=["config_map"],
        env_secrets=["secret"],
    )

    job = construct_dagster_k8s_job(
        cfg, ["foo", "bar"], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    env_from = job["spec"]["template"]["spec"]["containers"][0]["env_from"]
    env_from_mapping = {
        (env_var.get("config_map_ref") or env_var.get("secret_ref")).get("name"): env_var
        for env_var in env_from
    }

    assert len(env_from_mapping) == 5
    assert env_from_mapping["config_map"]
    assert env_from_mapping["user_config_map_ref"]
    assert env_from_mapping["secret"]
    assert env_from_mapping["user_secret_ref_one"]
    assert env_from_mapping["user_secret_ref_two"]


def test_construct_dagster_k8s_job_with_user_defined_env_from():
    @graph
    def user_defined_k8s_env_from_tags_graph():
        pass

    # These fields still work even when using underscore keys
    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_env_from_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "envFrom": [
                            {
                                "configMapRef": {
                                    "name": "user_config_map_ref",
                                    "optional": "True",
                                }
                            },
                            {"secretRef": {"name": "user_secret_ref_one", "optional": "True"}},
                            {
                                "secretRef": {
                                    "name": "user_secret_ref_two",
                                    "optional": "False",
                                },
                                "prefix": "with_prefix",
                            },
                        ]
                    }
                }
            }
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
        env_config_maps=["config_map"],
        env_secrets=["secret"],
    )

    job = construct_dagster_k8s_job(
        cfg, ["foo", "bar"], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    env_from = job["spec"]["template"]["spec"]["containers"][0]["env_from"]
    env_from_mapping = {
        (env_var.get("config_map_ref") or env_var.get("secret_ref")).get("name"): env_var
        for env_var in env_from
    }

    assert len(env_from_mapping) == 5
    assert env_from_mapping["config_map"]
    assert env_from_mapping["user_config_map_ref"]
    assert env_from_mapping["secret"]
    assert env_from_mapping["user_secret_ref_one"]
    assert env_from_mapping["user_secret_ref_two"]


def test_construct_dagster_k8s_job_with_user_defined_volume_mounts_snake_case():
    @graph
    def user_defined_k8s_volume_mounts_tags_graph():
        pass

    # volume_mounts still work even when using underscore keys
    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_volume_mounts_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "volume_mounts": [
                            {
                                "mountPath": "mount_path",
                                "mountPropagation": "mount_propagation",
                                "name": "a_volume_mount_one",
                                "readOnly": "False",
                                "subPath": "path/",
                            },
                            {
                                "mountPath": "mount_path",
                                "mountPropagation": "mount_propagation",
                                "name": "a_volume_mount_two",
                                "readOnly": "False",
                                "subPathExpr": "path/",
                            },
                        ]
                    }
                }
            }
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
    )

    job = construct_dagster_k8s_job(
        cfg, ["foo", "bar"], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    volume_mounts = job["spec"]["template"]["spec"]["containers"][0]["volume_mounts"]
    volume_mounts_mapping = {volume_mount["name"]: volume_mount for volume_mount in volume_mounts}

    assert len(volume_mounts_mapping) == 2
    assert volume_mounts_mapping["a_volume_mount_one"]
    assert volume_mounts_mapping["a_volume_mount_two"]


def test_construct_dagster_k8s_job_with_user_defined_volume_mounts_camel_case():
    @graph
    def user_defined_k8s_volume_mounts_tags_graph():
        pass

    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_volume_mounts_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "volumeMounts": [
                            {
                                "mountPath": "mount_path",
                                "mountPropagation": "mount_propagation",
                                "name": "a_volume_mount_one",
                                "readOnly": "False",
                                "subPath": "path/",
                            },
                            {
                                "mountPath": "mount_path",
                                "mountPropagation": "mount_propagation",
                                "name": "a_volume_mount_two",
                                "readOnly": "False",
                                "subPathExpr": "path/",
                            },
                        ]
                    }
                }
            }
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
    )

    job = construct_dagster_k8s_job(
        cfg, ["foo", "bar"], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    volume_mounts = job["spec"]["template"]["spec"]["containers"][0]["volume_mounts"]
    volume_mounts_mapping = {volume_mount["name"]: volume_mount for volume_mount in volume_mounts}

    assert len(volume_mounts_mapping) == 2
    assert volume_mounts_mapping["a_volume_mount_one"]
    assert volume_mounts_mapping["a_volume_mount_two"]


def test_construct_dagster_k8s_job_with_user_defined_service_account_name_snake_case():
    @graph
    def user_defined_k8s_service_account_name_tags_graph():
        pass

    # service_account_name still works
    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_service_account_name_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "pod_spec_config": {
                        "service_account_name": "this-should-take-precedence",
                    },
                },
            },
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
        service_account_name="this-should-be-overriden",
    )

    job = construct_dagster_k8s_job(
        cfg, ["foo", "bar"], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    service_account_name = job["spec"]["template"]["spec"]["service_account_name"]
    assert service_account_name == "this-should-take-precedence"


def test_construct_dagster_k8s_job_with_user_defined_service_account_name():
    @graph
    def user_defined_k8s_service_account_name_tags_graph():
        pass

    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_service_account_name_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "pod_spec_config": {
                        "serviceAccountName": "this-should-take-precedence",
                    },
                },
            },
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
        service_account_name="this-should-be-overriden",
    )

    job = construct_dagster_k8s_job(
        cfg, ["foo", "bar"], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    service_account_name = job["spec"]["template"]["spec"]["service_account_name"]
    assert service_account_name == "this-should-take-precedence"


def test_construct_dagster_k8s_job_with_deep_merge():
    @job(
        tags={
            USER_DEFINED_K8S_CONFIG_KEY: {
                "pod_template_spec_metadata": {
                    "labels": {"foo_label": "bar_value"},
                },
            }
        }
    )
    def user_defined_deep_merge_job():
        pass

    job_user_defined_k8s_config = get_user_defined_k8s_config(user_defined_deep_merge_job.tags)
    assert job_user_defined_k8s_config.merge_behavior == K8sConfigMergeBehavior.DEEP

    @op(
        tags={
            USER_DEFINED_K8S_CONFIG_KEY: {
                "pod_template_spec_metadata": {
                    "labels": {"baz_label": "quux_value"},
                },
                "merge_behavior": K8sConfigMergeBehavior.DEEP.value,
            }
        }
    )
    def user_defined_deep_merge_op():
        pass

    op_user_defined_k8s_config = get_user_defined_k8s_config(user_defined_deep_merge_op.tags)
    assert op_user_defined_k8s_config.merge_behavior == K8sConfigMergeBehavior.DEEP

    merged_k8s_config = (
        K8sContainerContext(run_k8s_config=job_user_defined_k8s_config)
        .merge(K8sContainerContext(run_k8s_config=op_user_defined_k8s_config))
        .run_k8s_config
    )

    assert merged_k8s_config.pod_template_spec_metadata["labels"] == {
        "foo_label": "bar_value",
        "baz_label": "quux_value",
    }


def test_construct_dagster_k8s_job_with_ttl_snake_case():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
    )
    job = construct_dagster_k8s_job(cfg, [], "job123").to_dict()

    assert job["spec"]["ttl_seconds_after_finished"] == DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED

    # Setting ttl_seconds_after_finished still works
    user_defined_cfg = UserDefinedDagsterK8sConfig(
        job_spec_config={"ttl_seconds_after_finished": 0},
    )
    job = construct_dagster_k8s_job(
        cfg, [], "job123", user_defined_k8s_config=user_defined_cfg
    ).to_dict()
    assert job["spec"]["ttl_seconds_after_finished"] == 0


def test_construct_dagster_k8s_job_with_ttl():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
    )
    job = construct_dagster_k8s_job(cfg, [], "job123").to_dict()

    assert job["spec"]["ttl_seconds_after_finished"] == DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED

    user_defined_cfg = UserDefinedDagsterK8sConfig(
        job_spec_config={"ttlSecondsAfterFinished": 0},
    )
    job = construct_dagster_k8s_job(
        cfg, [], "job123", user_defined_k8s_config=user_defined_cfg
    ).to_dict()
    assert job["spec"]["ttl_seconds_after_finished"] == 0


def test_construct_dagster_k8s_job_with_sidecar_container():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
    )
    job = construct_dagster_k8s_job(cfg, [], "job123").to_dict()

    assert job["spec"]["ttl_seconds_after_finished"] == DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED

    user_defined_cfg = UserDefinedDagsterK8sConfig(
        pod_spec_config={
            "containers": [{"command": ["echo", "HI"], "image": "sidecar:bar", "name": "sidecar"}]
        },
    )
    job = construct_dagster_k8s_job(
        cfg, [], "job123", user_defined_k8s_config=user_defined_cfg
    ).to_dict()

    containers = job["spec"]["template"]["spec"]["containers"]

    assert len(containers) == 2

    assert containers[0]["image"] == "test/foo:latest"

    assert containers[1]["image"] == "sidecar:bar"
    assert containers[1]["command"] == ["echo", "HI"]
    assert containers[1]["name"] == "sidecar"


def test_construct_dagster_k8s_job_with_invalid_key_raises_error():
    with pytest.raises(
        Exception, match="Unexpected keys in model class V1JobSpec: {'nonExistantKey'}"
    ):
        UserDefinedDagsterK8sConfig(
            job_spec_config={"nonExistantKey": "nonExistantValue"},
        )


def test_construct_dagster_k8s_job_with_labels():
    common_labels = {
        "app.kubernetes.io/name": "dagster",
        "app.kubernetes.io/instance": "dagster",
        "app.kubernetes.io/version": sanitize_k8s_label(dagster_version),
        "app.kubernetes.io/part-of": "dagster",
    }

    job_config_labels = {
        "foo_label_key": "bar_label_value",
    }

    user_defined_labels = {
        "user_label_key": "user_label_value",
    }

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
        labels=job_config_labels,
    )

    job1 = construct_dagster_k8s_job(
        cfg,
        [],
        "job123",
        user_defined_k8s_config=UserDefinedDagsterK8sConfig(
            pod_template_spec_metadata={"labels": user_defined_labels},
        ),
        labels={
            "dagster/job": "some_job",
            "dagster/op": "some_op",
            "dagster/run-id": "some_run_id",
        },
    ).to_dict()

    expected_labels1 = dict(
        **common_labels,
        **job_config_labels,
        **{
            "dagster/job": "some_job",
            "dagster/op": "some_op",
            "dagster/run-id": "some_run_id",
        },
    )

    expected_template_labels1 = {
        **expected_labels1,
        **user_defined_labels,
    }

    assert job1["metadata"]["labels"] == expected_labels1
    assert job1["spec"]["template"]["metadata"]["labels"] == expected_template_labels1

    job2 = construct_dagster_k8s_job(
        cfg,
        [],
        "job456",
        labels={
            "dagster/job": "long_job_name_64____01234567890123456789012345678901234567890123",
            "dagster/op": "long_op_name_64_____01234567890123456789012345678901234567890123",
            "dagster/run_id": "long_run_id_64______01234567890123456789012345678901234567890123",
        },
    ).to_dict()
    expected_labels2 = dict(
        **common_labels,
        **job_config_labels,
        **{
            # The last character should be truncated.
            "dagster/job": "long_job_name_64____0123456789012345678901234567890123456789012",
            "dagster/op": "long_op_name_64_____0123456789012345678901234567890123456789012",
            "dagster/run_id": "long_run_id_64______0123456789012345678901234567890123456789012",
        },
    )
    assert job2["metadata"]["labels"] == expected_labels2
    assert job2["spec"]["template"]["metadata"]["labels"] == expected_labels2


def test_construct_dagster_k8s_job_with_label_precedence():
    job_labels = {
        "a": "job a",
        "b": "job b",
    }

    user_labels = {
        "a": "user a",
    }

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
        labels=job_labels,
    )

    job = construct_dagster_k8s_job(
        cfg,
        [],
        "job123",
        user_defined_k8s_config=UserDefinedDagsterK8sConfig(
            pod_template_spec_metadata={"labels": user_labels},
        ),
    ).to_dict()

    assert job["metadata"]["labels"]["a"] == "job a"
    assert job["metadata"]["labels"]["b"] == "job b"

    assert job["spec"]["template"]["metadata"]["labels"]["a"] == "user a"
    assert job["spec"]["template"]["metadata"]["labels"]["b"] == "job b"


def test_construct_dagster_k8s_job_with_user_defined_image():
    @graph
    def user_defined_k8s_env_tags_graph():
        pass

    expected_image = "different_image:tag"
    user_defined_k8s_config = get_user_defined_k8s_config(
        user_defined_k8s_env_tags_graph.to_job(
            tags={
                USER_DEFINED_K8S_CONFIG_KEY: {"container_config": {"image": expected_image}},
            }
        ).tags
    )

    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
    )

    job = construct_dagster_k8s_job(
        cfg, [], "job", user_defined_k8s_config=user_defined_k8s_config
    ).to_dict()

    image = job["spec"]["template"]["spec"]["containers"][0]["image"]
    assert image == expected_image


def test_sanitize_labels():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
    )

    job = construct_dagster_k8s_job(
        cfg,
        [],
        "job456",
        labels={
            "dagster/op": r"-get_f\o.o[bar-0]-",
            "my_label": "_WhatsUP",
        },
    ).to_dict()

    assert job["metadata"]["labels"]["dagster/op"] == "get_f-o.o-bar-0"
    assert job["metadata"]["labels"]["my_label"] == "WhatsUP"


def test_construct_dagster_k8s_job_with_raw_env():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="some-instance-configmap",
    )
    with environ({"ENV_VAR_1": "one"}):
        job = construct_dagster_k8s_job(
            cfg,
            ["foo", "bar"],
            "job",
            env_vars=[
                {"name": "FOO", "value": "BAR"},
                {
                    "name": "DD_AGENT_HOST",
                    "value_from": {"field_ref": {"field_path": "status.hostIP"}},
                },
            ],
        ).to_dict()

        env = job["spec"]["template"]["spec"]["containers"][0]["env"]
        env_mapping = {env_var["name"]: env_var for env_var in env}

        # Has DAGSTER_HOME and two additional env vars
        assert len(env_mapping) == 3
        assert env_mapping["FOO"]["value"] == "BAR"
        assert (
            env_mapping["DD_AGENT_HOST"]["value_from"]["field_ref"]["field_path"] == "status.hostIP"
        )


# Taken from the k8s error message when a label is invalid
K8s_LABEL_REGEX = r"(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?"


def test_sanitize_labels_regex():
    assert re.fullmatch(K8s_LABEL_REGEX, sanitize_k8s_label("normal-string"))

    assert not re.fullmatch(
        K8s_LABEL_REGEX,
        "string-with-period.",
    )

    assert re.fullmatch(
        K8s_LABEL_REGEX,
        sanitize_k8s_label("string-with-period."),
    )

    # string that happens to end with a period after being truncated to 63 characters
    assert re.fullmatch(
        K8s_LABEL_REGEX,
        sanitize_k8s_label(
            "data_pipe_graph_abcdefghi_jklmn.raw_data_graph_abcdefghi_jklmn.opqrstuvwxyz"
        ),
    )

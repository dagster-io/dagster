import pytest
from dagster import graph
from dagster.core.test_utils import environ, remove_none_recursively
from dagster_k8s import DagsterK8sJobConfig, construct_dagster_k8s_job
from dagster_k8s.job import (
    DAGSTER_PG_PASSWORD_ENV_VAR,
    DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED,
    USER_DEFINED_K8S_CONFIG_KEY,
    UserDefinedDagsterK8sConfig,
    get_user_defined_k8s_config,
)


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
            "resouces": {
                "requests": {"cpu": "250m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "2560Mi"},
            }
        },
        pod_template_spec_metadata={"key": "value"},
        pod_spec_config={"key": "value"},
        job_config={"key": "value"},
        job_metadata={"key": "value"},
        job_spec_config={"key": "value"},
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

    assert len(job["spec"]["template"]["spec"]["volumes"]) == 2
    foo_volumes = [
        volume for volume in job["spec"]["template"]["spec"]["volumes"] if volume["name"] == "foo"
    ]
    assert len(foo_volumes) == 1
    assert foo_volumes[0]["config_map"]["name"] == "settings-cm"

    assert len(job["spec"]["template"]["spec"]["containers"][0]["volume_mounts"]) == 2
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
    assert len(job["spec"]["template"]["spec"]["volumes"]) == 2
    foo_volumes = [
        volume for volume in job["spec"]["template"]["spec"]["volumes"] if volume["name"] == "foo"
    ]
    assert len(foo_volumes) == 1
    assert foo_volumes[0]["secret"]["secret_name"] == "settings-secret"

    cfg_with_invalid_volume_key = DagsterK8sJobConfig(
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
    with pytest.raises(Exception, match="Unexpected keys in model class V1Volume: {'invalidKey'}"):
        construct_dagster_k8s_job(cfg_with_invalid_volume_key, ["foo", "bar"], "job123").to_dict()


def test_construct_dagster_k8s_job_with_env():
    with environ({"ENV_VAR_1": "one", "ENV_VAR_2": "two"}):
        cfg = DagsterK8sJobConfig(
            job_image="test/foo:latest",
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="some-instance-configmap",
            env_vars=["ENV_VAR_1", "ENV_VAR_2"],
        )

        job = construct_dagster_k8s_job(cfg, ["foo", "bar"], "job").to_dict()

        env = job["spec"]["template"]["spec"]["containers"][0]["env"]
        env_mapping = {env_var["name"]: env_var for env_var in env}

        # Has DAGSTER_HOME and two additional env vars
        assert len(env_mapping) == 3
        assert env_mapping["ENV_VAR_1"]["value"] == "one"
        assert env_mapping["ENV_VAR_2"]["value"] == "two"


def test_construct_dagster_k8s_job_with_user_defined_env():
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


def test_construct_dagster_k8s_job_with_user_defined_env_from():
    @graph
    def user_defined_k8s_env_from_tags_graph():
        pass

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


def test_construct_dagster_k8s_job_with_user_defined_volume_mounts():
    @graph
    def user_defined_k8s_volume_mounts_tags_graph():
        pass

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

    assert len(volume_mounts_mapping) == 3
    assert volume_mounts_mapping["dagster-instance"]
    assert volume_mounts_mapping["a_volume_mount_one"]
    assert volume_mounts_mapping["a_volume_mount_two"]


def test_construct_dagster_k8s_job_with_user_defined_service_account_name():
    @graph
    def user_defined_k8s_service_account_name_tags_graph():
        pass

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


def test_construct_dagster_k8s_job_with_ttl():
    cfg = DagsterK8sJobConfig(
        job_image="test/foo:latest",
        dagster_home="/opt/dagster/dagster_home",
        instance_config_map="test",
    )
    job = construct_dagster_k8s_job(cfg, [], "job123").to_dict()
    assert job["spec"]["ttl_seconds_after_finished"] == DEFAULT_K8S_JOB_TTL_SECONDS_AFTER_FINISHED

    user_defined_cfg = UserDefinedDagsterK8sConfig(
        job_spec_config={"ttl_seconds_after_finished": 0},
    )
    job = construct_dagster_k8s_job(
        cfg, [], "job123", user_defined_k8s_config=user_defined_cfg
    ).to_dict()
    assert job["spec"]["ttl_seconds_after_finished"] == 0

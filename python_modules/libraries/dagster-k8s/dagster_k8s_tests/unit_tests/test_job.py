from dagster import graph
from dagster.core.test_utils import environ
from dagster_k8s import DagsterK8sJobConfig, construct_dagster_k8s_job
from dagster_k8s.job import (
    DAGSTER_PG_PASSWORD_ENV_VAR,
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
        volume_mounts=[
            {"name": "foo", "path": "biz/buz", "sub_path": "file.txt", "configmap": "settings-cm"}
        ],
    )
    job = construct_dagster_k8s_job(cfg, ["foo", "bar"], "job123").to_dict()

    assert len(job["spec"]["template"]["spec"]["volumes"]) == 2
    foo_volumes = [
        volume for volume in job["spec"]["template"]["spec"]["volumes"] if volume["name"] == "foo"
    ]
    assert len(foo_volumes) == 1

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
        volume_mounts=[
            {"name": "foo", "path": "biz/buz", "sub_path": "file.txt", "secret": "settings-secret"}
        ],
    )
    construct_dagster_k8s_job(cfg, ["foo", "bar"], "job123").to_dict()


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
    env_mapping = {env_var["name"]: env_var for env_var in env}

    # Has DAGSTER_HOME and two additional env vars
    assert len(env_mapping) == 3
    assert env_mapping["ENV_VAR_1"]["value"] == "one"
    assert env_mapping["ENV_VAR_2"]["value"] == "two"

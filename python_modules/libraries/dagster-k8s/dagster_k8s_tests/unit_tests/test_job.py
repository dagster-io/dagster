from dagster_k8s import DagsterK8sJobConfig, construct_dagster_k8s_job
from dagster_k8s.job import DAGSTER_PG_PASSWORD_ENV_VAR, UserDefinedDagsterK8sConfig


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

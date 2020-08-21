from dagster_k8s import DagsterK8sJobConfig
from dagster_k8s.job import UserDefinedDagsterK8sConfig


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

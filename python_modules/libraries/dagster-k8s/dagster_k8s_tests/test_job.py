from dagster_k8s import DagsterK8sJobConfig


def test_job_serialization():

    cfg = DagsterK8sJobConfig(
        job_image='test/foo:latest',
        dagster_home='/opt/dagster/dagster_home',
        image_pull_policy='Always',
        image_pull_secrets=[{'name': 'my_secret'}],
        service_account_name=None,
        instance_config_map='some-instance-configmap',
        postgres_password_secret='some-secret-name',
        env_config_maps=None,
        env_secrets=None,
    )
    assert DagsterK8sJobConfig.from_dict(cfg.to_dict()) == cfg

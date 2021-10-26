import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.redis import Redis
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-env-dagit.yaml",
        model=models.V1ConfigMap,
    )


def test_celery_backend_with_redis_without_password(template: HelmTemplate):
    redis_host = "host"
    redis_port = 6379
    broker_db_number = 20
    backend_db_number = 21
    helm_values = DagsterHelmValues.construct(
        redis=Redis.construct(
            enabled=True,
            usePassword=False,
            host=redis_host,
            port=redis_port,
            brokerDbNumber=broker_db_number,
            backendDbNumber=backend_db_number,
        ),
    )

    [configmap] = template.render(helm_values)

    expected_celery_broker = f"redis://{redis_host}:{redis_port}/{broker_db_number}"
    expected_celery_backend = f"redis://{redis_host}:{redis_port}/{backend_db_number}"

    assert configmap.data["DAGSTER_K8S_CELERY_BROKER"] == expected_celery_broker
    assert configmap.data["DAGSTER_K8S_CELERY_BACKEND"] == expected_celery_backend


def test_celery_backend_with_redis_with_password(template: HelmTemplate):
    redis_password = "password"
    redis_host = "host"
    redis_port = 6379
    broker_db_number = 20
    backend_db_number = 21
    helm_values = DagsterHelmValues.construct(
        redis=Redis.construct(
            enabled=True,
            usePassword=True,
            password=redis_password,
            host=redis_host,
            port=redis_port,
            brokerDbNumber=broker_db_number,
            backendDbNumber=backend_db_number,
        ),
    )

    [configmap] = template.render(helm_values)

    expected_celery_broker = (
        f"redis://:{redis_password}@{redis_host}:{redis_port}/{broker_db_number}"
    )
    expected_celery_backend = (
        f"redis://:{redis_password}@{redis_host}:{redis_port}/{backend_db_number}"
    )

    assert configmap.data["DAGSTER_K8S_CELERY_BROKER"] == expected_celery_broker
    assert configmap.data["DAGSTER_K8S_CELERY_BACKEND"] == expected_celery_backend


def test_celery_backend_override_connection_string(template: HelmTemplate):
    broker_url = "host:6380,password=password,ssl=True"
    backend_url = "host:6381,password=password,ssl=True"
    helm_values = DagsterHelmValues.construct(
        redis=Redis.construct(
            enabled=True,
            brokerUrl=broker_url,
            backendUrl=backend_url,
        ),
    )

    [configmap] = template.render(helm_values)

    assert configmap.data["DAGSTER_K8S_CELERY_BROKER"] == broker_url
    assert configmap.data["DAGSTER_K8S_CELERY_BACKEND"] == backend_url

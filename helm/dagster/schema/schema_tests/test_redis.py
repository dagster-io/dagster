import base64

import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.redis import Redis
from schema.charts.dagster.subschema.run_launcher import RunLauncher, RunLauncherType
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/secret-celery-config.yaml",
        model=models.V1Secret,
    )


def test_default_redis_config(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        generateCeleryConfigSecret=True,
        runLauncher=RunLauncher.construct(type=RunLauncherType.CELERY),
        redis=Redis.construct(
            enabled=True,
            host="myhost",
        ),
    )
    [secret] = template.render(helm_values)

    expected_celery_broker = "redis://myhost:6379/0"
    expected_celery_backend = "redis://myhost:6379/0"

    assert secret.data["DAGSTER_CELERY_BROKER_URL"] == base64.b64encode(
        bytes(expected_celery_broker, encoding="utf-8")
    ).decode("utf-8")
    assert secret.data["DAGSTER_CELERY_BACKEND_URL"] == base64.b64encode(
        bytes(expected_celery_backend, encoding="utf-8")
    ).decode("utf-8")


def test_celery_backend_with_redis_without_password(template: HelmTemplate):
    redis_host = "host"
    redis_port = 6379
    broker_db_number = 20
    backend_db_number = 21
    helm_values = DagsterHelmValues.construct(
        generateCeleryConfigSecret=True,
        runLauncher=RunLauncher.construct(type=RunLauncherType.CELERY),
        redis=Redis.construct(
            enabled=True,
            usePassword=False,
            host=redis_host,
            port=redis_port,
            brokerDbNumber=broker_db_number,
            backendDbNumber=backend_db_number,
        ),
    )

    [secret] = template.render(helm_values)

    expected_celery_broker = f"redis://{redis_host}:{redis_port}/{broker_db_number}"
    expected_celery_backend = f"redis://{redis_host}:{redis_port}/{backend_db_number}"

    assert secret.data["DAGSTER_CELERY_BROKER_URL"] == base64.b64encode(
        bytes(expected_celery_broker, encoding="utf-8")
    ).decode("utf-8")
    assert secret.data["DAGSTER_CELERY_BACKEND_URL"] == base64.b64encode(
        bytes(expected_celery_backend, encoding="utf-8")
    ).decode("utf-8")


def test_celery_backend_with_redis_with_password(template: HelmTemplate):
    redis_password = "password"
    redis_host = "host"
    redis_port = 6379
    broker_db_number = 20
    backend_db_number = 21
    helm_values = DagsterHelmValues.construct(
        generateCeleryConfigSecret=True,
        runLauncher=RunLauncher.construct(type=RunLauncherType.CELERY),
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

    [secret] = template.render(helm_values)

    expected_celery_broker = (
        f"redis://:{redis_password}@{redis_host}:{redis_port}/{broker_db_number}"
    )
    expected_celery_backend = (
        f"redis://:{redis_password}@{redis_host}:{redis_port}/{backend_db_number}"
    )

    assert secret.data["DAGSTER_CELERY_BROKER_URL"] == base64.b64encode(
        bytes(expected_celery_broker, encoding="utf-8")
    ).decode("utf-8")
    assert secret.data["DAGSTER_CELERY_BACKEND_URL"] == base64.b64encode(
        bytes(expected_celery_backend, encoding="utf-8")
    ).decode("utf-8")


def test_celery_backend_override_connection_string(template: HelmTemplate):
    broker_url = "host:6380,password=password,ssl=True"
    backend_url = "host:6381,password=password,ssl=True"
    helm_values = DagsterHelmValues.construct(
        generateCeleryConfigSecret=True,
        runLauncher=RunLauncher.construct(type=RunLauncherType.CELERY),
        redis=Redis.construct(
            enabled=True,
            brokerUrl=broker_url,
            backendUrl=backend_url,
        ),
    )

    [secret] = template.render(helm_values)

    assert secret.data["DAGSTER_CELERY_BROKER_URL"] == base64.b64encode(
        bytes(broker_url, encoding="utf-8")
    ).decode("utf-8")
    assert secret.data["DAGSTER_CELERY_BACKEND_URL"] == base64.b64encode(
        bytes(backend_url, encoding="utf-8")
    ).decode("utf-8")


def test_celery_backend_override_only_one(template: HelmTemplate):
    custom_url = "host:6380,password=password,ssl=True"
    default_url = "redis://myhost:6379/0"

    # Override broker, not backend
    helm_values = DagsterHelmValues.construct(
        generateCeleryConfigSecret=True,
        runLauncher=RunLauncher.construct(type=RunLauncherType.CELERY),
        redis=Redis.construct(
            enabled=True,
            brokerUrl=custom_url,
            host="myhost",
        ),
    )

    [secret] = template.render(helm_values)

    assert secret.data["DAGSTER_CELERY_BROKER_URL"] == base64.b64encode(
        bytes(custom_url, encoding="utf-8")
    ).decode("utf-8")
    assert secret.data["DAGSTER_CELERY_BACKEND_URL"] == base64.b64encode(
        bytes(default_url, encoding="utf-8")
    ).decode("utf-8")

    # Override backend, not broker
    helm_values = DagsterHelmValues.construct(
        generateCeleryConfigSecret=True,
        runLauncher=RunLauncher.construct(type=RunLauncherType.CELERY),
        redis=Redis.construct(
            enabled=True,
            backendUrl=custom_url,
            host="myhost",
        ),
    )

    [secret] = template.render(helm_values)

    assert secret.data["DAGSTER_CELERY_BROKER_URL"] == base64.b64encode(
        bytes(default_url, encoding="utf-8")
    ).decode("utf-8")
    assert secret.data["DAGSTER_CELERY_BACKEND_URL"] == base64.b64encode(
        bytes(custom_url, encoding="utf-8")
    ).decode("utf-8")

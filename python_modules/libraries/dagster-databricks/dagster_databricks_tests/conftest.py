from importlib.metadata import version

import pytest
from databricks.sdk.config import Config
from databricks.sdk.service.jobs import JobsHealthMetric, JobsHealthOperator

DATABRICKS_SDK_VERSION = tuple(int(p) for p in version("databricks-sdk").split(".")[:2])


@pytest.fixture(autouse=True)
def skip_databricks_host_metadata(request, monkeypatch):
    # Since databricks-sdk 0.99, Config.__init__ queries {host}/.well-known/databricks-config
    # and retries unreachable test hosts for up to 5 minutes before falling back to explicit
    # config. Tests against a real workspace (via the databricks_client fixture) keep the probe.
    if DATABRICKS_SDK_VERSION < (0, 99) or "databricks_client" in request.fixturenames:
        return
    monkeypatch.setattr(Config, "_resolve_host_metadata", lambda self: None)


@pytest.fixture
def databricks_run_config() -> dict:
    return {
        "run_name": "dagster-databricks-test",
        "cluster": {"existing": "foo"},
        "task": {
            "spark_jar_task": {"main_class_name": "my-class", "parameters": ["first", "second"]}
        },
        "idempotency_token": "abc123",
        "timeout_seconds": 100,
        "job_health_settings": [
            {
                "metric": JobsHealthMetric.RUN_DURATION_SECONDS.value,
                "op": JobsHealthOperator.GREATER_THAN.value,
                "value": 100,
            }
        ],
    }

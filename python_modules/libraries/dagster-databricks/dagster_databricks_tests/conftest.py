import pytest
from databricks.sdk.config import Config
from databricks.sdk.service.jobs import JobsHealthMetric, JobsHealthOperator


@pytest.fixture(autouse=True)
def skip_databricks_host_metadata(monkeypatch):
    # Since databricks-sdk 0.99, Config.__init__ queries {host}/.well-known/databricks-config
    # and retries unreachable test hosts for up to 5 minutes before falling back to explicit
    # config. raising=False keeps older SDK versions, which lack the method, working.
    monkeypatch.setattr(Config, "_resolve_host_metadata", lambda self: None, raising=False)


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

import pytest
from databricks.sdk.config import Config
from databricks.sdk.service.jobs import JobsHealthMetric, JobsHealthOperator


@pytest.fixture(autouse=True)
def disable_databricks_host_metadata_probe(monkeypatch):
    # The SDK fetches host metadata when building a client and retries for up to 5 minutes
    # on fake hosts, outlasting the test timeout. Absent in older SDK versions.
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

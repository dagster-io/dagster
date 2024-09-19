import pytest
from databricks.sdk.service.jobs import JobsHealthMetric, JobsHealthOperator


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

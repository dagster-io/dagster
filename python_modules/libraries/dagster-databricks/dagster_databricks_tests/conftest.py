import pytest


@pytest.fixture
def databricks_run_config():
    return {
        "run_name": "dagster-databricks-test",
        "cluster": {"existing": "foo"},
        "task": {
            "spark_jar_task": {"main_class_name": "my-class", "parameters": ["first", "second"]}
        },
        "libraries": [
            {"pypi": {"package": "python_package_test==1.0.0"}},
        ]
    }

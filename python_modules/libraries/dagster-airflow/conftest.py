# fixtures: redundant alias to mark them as used imports
from dagster_airflow_tests.test_fixtures import (
    dagster_airflow_custom_operator_pipeline as dagster_airflow_custom_operator_pipeline,
    dagster_airflow_docker_operator_pipeline as dagster_airflow_docker_operator_pipeline,
    dagster_airflow_python_operator_pipeline as dagster_airflow_python_operator_pipeline,
)


# See: https://stackoverflow.com/a/31526934/324449
def pytest_addoption(parser):
    # We catch the ValueError to support cases where we are loading multiple test suites, e.g., in
    # the VSCode test explorer. When pytest tries to add an option twice, we get, e.g.
    #
    #    ValueError: option names {'--cluster-provider'} already added

    # Use kind or some other cluster provider?
    try:
        parser.addoption("--cluster-provider", action="store", default="kind")
    except ValueError:
        pass

    # Specify an existing kind cluster name to use
    try:
        parser.addoption("--kind-cluster", action="store")
    except ValueError:
        pass

    # Keep resources around after tests are done
    try:
        parser.addoption("--no-cleanup", action="store_true", default=False)
    except ValueError:
        pass

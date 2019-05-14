# pylint doesn't understand pytest fixtures
# pylint: disable=unused-argument


def test_build_dags(create_airflow_dags):
    '''This test generates Airflow DAGs for several pipelines in examples/toys and writes those DAGs
    to $AIRFLOW_HOME/dags.

    By invoking DagBag() below, an Airflow DAG refresh is triggered. If there are any failures in
    DAG parsing, DagBag() will add an entry to its import_errors property.

    By exercising this path, we ensure that our codegen continues to generate valid Airflow DAGs,
    and that Airflow is able to successfully parse our DAGs.
    '''

    # This forces Airflow to refresh DAGs; see https://stackoverflow.com/a/50356956/11295366
    from airflow.models import DagBag

    # If Airflow hits an import error, it will add an entry to this dict.
    assert not DagBag().import_errors

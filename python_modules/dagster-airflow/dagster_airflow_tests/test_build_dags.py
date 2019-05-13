import os
import subprocess


def test_build_dags():
    '''This test generates Airflow DAGs for several pipelines in examples/toys and writes those DAGs
    to $AIRFLOW_HOME/dags.

    By invoking DagBag() below, an Airflow DAG refresh is triggered. If there are any failures in
    DAG parsing, DagBag() will add an entry to its import_errors property.

    By exercising this path, we ensure that our codegen continues to generate valid Airflow DAGs,
    and that Airflow is able to successfully parse our DAGs.
    '''

    path = os.path.dirname(os.path.realpath(__file__))
    create_airflow_dags_script_path = os.path.join(path, '..', 'scripts/create_airflow_dags.sh')

    p = subprocess.Popen(
        create_airflow_dags_script_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = p.communicate()

    print(stdout)
    print(stderr)

    assert p.returncode == 0

    # This forces Airflow to refresh DAGs; see https://stackoverflow.com/a/50356956/11295366
    from airflow.models import DagBag

    # If Airflow hits an import error, it will add an entry to this dict
    assert not DagBag().import_errors

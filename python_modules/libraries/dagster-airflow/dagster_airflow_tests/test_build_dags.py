# pylint doesn't understand pytest fixtures
# pylint: disable=unused-argument

from click.testing import CliRunner
from dagster_airflow.cli import scaffold


def test_build_dags(clean_airflow_home):
    '''This test generates Airflow DAGs for several pipelines in examples/toys and writes those DAGs
    to $AIRFLOW_HOME/dags.

    By invoking DagBag() below, an Airflow DAG refresh is triggered. If there are any failures in
    DAG parsing, DagBag() will add an entry to its import_errors property.

    By exercising this path, we ensure that our codegen continues to generate valid Airflow DAGs,
    and that Airflow is able to successfully parse our DAGs.
    '''
    runner = CliRunner()

    cli_args_to_test = [
        ['--module-name', 'dagster_examples.toys.log_spew', '--pipeline-name', 'log_spew'],
        ['--module-name', 'dagster_examples.toys.many_events', '--pipeline-name', 'many_events'],
        [
            '--module-name',
            'dagster_examples.toys.error_monster',
            '--pipeline-name',
            'error_monster',
            '--preset',
            'passing',
        ],
        [
            '--module-name',
            'dagster_examples.toys.resources',
            '--pipeline-name',
            'resource_pipeline',
        ],
        ['--module-name', 'dagster_examples.toys.sleepy', '--pipeline-name', 'sleepy_pipeline'],
    ]

    for args in cli_args_to_test:
        runner.invoke(scaffold, args)

    # This forces Airflow to refresh DAGs; see https://stackoverflow.com/a/50356956/11295366
    from airflow.models import DagBag

    dag_bag = DagBag()

    # If Airflow hits an import error, it will add an entry to this dict.
    assert not dag_bag.import_errors

    assert args[-1] in dag_bag.dags

from dagster_examples.toys.log_spew import log_spew
from dagster_examples.toys.many_events import many_events
from dagster_pandas.examples.pandas_hello_world.pipeline import pandas_hello_world

from dagster import RepositoryDefinition


def define_repo():
    return RepositoryDefinition(
        name='experimental_repository', pipeline_defs=[log_spew, many_events, pandas_hello_world]
    )

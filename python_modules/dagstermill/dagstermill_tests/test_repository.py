from dagstermill.examples.repository import define_example_repository

from dagster import RepositoryDefinition


def test_dagstermill_repo():
    assert isinstance(define_example_repository(), RepositoryDefinition)

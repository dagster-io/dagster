from dagster import RepositoryDefinition

from dagstermill.examples.repository import define_example_repository


def test_dagstermill_repo():
    assert isinstance(define_example_repository(), RepositoryDefinition)

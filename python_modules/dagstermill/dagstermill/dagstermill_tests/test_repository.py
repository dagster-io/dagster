from dagster import RepositoryDefinition
from .repository import define_example_repository


def test_dagstermill_repo():
    assert isinstance(define_example_repository(), RepositoryDefinition)
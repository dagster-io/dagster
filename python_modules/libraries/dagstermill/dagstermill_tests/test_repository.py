from dagster import RepositoryDefinition
from dagstermill.examples.repository import notebook_repo


def test_dagstermill_repo():
    assert isinstance(notebook_repo, RepositoryDefinition)

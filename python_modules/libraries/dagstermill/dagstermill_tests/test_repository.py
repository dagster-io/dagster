from dagstermill.examples.repository import notebook_repo

from dagster import RepositoryDefinition


def test_dagstermill_repo():
    assert isinstance(notebook_repo, RepositoryDefinition)

from dagstermill.examples.repository import notebook_repo, notebook_assets_repo

from dagster import RepositoryDefinition


def test_dagstermill_repo():
    assert isinstance(notebook_repo, RepositoryDefinition)


def test_dagstermill_assets_repo():
    assert isinstance(notebook_assets_repo, RepositoryDefinition)
import sys

from dagster.api.list_repositories import sync_list_repositories
from dagster.cli.api import LoadableRepositorySymbol
from dagster.utils import file_relative_path


def test_sync_list_python_file():
    python_file = file_relative_path(__file__, 'api_tests_repo.py')
    loadable_repo_symbols = sync_list_repositories(
        sys.executable, python_file=python_file, module_name=None
    ).repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'bar_repo'
    assert symbol.attribute == 'bar_repo'


def test_sync_list_python_file_multi_repo():
    python_file = file_relative_path(__file__, 'multiple_repos.py')
    loadable_repo_symbols = sync_list_repositories(
        sys.executable, python_file=python_file, module_name=None
    ).repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 2
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)
    assert isinstance(loadable_repo_symbols[1], LoadableRepositorySymbol)

    by_symbol = {lrs.attribute: lrs for lrs in loadable_repo_symbols}

    assert by_symbol['repo_one_symbol'].repository_name == 'repo_one'
    assert by_symbol['repo_two'].repository_name == 'repo_two'


def test_sync_list_python_module():
    loadable_repo_symbols = sync_list_repositories(
        sys.executable, python_file=None, module_name='dagster.utils.test.hello_world_repository',
    ).repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'hello_world_repository'
    assert symbol.attribute == 'hello_world_repository'

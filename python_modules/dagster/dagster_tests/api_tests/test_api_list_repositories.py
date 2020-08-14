import sys

import pytest

from dagster import seven
from dagster.api.list_repositories import (
    sync_list_repositories,
    sync_list_repositories_ephemeral_grpc,
    sync_list_repositories_grpc,
)
from dagster.core.code_pointer import FileCodePointer, ModuleCodePointer
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.grpc.types import LoadableRepositorySymbol
from dagster.utils import file_relative_path


def test_sync_list_python_file():
    python_file = file_relative_path(__file__, 'api_tests_repo.py')
    loadable_repo_symbols = sync_list_repositories(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute=None,
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
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute=None,
    ).repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 2
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)
    assert isinstance(loadable_repo_symbols[1], LoadableRepositorySymbol)

    by_symbol = {lrs.attribute: lrs for lrs in loadable_repo_symbols}

    assert by_symbol['repo_one_symbol'].repository_name == 'repo_one'
    assert by_symbol['repo_two'].repository_name == 'repo_two'


def test_sync_list_python_file_attribute_multi_repo():
    python_file = file_relative_path(__file__, 'multiple_repos.py')
    loadable_repo_symbols = sync_list_repositories(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute='repo_one_symbol',
    ).repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    assert loadable_repo_symbols[0].repository_name == 'repo_one'
    assert loadable_repo_symbols[0].attribute == 'repo_one_symbol'


def test_sync_list_python_module():
    loadable_repo_symbols = sync_list_repositories(
        sys.executable,
        python_file=None,
        module_name='dagster.utils.test.hello_world_repository',
        working_directory=None,
        attribute=None,
    ).repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'hello_world_repository'
    assert symbol.attribute == 'hello_world_repository'


def test_sync_list_python_module_attribute():
    loadable_repo_symbols = sync_list_repositories(
        sys.executable,
        python_file=None,
        module_name='dagster.utils.test.hello_world_repository',
        working_directory=None,
        attribute='hello_world_repository',
    ).repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'hello_world_repository'
    assert symbol.attribute == 'hello_world_repository'


def test_sync_list_python_file_grpc():
    python_file = file_relative_path(__file__, 'api_tests_repo.py')
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute=None,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'bar_repo'
    assert symbol.attribute == 'bar_repo'

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict
    assert 'bar_repo' in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict['bar_repo'], FileCodePointer)
    assert repository_code_pointer_dict['bar_repo'].python_file.endswith("api_tests_repo.py")
    assert repository_code_pointer_dict['bar_repo'].fn_name == 'bar_repo'


def test_sync_list_python_file_multi_repo_grpc():
    python_file = file_relative_path(__file__, 'multiple_repos.py')
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute=None,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 2
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)
    assert isinstance(loadable_repo_symbols[1], LoadableRepositorySymbol)

    by_symbol = {lrs.attribute: lrs for lrs in loadable_repo_symbols}

    assert by_symbol['repo_one_symbol'].repository_name == 'repo_one'
    assert by_symbol['repo_two'].repository_name == 'repo_two'

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict
    assert 'repo_one' in repository_code_pointer_dict
    assert 'repo_two' in repository_code_pointer_dict

    assert isinstance(repository_code_pointer_dict['repo_one'], FileCodePointer)
    assert repository_code_pointer_dict['repo_one'].python_file == python_file
    assert repository_code_pointer_dict['repo_one'].fn_name == 'repo_one_symbol'

    assert isinstance(repository_code_pointer_dict['repo_two'], FileCodePointer)
    assert repository_code_pointer_dict['repo_two'].fn_name == 'repo_two'


def test_sync_list_python_file_attribute_multi_repo_grpc():
    python_file = file_relative_path(__file__, 'multiple_repos.py')
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute='repo_one_symbol',
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'repo_one'
    assert symbol.attribute == 'repo_one_symbol'

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict
    assert 'repo_one' in repository_code_pointer_dict

    assert isinstance(repository_code_pointer_dict['repo_one'], FileCodePointer)
    assert repository_code_pointer_dict['repo_one'].python_file == python_file
    assert repository_code_pointer_dict['repo_one'].fn_name == 'repo_one_symbol'


def test_sync_list_python_module_grpc():
    module_name = 'dagster.utils.test.hello_world_repository'
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=None,
        module_name=module_name,
        working_directory=None,
        attribute=None,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'hello_world_repository'
    assert symbol.attribute == 'hello_world_repository'

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict

    assert 'hello_world_repository' in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict['hello_world_repository'], ModuleCodePointer)
    assert repository_code_pointer_dict['hello_world_repository'].module == module_name
    assert (
        repository_code_pointer_dict['hello_world_repository'].fn_name == 'hello_world_repository'
    )


def test_sync_list_python_module_attribute_grpc():
    module_name = 'dagster.utils.test.hello_world_repository'
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=None,
        module_name=module_name,
        working_directory=None,
        attribute='hello_world_repository',
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'hello_world_repository'
    assert symbol.attribute == 'hello_world_repository'

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict

    assert 'hello_world_repository' in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict['hello_world_repository'], ModuleCodePointer)
    assert repository_code_pointer_dict['hello_world_repository'].module == module_name
    assert (
        repository_code_pointer_dict['hello_world_repository'].fn_name == 'hello_world_repository'
    )


@pytest.mark.skipif(seven.IS_WINDOWS, reason='Depends on Docker, so skip running in Windows')
def test_sync_list_container_grpc(docker_grpc_client):
    response = sync_list_repositories_grpc(docker_grpc_client)

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == 'bar_repo'
    assert symbol.attribute == 'bar_repo'

    executable_path = response.executable_path
    assert executable_path

    repository_code_pointer_dict = response.repository_code_pointer_dict
    assert 'bar_repo' in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict['bar_repo'], FileCodePointer)
    assert repository_code_pointer_dict['bar_repo'].python_file.endswith("repo.py")
    assert repository_code_pointer_dict['bar_repo'].fn_name == 'bar_repo'


def test_sync_list_python_file_with_error():
    python_file = file_relative_path(__file__, 'error_on_load_repo.py')
    with pytest.raises(DagsterUserCodeProcessError) as e:
        sync_list_repositories(
            sys.executable,
            python_file=python_file,
            module_name=None,
            working_directory=None,
            attribute=None,
        )

    assert e.value.args[0].startswith('(ValueError) - ValueError: User did something bad')
    assert e.value.args[0].endswith("raise ValueError('User did something bad')\n")


def test_sync_list_python_file_grpc_with_error():
    python_file = file_relative_path(__file__, 'error_on_load_repo.py')
    with pytest.raises(DagsterUserCodeProcessError) as e:
        sync_list_repositories_ephemeral_grpc(
            sys.executable,
            python_file=python_file,
            module_name=None,
            working_directory=None,
            attribute=None,
        )

    assert e.value.args[0].startswith('(ValueError) - ValueError: User did something bad')
    assert e.value.args[0].endswith("raise ValueError('User did something bad')\n")

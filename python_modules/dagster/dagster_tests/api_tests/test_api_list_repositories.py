import asyncio
import sys

import dagster as dg
import pytest
from dagster._api.list_repositories import (
    gen_list_repositories_ephemeral_grpc,
    sync_list_repositories_ephemeral_grpc,
)
from dagster._core.code_pointer import FileCodePointer, ModuleCodePointer, PackageCodePointer
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._grpc.types import LoadableRepositorySymbol


@pytest.mark.asyncio
async def test_list_repositories_python_file_grpc():
    python_file = dg.file_relative_path(__file__, "api_tests_repo.py")
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute="bar_repo",
        package_name=None,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == "bar_repo"
    assert symbol.attribute == "bar_repo"

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict
    assert "bar_repo" in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict["bar_repo"], FileCodePointer)
    assert repository_code_pointer_dict["bar_repo"].python_file.endswith("api_tests_repo.py")
    assert repository_code_pointer_dict["bar_repo"].fn_name == "bar_repo"

    async_response = await gen_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute="bar_repo",
        package_name=None,
    )
    assert async_response == response


def test_sync_list_python_file_multi_repo_grpc():
    python_file = dg.file_relative_path(__file__, "multiple_repos.py")
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute=None,
        package_name=None,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 2
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)
    assert isinstance(loadable_repo_symbols[1], LoadableRepositorySymbol)

    by_symbol = {lrs.attribute: lrs for lrs in loadable_repo_symbols}

    assert by_symbol["repo_one_symbol"].repository_name == "repo_one"
    assert by_symbol["repo_two"].repository_name == "repo_two"

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict
    assert "repo_one" in repository_code_pointer_dict
    assert "repo_two" in repository_code_pointer_dict

    assert isinstance(repository_code_pointer_dict["repo_one"], FileCodePointer)
    assert repository_code_pointer_dict["repo_one"].python_file == python_file
    assert repository_code_pointer_dict["repo_one"].fn_name == "repo_one_symbol"

    assert isinstance(repository_code_pointer_dict["repo_two"], FileCodePointer)
    assert repository_code_pointer_dict["repo_two"].fn_name == "repo_two"


def test_sync_list_python_file_attribute_multi_repo_grpc():
    python_file = dg.file_relative_path(__file__, "multiple_repos.py")
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute="repo_one_symbol",
        package_name=None,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == "repo_one"
    assert symbol.attribute == "repo_one_symbol"

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict
    assert "repo_one" in repository_code_pointer_dict

    assert isinstance(repository_code_pointer_dict["repo_one"], FileCodePointer)
    assert repository_code_pointer_dict["repo_one"].python_file == python_file
    assert repository_code_pointer_dict["repo_one"].fn_name == "repo_one_symbol"


def test_sync_list_python_module_grpc():
    module_name = "dagster.utils.test.hello_world_repository"
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=None,
        module_name=module_name,
        working_directory=None,
        attribute=None,
        package_name=None,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == "hello_world_repository"
    assert symbol.attribute == "hello_world_repository"

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict

    assert "hello_world_repository" in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict["hello_world_repository"], ModuleCodePointer)
    assert repository_code_pointer_dict["hello_world_repository"].module == module_name
    assert (
        repository_code_pointer_dict["hello_world_repository"].fn_name == "hello_world_repository"
    )


def test_sync_list_python_module_attribute_grpc():
    module_name = "dagster.utils.test.hello_world_repository"
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=None,
        module_name=module_name,
        working_directory=None,
        attribute="hello_world_repository",
        package_name=None,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == "hello_world_repository"
    assert symbol.attribute == "hello_world_repository"

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict

    assert "hello_world_repository" in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict["hello_world_repository"], ModuleCodePointer)
    assert repository_code_pointer_dict["hello_world_repository"].module == module_name
    assert (
        repository_code_pointer_dict["hello_world_repository"].fn_name == "hello_world_repository"
    )


def test_sync_list_python_package_attribute_grpc():
    package_name = "dagster.utils.test.hello_world_repository"
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=None,
        module_name=None,
        working_directory=None,
        attribute="hello_world_repository",
        package_name=package_name,
    )

    loadable_repo_symbols = response.repository_symbols

    assert isinstance(loadable_repo_symbols, list)
    assert len(loadable_repo_symbols) == 1
    assert isinstance(loadable_repo_symbols[0], LoadableRepositorySymbol)

    symbol = loadable_repo_symbols[0]

    assert symbol.repository_name == "hello_world_repository"
    assert symbol.attribute == "hello_world_repository"

    executable_path = response.executable_path
    assert executable_path == sys.executable

    repository_code_pointer_dict = response.repository_code_pointer_dict

    assert "hello_world_repository" in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict["hello_world_repository"], PackageCodePointer)
    assert repository_code_pointer_dict["hello_world_repository"].module == package_name
    assert (
        repository_code_pointer_dict["hello_world_repository"].attribute == "hello_world_repository"
    )


def test_sync_list_python_file_grpc_with_error():
    python_file = dg.file_relative_path(__file__, "error_on_load_repo.py")
    with pytest.raises(DagsterUserCodeProcessError) as e:
        sync_list_repositories_ephemeral_grpc(
            sys.executable,
            python_file=python_file,
            module_name=None,
            working_directory=None,
            attribute=None,
            package_name=None,
        )

    assert 'raise ValueError("User did something bad")' in str(e)

    with pytest.raises(DagsterUserCodeProcessError) as e:
        asyncio.run(
            gen_list_repositories_ephemeral_grpc(
                sys.executable,
                python_file=python_file,
                module_name=None,
                working_directory=None,
                attribute=None,
                package_name=None,
            )
        )

    assert 'raise ValueError("User did something bad")' in str(e)

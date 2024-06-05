import sys

from dagster._api.list_repositories import sync_list_repositories_ephemeral_grpc
from dagster._core.code_pointer import FileCodePointer, ModuleCodePointer, PackageCodePointer
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._utils import file_relative_path


def test_loadable_target_origin_context_python_file_grpc():
    python_file = file_relative_path(__file__, "loadable_target_origin_test_repo.py")
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=python_file,
        module_name=None,
        working_directory=None,
        attribute="defs",
        package_name=None,
    )

    repository_code_pointer_dict = response.repository_code_pointer_dict
    assert SINGLETON_REPOSITORY_NAME in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict[SINGLETON_REPOSITORY_NAME], FileCodePointer)


def test_loadable_target_origin_context_python_module_grpc():
    module_name = "dagster_tests.general_tests.loadable_target_origin_context.loadable_target_origin_test_repo"
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=None,
        module_name=module_name,
        working_directory=None,
        attribute=None,
        package_name=None,
    )

    repository_code_pointer_dict = response.repository_code_pointer_dict

    assert SINGLETON_REPOSITORY_NAME in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict[SINGLETON_REPOSITORY_NAME], ModuleCodePointer)


def test_loadable_target_origin_context_python_package_attribute_grpc():
    package_name = "dagster_tests.general_tests.loadable_target_origin_context.loadable_target_origin_test_repo"
    response = sync_list_repositories_ephemeral_grpc(
        sys.executable,
        python_file=None,
        module_name=None,
        working_directory=None,
        attribute="defs",
        package_name=package_name,
    )

    repository_code_pointer_dict = response.repository_code_pointer_dict

    assert SINGLETON_REPOSITORY_NAME in repository_code_pointer_dict
    assert isinstance(repository_code_pointer_dict[SINGLETON_REPOSITORY_NAME], PackageCodePointer)

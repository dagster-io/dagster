import click
import pytest
from click.testing import CliRunner

from dagster._cli.workspace.cli_target import (
    get_external_repository_from_kwargs,
    repository_target_argument,
)
from dagster._core.host_representation import ExternalRepository
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path


def load_repository_via_cli_runner(cli_args, repo_assert_fn=None):
    @click.command(name="test_repository_command")
    @repository_target_argument
    def command(**kwargs):
        with get_external_repository_from_kwargs(
            DagsterInstance.get(),
            version="",
            kwargs=kwargs,
        ) as external_repo:
            if repo_assert_fn:
                repo_assert_fn(external_repo)

    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(command, cli_args)

    return result


def successfully_load_repository_via_cli(cli_args, repo_assert_fn=None):
    def wrapped_repo_assert(external_repo):
        assert isinstance(external_repo, ExternalRepository)
        if repo_assert_fn:
            repo_assert_fn(external_repo)

    result = load_repository_via_cli_runner(cli_args, wrapped_repo_assert)
    assert result.exit_code == 0


PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE = file_relative_path(
    __file__, "hello_world_in_file/python_file_with_named_location_workspace.yaml"
)


@pytest.mark.parametrize(
    "cli_args",
    (
        # auto infer location and repo
        ["-w", PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE],
        # auto infer location
        ["-w", PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, "-r", "hello_world_repository"],
        # auto infer repository
        ["-w", PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, "-l", "hello_world_location"],
        [
            "-w",
            PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE,
            "-l",
            "hello_world_location",
            "-r",
            "hello_world_repository",
        ],
    ),
)
def test_valid_repository_target_combos_with_single_repo_single_location(cli_args):
    successfully_load_repository_via_cli(cli_args, lambda er: er.name == "hello_world_repository")


def test_repository_target_argument_one_repo_and_specified_wrong():
    result = load_repository_via_cli_runner(
        ["-w", PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, "-r", "not_present"]
    )

    assert result.exit_code == 2

    assert (
        """Repository "not_present" not found in location "hello_world_location". """
        """Found ['hello_world_repository'] instead.""" in result.stdout
    )


def test_repository_target_argument_one_location_and_specified_wrong():
    result = load_repository_via_cli_runner(
        ["-w", PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, "-l", "location_not_present"]
    )

    assert result.exit_code == 2

    assert (
        """Location "location_not_present" not found in workspace. """
        """Found ['hello_world_location'] instead."""
    ) in result.stdout


MULTI_LOCATION_WORKSPACE = file_relative_path(__file__, "multi_location/multi_location.yaml")


def test_valid_multi_location_from_file():
    def the_assert(external_repository):
        assert external_repository.name == "hello_world_repository"
        assert external_repository.handle.location_name == "loaded_from_file"

    successfully_load_repository_via_cli(
        ["-w", MULTI_LOCATION_WORKSPACE, "-l", "loaded_from_file"], the_assert
    )


def test_valid_multi_location_from_module():
    def the_assert(external_repository):
        assert external_repository.name == "hello_world_repository"
        assert external_repository.handle.location_name == "loaded_from_module"

    successfully_load_repository_via_cli(
        ["-w", MULTI_LOCATION_WORKSPACE, "-l", "loaded_from_module"], the_assert
    )


def test_missing_location_name_multi_location():
    result = load_repository_via_cli_runner(["-w", MULTI_LOCATION_WORKSPACE])

    assert result.exit_code == 2

    assert (
        """Must provide --location as there are multiple locations available. """
        """Options are: ['loaded_from_file', 'loaded_from_module', 'loaded_from_package']"""
    ) in result.stdout


SINGLE_LOCATION_MULTI_REPO_WORKSPACE = file_relative_path(__file__, "multi_repo/multi_repo.yaml")


def test_valid_multi_repo():
    def the_assert(external_repository):
        assert external_repository.name == "repo_one"

    successfully_load_repository_via_cli(
        ["-w", SINGLE_LOCATION_MULTI_REPO_WORKSPACE, "-r", "repo_one"], the_assert
    )

    def the_assert_two(external_repository):
        assert external_repository.name == "repo_two"

    successfully_load_repository_via_cli(
        ["-w", SINGLE_LOCATION_MULTI_REPO_WORKSPACE, "-r", "repo_two"], the_assert_two
    )


def test_missing_repo_name_in_multi_repo_location():
    result = load_repository_via_cli_runner(["-w", SINGLE_LOCATION_MULTI_REPO_WORKSPACE])

    assert result.exit_code == 2

    assert (
        """Must provide --repository as there is more than one repository in """
        """multi_repo. Options are: ['repo_one', 'repo_two']."""
    ) in result.stdout


def test_pending_repo():
    pending_location = file_relative_path(__file__, "pending_repo/pending_repo.yaml")

    def the_assert(external_repository):
        assert external_repository.name == "pending_repo"

    successfully_load_repository_via_cli(["-w", pending_location, "-r", "pending_repo"], the_assert)


def test_local_directory_module():
    cli_args = [
        "-w",
        file_relative_path(__file__, "hello_world_in_module/local_directory_module_workspace.yaml"),
    ]
    result = load_repository_via_cli_runner(cli_args)

    # repository loading should fail even though pytest is being run from the current directory
    # because we removed module resolution from the working directory
    assert result.exit_code != 0


@pytest.mark.parametrize(
    "cli_args",
    (
        # load workspace with explicit working directory
        [
            "-w",
            file_relative_path(
                __file__, "hello_world_file_in_directory/working_directory_workspace.yaml"
            ),
        ],
        # load workspace with default working directory
        [
            "-w",
            file_relative_path(
                __file__, "hello_world_file_in_directory/default_working_dir_workspace.yaml"
            ),
        ],
        # load workspace with multiple working directory file targets
        [
            "-w",
            file_relative_path(__file__, "multi_file_target_workspace/workspace.yaml"),
            "-l",
            "one",
        ],
    ),
)
def test_local_directory_file(cli_args):
    successfully_load_repository_via_cli(cli_args)

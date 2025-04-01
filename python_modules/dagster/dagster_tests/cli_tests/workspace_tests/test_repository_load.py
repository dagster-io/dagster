import click
import pytest
from click.testing import CliRunner
from dagster._cli.utils import assert_no_remaining_opts
from dagster._cli.workspace.cli_target import (
    RepositoryOpts,
    WorkspaceOpts,
    get_repository_from_cli_opts,
    get_workspace_from_cli_opts,
    repository_options,
    workspace_options,
)
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import RemoteRepository
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._utils import file_relative_path


def load_repository_via_cli_runner(cli_args, repo_assert_fn=None):
    @click.command(name="test_repository_command")
    @workspace_options
    @repository_options
    def command(**opts: object):
        workspace_opts = WorkspaceOpts.extract_from_cli_options(opts)
        repository_opts = RepositoryOpts.extract_from_cli_options(opts)
        assert_no_remaining_opts(opts)
        with get_repository_from_cli_opts(
            DagsterInstance.get(),
            version="",
            workspace_opts=workspace_opts,
            repository_opts=repository_opts,
        ) as repo:
            if repo_assert_fn:
                repo_assert_fn(repo)

    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(command, cli_args)

    return result


def load_workspace_via_cli_runner(cli_args, workspace_assert_fn=None):
    @click.command(name="test_workspace_command")
    @workspace_options
    def command(**opts: object):
        workspace_opts = WorkspaceOpts.extract_from_cli_options(opts)
        assert_no_remaining_opts(opts)
        with get_workspace_from_cli_opts(
            DagsterInstance.get(),
            version="",
            workspace_opts=workspace_opts,
        ) as workspace:
            assert isinstance(workspace, WorkspaceRequestContext)
            if workspace_assert_fn:
                workspace_assert_fn(workspace)

    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(command, cli_args)

    return result


def successfully_load_repository_via_cli(cli_args, repo_assert_fn=None):
    def wrapped_repo_assert(remote_repo):
        assert isinstance(remote_repo, RemoteRepository)
        if repo_assert_fn:
            repo_assert_fn(remote_repo)

    result = load_repository_via_cli_runner(cli_args, wrapped_repo_assert)
    assert result.exit_code == 0
    return result


PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE = file_relative_path(
    __file__, "hello_world_in_file/python_file_with_named_location_workspace.yaml"
)


def test_multiple_module_load():
    MODULE_ONE = "dagster._utils.test.hello_world_repository"
    MODULE_TWO = "dagster._utils.test.hello_world_defs"

    executed = {}

    def wrapped_workspace_assert(workspace_context):
        assert isinstance(workspace_context, WorkspaceRequestContext)
        assert workspace_context.get_code_location(MODULE_ONE)
        assert workspace_context.get_code_location(MODULE_TWO)
        executed["yes"] = True

    result = load_workspace_via_cli_runner(
        ["-m", MODULE_ONE, "-m", MODULE_TWO],
        wrapped_workspace_assert,
    )

    assert executed["yes"]
    assert result.exit_code == 0


def test_multiple_module_load_with_attribute():
    MODULE_ONE = "dagster._utils.test.hello_world_repository"
    MODULE_TWO = "dagster._utils.test.hello_world_defs"

    result = load_workspace_via_cli_runner(
        ["-m", MODULE_ONE, "-m", MODULE_TWO, "-a", "defs"],  # does not accept attribute
    )

    assert "If you are specifying multiple modules you cannot specify an attribute" in result.stdout
    assert result.exit_code != 0


def test_multiple_file_load():
    FILE_ONE = file_relative_path(__file__, "hello_world_in_file/hello_world_repository.py")
    FILE_TWO = file_relative_path(__file__, "definitions_test_cases/defs_file.py")

    executed = {}

    def wrapped_workspace_assert(workspace_context):
        assert isinstance(workspace_context, WorkspaceRequestContext)
        assert workspace_context.get_code_location("hello_world_repository.py")
        assert workspace_context.get_code_location("defs_file.py")
        executed["yes"] = True

    result = load_workspace_via_cli_runner(
        ["-f", FILE_ONE, "-f", FILE_TWO],
        wrapped_workspace_assert,
    )

    assert result.exit_code == 0
    assert executed["yes"]


def test_multiple_file_load_with_attribute():
    FILE_ONE = file_relative_path(__file__, "hello_world_in_file/hello_world_repository.py")
    FILE_TWO = file_relative_path(__file__, "definitions_test_cases/defs_file.py")

    result = load_workspace_via_cli_runner(
        ["-f", FILE_ONE, "-f", FILE_TWO, "-a", "defs"],
    )

    assert "If you are specifying multiple files you cannot specify an attribute" in result.stdout
    assert result.exit_code != 0


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
    def the_assert(remote_repository):
        assert remote_repository.name == "hello_world_repository"
        assert remote_repository.handle.location_name == "loaded_from_file"

    successfully_load_repository_via_cli(
        ["-w", MULTI_LOCATION_WORKSPACE, "-l", "loaded_from_file"], the_assert
    )


def test_valid_multi_location_from_module():
    def the_assert(remote_repository):
        assert remote_repository.name == "hello_world_repository"
        assert remote_repository.handle.location_name == "loaded_from_module"

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
    def the_assert(remote_repository):
        assert remote_repository.name == "repo_one"

    successfully_load_repository_via_cli(
        ["-w", SINGLE_LOCATION_MULTI_REPO_WORKSPACE, "-r", "repo_one"], the_assert
    )

    def the_assert_two(remote_repository):
        assert remote_repository.name == "repo_two"

    successfully_load_repository_via_cli(
        ["-w", SINGLE_LOCATION_MULTI_REPO_WORKSPACE, "-r", "repo_two"], the_assert_two
    )


def test_missing_repo_name_in_multi_repo_code_location():
    result = load_repository_via_cli_runner(["-w", SINGLE_LOCATION_MULTI_REPO_WORKSPACE])

    assert result.exit_code == 2

    assert (
        """Must provide --repository as there is more than one repository in """
        """multi_repo. Options are: ['repo_one', 'repo_two']."""
    ) in result.stdout


def test_pending_repo():
    pending_location = file_relative_path(__file__, "pending_repo/pending_repo.yaml")

    def the_assert(remote_repository):
        assert remote_repository.name == "pending_repo"

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


def test_dagster_definitions():
    cli_args = ["-f", file_relative_path(__file__, "definitions_test_cases/defs_file.py")]

    executed = {}

    def the_assert(remote_repo: RemoteRepository):
        assert remote_repo.name == "__repository__"
        assert len(remote_repo.get_asset_node_snaps()) == 1
        executed["yes"] = True

    assert successfully_load_repository_via_cli(cli_args, the_assert)

    assert executed["yes"]

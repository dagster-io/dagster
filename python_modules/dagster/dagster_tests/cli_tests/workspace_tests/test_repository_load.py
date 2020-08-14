import os
import re
from contextlib import contextmanager

import click
import pytest
from click.testing import CliRunner

from dagster.cli.workspace.cli_target import (
    get_external_repository_from_kwargs,
    repository_target_argument,
)
from dagster.core.host_representation import ExternalRepository
from dagster.core.instance import DagsterInstance
from dagster.utils import file_relative_path


def load_repository_via_cli_runner(cli_args):
    capture_result = {'external_repo': None}

    @click.command(name='test_repository_command')
    @repository_target_argument
    def command(**kwargs):
        capture_result['external_repo'] = get_external_repository_from_kwargs(
            kwargs, DagsterInstance.ephemeral()
        )

    runner = CliRunner()
    result = runner.invoke(command, cli_args)

    external_repo = capture_result['external_repo']
    return result, external_repo


def successfully_load_repository_via_cli(cli_args):
    result, external_repository = load_repository_via_cli_runner(cli_args)
    assert result.exit_code == 0
    assert isinstance(external_repository, ExternalRepository)
    return external_repository


PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE = file_relative_path(
    __file__, 'hello_world_in_file/python_file_with_named_location_workspace.yaml'
)

LEGACY_REPOSITORY = file_relative_path(__file__, 'hello_world_in_file/legacy_repository.yaml')


@pytest.mark.parametrize(
    'cli_args',
    (
        # auto infer location and repo
        ['-w', PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE],
        # auto infer location
        ['-w', PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, '-r', 'hello_world_repository'],
        # auto infer repository
        ['-w', PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, '-l', 'hello_world_location'],
        [
            '-w',
            PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE,
            '-l',
            'hello_world_location',
            '-r',
            'hello_world_repository',
        ],
        # legacy repository
        ['-w', LEGACY_REPOSITORY],
        # legacy repository with specified name
        ['-w', LEGACY_REPOSITORY, '-r', 'hello_world_repository'],
    ),
)
def test_valid_repository_target_combos_with_single_repo_single_location(cli_args):
    if cli_args[1] == LEGACY_REPOSITORY:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            external_repository = successfully_load_repository_via_cli(cli_args)
    else:
        external_repository = successfully_load_repository_via_cli(cli_args)
    assert isinstance(external_repository, ExternalRepository)
    assert external_repository.name == 'hello_world_repository'


def test_repository_target_argument_one_repo_and_specified_wrong():
    result, _ = load_repository_via_cli_runner(
        ['-w', PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, '-r', 'not_present']
    )

    assert result.exit_code == 2

    assert (
        '''Repository "not_present" not found in location "hello_world_location". '''
        '''Found ['hello_world_repository'] instead.''' in result.stdout
    )


def test_repository_target_argument_one_location_and_specified_wrong():
    result, _ = load_repository_via_cli_runner(
        ['-w', PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, '-l', 'location_not_present']
    )

    assert result.exit_code == 2

    assert (
        '''Location "location_not_present" not found in workspace. '''
        '''Found ['hello_world_location'] instead.'''
    ) in result.stdout


MULTI_LOCATION_WORKSPACE = file_relative_path(__file__, 'multi_location/multi_location.yaml')


def test_valid_multi_location_from_file():
    external_repository = successfully_load_repository_via_cli(
        ['-w', MULTI_LOCATION_WORKSPACE, '-l', 'loaded_from_file']
    )
    assert external_repository.name == 'hello_world_repository'
    assert external_repository.handle.repository_location_handle.location_name == 'loaded_from_file'


def test_valid_multi_location_from_module():
    external_repository = successfully_load_repository_via_cli(
        ['-w', MULTI_LOCATION_WORKSPACE, '-l', 'loaded_from_module']
    )
    assert external_repository.name == 'hello_world_repository'
    assert (
        external_repository.handle.repository_location_handle.location_name == 'loaded_from_module'
    )


def test_missing_location_name_multi_location():
    result, _ = load_repository_via_cli_runner(['-w', MULTI_LOCATION_WORKSPACE])

    assert result.exit_code == 2

    assert (
        '''Must provide --location as there are more than one locations available. '''
        '''Options are: ['loaded_from_file', 'loaded_from_module']'''
    ) in result.stdout


SINGLE_LOCATION_MULTI_REPO_WORKSPACE = file_relative_path(__file__, 'multi_repo/multi_repo.yaml')


def test_valid_multi_repo():
    assert (
        successfully_load_repository_via_cli(
            ['-w', SINGLE_LOCATION_MULTI_REPO_WORKSPACE, '-r', 'repo_one']
        ).name
        == 'repo_one'
    )
    assert (
        successfully_load_repository_via_cli(
            ['-w', SINGLE_LOCATION_MULTI_REPO_WORKSPACE, '-r', 'repo_two']
        ).name
        == 'repo_two'
    )


def test_missing_repo_name_in_multi_repo_location():
    result, _ = load_repository_via_cli_runner(['-w', SINGLE_LOCATION_MULTI_REPO_WORKSPACE])

    assert result.exit_code == 2

    assert (
        '''Must provide --repository as there is more than one repository in '''
        '''multi_repo. Options are: ['repo_one', 'repo_two'].'''
    ) in result.stdout


@contextmanager
def new_cwd(path):
    old = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)


def test_legacy_repository_yaml_autoload():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        with new_cwd(file_relative_path(__file__, 'legacy_repository_yaml')):
            assert successfully_load_repository_via_cli([]).name == 'hello_world_repository'


def test_legacy_repository_yaml_dash_y():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You have used -y or --repository-yaml to load a workspace. This is deprecated and '
            'will be eliminated in 0.9.0.'
        ),
    ):
        with new_cwd(file_relative_path(__file__, 'legacy_repository_yaml')):
            assert (
                successfully_load_repository_via_cli(['-y', 'repository.yaml']).name
                == 'hello_world_repository'
            )


def test_legacy_repository_yaml_module_autoload():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        with new_cwd(file_relative_path(__file__, 'legacy_repository_yaml_module')):
            assert successfully_load_repository_via_cli([]).name == 'hello_world_repository'


def test_legacy_repository_module_yaml_dash_y():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You have used -y or --repository-yaml to load a workspace. This is deprecated and '
            'will be eliminated in 0.9.0.'
        ),
    ):
        with new_cwd(file_relative_path(__file__, 'legacy_repository_yaml_module')):
            assert (
                successfully_load_repository_via_cli(['-y', 'repository.yaml']).name
                == 'hello_world_repository'
            )


def test_local_directory_module():
    cli_args = [
        '-w',
        file_relative_path(__file__, 'hello_world_in_module/local_directory_module_workspace.yaml'),
    ]
    result, _ = load_repository_via_cli_runner(cli_args)

    # repository loading should fail even though pytest is being run from the current directory
    # because we removed module resolution from the working directory
    assert result.exit_code != 0


@pytest.mark.parametrize(
    'cli_args',
    (
        # load workspace with explicit working directory
        [
            '-w',
            file_relative_path(
                __file__, 'hello_world_file_in_directory/working_directory_workspace.yaml'
            ),
        ],
        # load workspace with default working directory
        [
            '-w',
            file_relative_path(
                __file__, 'hello_world_file_in_directory/default_working_dir_workspace.yaml'
            ),
        ],
        # load workspace with multiple working directory file targets
        [
            '-w',
            file_relative_path(__file__, 'multi_file_target_workspace/workspace.yaml'),
            '-l',
            'one',
        ],
    ),
)
def test_local_directory_file(cli_args):
    assert successfully_load_repository_via_cli(cli_args)

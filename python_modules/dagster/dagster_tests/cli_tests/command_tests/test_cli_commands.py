from __future__ import print_function

import os
import re
import string

import mock
import pytest
from click import UsageError
from click.testing import CliRunner

from dagster import (
    PartitionSetDefinition,
    ScheduleDefinition,
    check,
    lambda_solid,
    pipeline,
    repository,
    seven,
    solid,
)
from dagster.cli.pipeline import (
    execute_backfill_command,
    execute_execute_command,
    execute_launch_command,
    execute_list_command,
    execute_print_command,
    execute_scaffold_command,
    pipeline_backfill_command,
    pipeline_execute_command,
    pipeline_launch_command,
    pipeline_list_command,
    pipeline_print_command,
    pipeline_scaffold_command,
)
from dagster.cli.run import run_list_command, run_wipe_command
from dagster.cli.schedule import (
    schedule_list_command,
    schedule_logs_command,
    schedule_restart_command,
    schedule_start_command,
    schedule_stop_command,
    schedule_up_command,
    schedule_wipe_command,
)
from dagster.config.field_utils import Shape
from dagster.core.errors import DagsterLaunchFailedError, DagsterUserCodeProcessError
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher import RunLauncher
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.core.test_utils import test_instance
from dagster.grpc.server import GrpcServerProcess
from dagster.grpc.types import LoadableTargetOrigin
from dagster.serdes import ConfigurableClass
from dagster.utils import file_relative_path
from dagster.utils.test import FilesystemTestScheduler


def no_print(_):
    return None


@lambda_solid
def do_something():
    return 1


@lambda_solid
def do_input(x):
    return x


@pipeline(name='foo')
def foo_pipeline():
    do_input(do_something())


def define_foo_pipeline():
    return foo_pipeline


@pipeline(name='baz', description='Not much tbh')
def baz_pipeline():
    do_input()


def define_bar_schedules():
    return {
        'foo_schedule': ScheduleDefinition(
            "foo_schedule", cron_schedule="* * * * *", pipeline_name="test_pipeline", run_config={},
        ),
    }


def define_baz_partitions():
    return {
        'baz_partitions': PartitionSetDefinition(
            name='baz_partitions',
            pipeline_name='baz',
            partition_fn=lambda: string.ascii_lowercase,
            run_config_fn_for_partition=lambda partition: {
                'solids': {'do_input': {'inputs': {'x': {'value': partition.value}}}}
            },
        )
    }


@repository
def bar():
    return {
        'pipelines': {'foo': foo_pipeline, 'baz': baz_pipeline},
        'schedules': define_bar_schedules(),
        'partition_sets': define_baz_partitions(),
    }


@solid
def spew(context):
    context.log.info('HELLO WORLD')


@solid
def fail(context):
    raise Exception('I AM SUPPOSED TO FAIL')


@pipeline
def stdout_pipeline():
    spew()


@pipeline
def stderr_pipeline():
    fail()


def assert_correct_bar_repository_output(result):
    assert result.exit_code == 0
    assert result.output == (
        'Repository bar\n'
        '**************\n'
        'Pipeline: baz\n'
        'Description:\n'
        'Not much tbh\n'
        'Solids: (Execution Order)\n'
        '    do_input\n'
        '*************\n'
        'Pipeline: foo\n'
        'Solids: (Execution Order)\n'
        '    do_something\n'
        '    do_input\n'
    )


def assert_correct_extra_repository_output(result):
    assert result.exit_code == 0
    assert result.output == (
        'Repository extra\n'
        '****************\n'
        'Pipeline: extra\n'
        'Solids: (Execution Order)\n'
        '    do_something\n'
    )


def grpc_instance():
    return DagsterInstance.local_temp(overrides={"opt_in": {"local_servers": True}})


@pytest.mark.skipif(seven.IS_WINDOWS, reason="no named sockets on Windows")
def test_list_command_grpc_socket():
    runner = CliRunner()

    with GrpcServerProcess(
        loadable_target_origin=LoadableTargetOrigin(
            python_file=file_relative_path(__file__, 'test_cli_commands.py'), attribute='bar'
        ),
    ).create_ephemeral_client() as api_client:
        execute_list_command(
            {'grpc_socket': api_client.socket}, no_print, DagsterInstance.local_temp(),
        )
        execute_list_command(
            {'grpc_socket': api_client.socket, 'grpc_host': api_client.host},
            no_print,
            DagsterInstance.local_temp(),
        )

        result = runner.invoke(pipeline_list_command, ['--grpc_socket', api_client.socket])
        assert_correct_bar_repository_output(result)

        result = runner.invoke(
            pipeline_list_command,
            ['--grpc_socket', api_client.socket, '--grpc_host', api_client.host],
        )
        assert_correct_bar_repository_output(result)


def test_list_command():
    runner = CliRunner()

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'bar',
        },
        no_print,
        DagsterInstance.local_temp(),
    )

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'bar',
            'working_directory': os.path.dirname(__file__),
        },
        no_print,
        DagsterInstance.local_temp(),
    )

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'bar',
        },
        no_print,
        grpc_instance(),
    )

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'bar',
            'working_directory': os.path.dirname(__file__),
        },
        no_print,
        grpc_instance(),
    )

    result = runner.invoke(
        pipeline_list_command,
        ['-f', file_relative_path(__file__, 'test_cli_commands.py'), '-a', 'bar'],
    )

    assert_correct_bar_repository_output(result)

    with GrpcServerProcess(
        loadable_target_origin=LoadableTargetOrigin(
            python_file=file_relative_path(__file__, 'test_cli_commands.py'), attribute='bar'
        ),
        force_port=True,
    ).create_ephemeral_client() as api_client:
        execute_list_command(
            {'grpc_port': api_client.port}, no_print, DagsterInstance.local_temp(),
        )
        result = runner.invoke(pipeline_list_command, ['--grpc_port', api_client.port])
        assert_correct_bar_repository_output(result)

        result = runner.invoke(
            pipeline_list_command, ['--grpc_port', api_client.port, '--grpc_host', api_client.host],
        )
        assert_correct_bar_repository_output(result)

        result = runner.invoke(pipeline_list_command, ['--grpc_port', api_client.port],)
        assert_correct_bar_repository_output(result)

        # Can't supply both port and socket
        with pytest.raises(UsageError):
            execute_list_command(
                {'grpc_port': api_client.port, 'grpc_socket': 'foonamedsocket'},
                no_print,
                DagsterInstance.local_temp(),
            )

        result = runner.invoke(
            pipeline_list_command,
            ['--grpc_port', api_client.port, '--grpc_socket', 'foonamedsocket'],
        )

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': None,
            'module_name': 'dagster_tests.cli_tests.command_tests.test_cli_commands',
            'fn_name': 'bar',
        },
        no_print,
        DagsterInstance.local_temp(),
    )

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': None,
            'module_name': 'dagster_tests.cli_tests.command_tests.test_cli_commands',
            'fn_name': 'bar',
        },
        no_print,
        grpc_instance(),
    )

    result = runner.invoke(
        pipeline_list_command,
        ['-m', 'dagster_tests.cli_tests.command_tests.test_cli_commands', '-a', 'bar'],
    )
    assert_correct_bar_repository_output(result)

    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You have used -y or --repository-yaml to load a workspace. This is deprecated and '
            'will be eliminated in 0.9.0.'
        ),
    ):
        execute_list_command(
            {
                'repository_yaml': file_relative_path(__file__, 'repository_module.yaml'),
                'python_file': None,
                'module_name': None,
                'fn_name': None,
            },
            no_print,
            DagsterInstance.local_temp(),
        )

    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        result = runner.invoke(
            pipeline_list_command, ['-w', file_relative_path(__file__, 'repository_module.yaml')]
        )
        assert_correct_bar_repository_output(result)

    result = runner.invoke(
        pipeline_list_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )
    assert_correct_bar_repository_output(result)

    result = runner.invoke(
        pipeline_list_command,
        [
            '-w',
            file_relative_path(__file__, 'workspace.yaml'),
            '-w',
            file_relative_path(__file__, 'override.yaml'),
        ],
    )
    assert_correct_extra_repository_output(result)

    with pytest.raises(UsageError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': 'foo.py',
                'module_name': 'dagster_tests.cli_tests.command_tests.test_cli_commands',
                'fn_name': 'bar',
            },
            no_print,
            DagsterInstance.local_temp(),
        )

    result = runner.invoke(
        pipeline_list_command,
        [
            '-f',
            'foo.py',
            '-m',
            'dagster_tests.cli_tests.command_tests.test_cli_commands',
            '-a',
            'bar',
        ],
    )
    assert result.exit_code == 2

    result = runner.invoke(
        pipeline_list_command, ['-m', 'dagster_tests.cli_tests.command_tests.test_cli_commands'],
    )
    assert_correct_bar_repository_output(result)

    result = runner.invoke(
        pipeline_list_command, ['-f', file_relative_path(__file__, 'test_cli_commands.py')]
    )
    assert_correct_bar_repository_output(result)


# [(cli_args, uses_legacy_repository_yaml_format)]
def valid_execute_args():
    return [
        (
            {
                'workspace': (file_relative_path(__file__, 'repository_file.yaml'),),
                'pipeline': 'foo',
                'python_file': None,
                'module_name': None,
                'attribute': None,
            },
            True,
        ),
        (
            {
                'workspace': (file_relative_path(__file__, 'repository_module.yaml'),),
                'pipeline': 'foo',
                'python_file': None,
                'module_name': None,
                'attribute': None,
            },
            True,
        ),
        (
            {
                'workspace': None,
                'pipeline': 'foo',
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'bar',
            },
            False,
        ),
        (
            {
                'workspace': None,
                'pipeline': 'foo',
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'bar',
                'working_directory': os.path.dirname(__file__),
            },
            False,
        ),
        (
            {
                'workspace': None,
                'pipeline': 'foo',
                'python_file': None,
                'module_name': 'dagster_tests.cli_tests.command_tests.test_cli_commands',
                'attribute': 'bar',
            },
            False,
        ),
        (
            {
                'workspace': None,
                'pipeline': None,
                'python_file': None,
                'module_name': 'dagster_tests.cli_tests.command_tests.test_cli_commands',
                'attribute': 'foo_pipeline',
            },
            False,
        ),
        (
            {
                'workspace': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'define_foo_pipeline',
            },
            False,
        ),
        (
            {
                'workspace': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'define_foo_pipeline',
                'working_directory': os.path.dirname(__file__),
            },
            False,
        ),
        (
            {
                'workspace': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'foo_pipeline',
            },
            False,
        ),
    ]


# [(cli_args, uses_legacy_repository_yaml_format)]
def valid_cli_args():
    return [
        (['-w', file_relative_path(__file__, 'repository_file.yaml'), '-p', 'foo'], True),
        (['-w', file_relative_path(__file__, 'repository_module.yaml'), '-p', 'foo'], True),
        (['-w', file_relative_path(__file__, 'workspace.yaml'), '-p', 'foo'], False),
        (
            [
                '-w',
                file_relative_path(__file__, 'override.yaml'),
                '-w',
                file_relative_path(__file__, 'workspace.yaml'),
                '-p',
                'foo',
            ],
            False,
        ),
        (
            ['-f', file_relative_path(__file__, 'test_cli_commands.py'), '-a', 'bar', '-p', 'foo'],
            False,
        ),
        (
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-d',
                os.path.dirname(__file__),
                '-a',
                'bar',
                '-p',
                'foo',
            ],
            False,
        ),
        (
            [
                '-m',
                'dagster_tests.cli_tests.command_tests.test_cli_commands',
                '-a',
                'bar',
                '-p',
                'foo',
            ],
            False,
        ),
        (
            ['-m', 'dagster_tests.cli_tests.command_tests.test_cli_commands', '-a', 'foo_pipeline'],
            False,
        ),
        (
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'define_foo_pipeline',
            ],
            False,
        ),
        (
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-d',
                os.path.dirname(__file__),
                '-a',
                'define_foo_pipeline',
            ],
            False,
        ),
    ]


@pytest.mark.parametrize('execute_args', valid_execute_args())
def test_print_command_verbose(execute_args):
    cli_args, uses_legacy_repository_yaml_format = execute_args
    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            execute_print_command(verbose=True, cli_args=cli_args, print_fn=no_print)
    else:
        execute_print_command(verbose=True, cli_args=cli_args, print_fn=no_print)


@pytest.mark.parametrize('execute_args', valid_execute_args())
def test_print_command(execute_args):
    cli_args, uses_legacy_repository_yaml_format = execute_args
    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            execute_print_command(verbose=False, cli_args=cli_args, print_fn=no_print)
    else:
        execute_print_command(verbose=False, cli_args=cli_args, print_fn=no_print)


@pytest.mark.parametrize('execute_cli_args', valid_cli_args())
def test_print_command_cli(execute_cli_args):
    runner = CliRunner()
    cli_args, uses_legacy_repository_yaml_format = execute_cli_args
    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            result = runner.invoke(pipeline_print_command, cli_args)
            assert result.exit_code == 0, result.stdout

            result = runner.invoke(pipeline_print_command, ['--verbose'] + cli_args)
            assert result.exit_code == 0, result.stdout
    else:
        result = runner.invoke(pipeline_print_command, cli_args)
        assert result.exit_code == 0, result.stdout

        result = runner.invoke(pipeline_print_command, ['--verbose'] + cli_args)
        assert result.exit_code == 0, result.stdout


def test_print_command_baz():
    runner = CliRunner()
    res = runner.invoke(
        pipeline_print_command,
        [
            '--verbose',
            '-f',
            file_relative_path(__file__, 'test_cli_commands.py'),
            '-a',
            'bar',
            '-p',
            'baz',
        ],
    )
    assert res.exit_code == 0, res.stdout


def test_execute_mode_command():
    runner = CliRunner()

    with test_instance():
        add_result = runner_pipeline_execute(
            runner,
            [
                '-w',
                file_relative_path(__file__, '../../workspace.yaml'),
                '--config',
                file_relative_path(
                    __file__, '../../environments/multi_mode_with_resources/add_mode.yaml'
                ),
                '--mode',
                'add_mode',
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )

        assert add_result

        mult_result = runner_pipeline_execute(
            runner,
            [
                '-w',
                file_relative_path(__file__, '../../workspace.yaml'),
                '--config',
                file_relative_path(
                    __file__, '../../environments/multi_mode_with_resources/mult_mode.yaml'
                ),
                '--mode',
                'mult_mode',
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )

        assert mult_result

        double_adder_result = runner_pipeline_execute(
            runner,
            [
                '-w',
                file_relative_path(__file__, '../../workspace.yaml'),
                '--config',
                file_relative_path(
                    __file__, '../../environments/multi_mode_with_resources/double_adder_mode.yaml'
                ),
                '--mode',
                'double_adder_mode',
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )

        assert double_adder_result


def test_execute_preset_command():
    with test_instance():
        runner = CliRunner()
        add_result = runner_pipeline_execute(
            runner,
            [
                '-w',
                file_relative_path(__file__, '../../workspace.yaml'),
                '--preset',
                'add',
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )

        assert 'PIPELINE_SUCCESS' in add_result.output

        # Can't use --preset with --config
        bad_res = runner.invoke(
            pipeline_execute_command,
            [
                '-w',
                file_relative_path(__file__, '../../workspace.yaml'),
                '--preset',
                'add',
                '--config',
                file_relative_path(
                    __file__, '../../environments/multi_mode_with_resources/double_adder_mode.yaml'
                ),
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )
        assert bad_res.exit_code == 2


@pytest.mark.parametrize('execute_args', valid_execute_args())
def test_execute_command_no_env(execute_args):
    with test_instance():
        cli_args, uses_legacy_repository_yaml_format = execute_args
        if uses_legacy_repository_yaml_format:
            with pytest.warns(
                UserWarning,
                match=re.escape(
                    'You are using the legacy repository yaml format. Please update your file '
                ),
            ):
                execute_execute_command(env_file_list=None, cli_args=cli_args)
        else:
            execute_execute_command(env_file_list=None, cli_args=cli_args)


@pytest.mark.parametrize('execute_args', valid_execute_args())
def test_execute_command_env(execute_args):
    with test_instance():
        cli_args, uses_legacy_repository_yaml_format = execute_args
        if uses_legacy_repository_yaml_format:
            with pytest.warns(
                UserWarning,
                match=re.escape(
                    'You are using the legacy repository yaml format. Please update your file '
                ),
            ):
                execute_execute_command(
                    env_file_list=[file_relative_path(__file__, 'default_log_error_env.yaml')],
                    cli_args=cli_args,
                )
        else:
            execute_execute_command(
                env_file_list=[file_relative_path(__file__, 'default_log_error_env.yaml')],
                cli_args=cli_args,
            )


@pytest.mark.parametrize('execute_cli_args', valid_cli_args())
def test_execute_command_runner(execute_cli_args):
    cli_args, uses_legacy_repository_yaml_format = execute_cli_args
    runner = CliRunner()

    with test_instance():
        if uses_legacy_repository_yaml_format:
            with pytest.warns(
                UserWarning,
                match=re.escape(
                    'You are using the legacy repository yaml format. Please update your file '
                ),
            ):
                runner_pipeline_execute(runner, cli_args)

                runner_pipeline_execute(
                    runner,
                    ['--config', file_relative_path(__file__, 'default_log_error_env.yaml')]
                    + cli_args,
                )
        else:
            runner_pipeline_execute(runner, cli_args)

            runner_pipeline_execute(
                runner,
                ['--config', file_relative_path(__file__, 'default_log_error_env.yaml')] + cli_args,
            )


def test_output_execute_log_stdout(capfd):
    with test_instance(
        overrides={
            'compute_logs': {
                'module': 'dagster.core.storage.noop_compute_log_manager',
                'class': 'NoOpComputeLogManager',
            }
        },
    ) as instance:
        execute_execute_command(
            env_file_list=None,
            cli_args={
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'attribute': 'stdout_pipeline',
            },
            instance=instance,
        )

        captured = capfd.readouterr()
        # All pipeline execute output currently logged to stderr
        assert 'HELLO WORLD' in captured.err


def test_output_execute_log_stderr(capfd):
    with test_instance(
        overrides={
            'compute_logs': {
                'module': 'dagster.core.storage.noop_compute_log_manager',
                'class': 'NoOpComputeLogManager',
            }
        },
    ) as instance:
        execute_execute_command(
            env_file_list=None,
            cli_args={
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'attribute': 'stderr_pipeline',
            },
            instance=instance,
        )
        captured = capfd.readouterr()
        assert 'I AM SUPPOSED TO FAIL' in captured.err


def test_more_than_one_pipeline():
    with pytest.raises(
        UsageError,
        match=re.escape(
            "Must provide --pipeline as there is more than one pipeline in bar. "
            "Options are: ['baz', 'foo']."
        ),
    ):
        execute_execute_command(
            env_file_list=None,
            cli_args={
                'repository_yaml': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': None,
            },
        )


def test_attribute_not_found():
    with pytest.raises(
        DagsterUserCodeProcessError, match=re.escape('nope not found at module scope in file')
    ):
        execute_execute_command(
            env_file_list=None,
            cli_args={
                'repository_yaml': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'nope',
            },
        )


def not_a_repo_or_pipeline_fn():
    return 'kdjfkjdf'


not_a_repo_or_pipeline = 123


def test_attribute_is_wrong_thing():
    with pytest.raises(
        DagsterUserCodeProcessError,
        match=re.escape(
            'Loadable attributes must be either a PipelineDefinition or a '
            'RepositoryDefinition. Got 123.'
        ),
    ):
        execute_execute_command(
            env_file_list=[],
            cli_args={
                'repository_yaml': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'not_a_repo_or_pipeline',
            },
        )


def test_attribute_fn_returns_wrong_thing():
    with pytest.raises(
        DagsterUserCodeProcessError,
        match=re.escape(
            "Loadable attributes must be either a PipelineDefinition or a RepositoryDefinition."
        ),
    ):
        execute_execute_command(
            env_file_list=[],
            cli_args={
                'repository_yaml': None,
                'pipeline': None,
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'module_name': None,
                'attribute': 'not_a_repo_or_pipeline_fn',
            },
        )


def runner_pipeline_execute(runner, cli_args):
    result = runner.invoke(pipeline_execute_command, cli_args)
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                'dagster pipeline execute commands with cli_args {cli_args} '
                'returned exit_code {exit_code} with stdout:\n"{stdout}" and '
                '\nresult as string: "{result}"'
            ).format(
                cli_args=cli_args, exit_code=result.exit_code, stdout=result.stdout, result=result
            )
        )
    return result


@pytest.mark.parametrize('execute_args', valid_execute_args())
def test_scaffold_command(execute_args):
    cli_args, uses_legacy_repository_yaml_format = execute_args
    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            cli_args['print_only_required'] = True
            execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

            cli_args['print_only_required'] = False
            execute_scaffold_command(cli_args=cli_args, print_fn=no_print)
    else:
        cli_args['print_only_required'] = True
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

        cli_args['print_only_required'] = False
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)


@pytest.mark.parametrize('execute_cli_args', valid_cli_args())
def test_scaffold_command_cli(execute_cli_args):
    cli_args, uses_legacy_repository_yaml_format = execute_cli_args

    runner = CliRunner()

    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            result = runner.invoke(pipeline_scaffold_command, cli_args)
            assert result.exit_code == 0

            result = runner.invoke(pipeline_scaffold_command, ['--print-only-required'] + cli_args)
            assert result.exit_code == 0
    else:
        result = runner.invoke(pipeline_scaffold_command, cli_args)
        assert result.exit_code == 0

        result = runner.invoke(pipeline_scaffold_command, ['--print-only-required'] + cli_args)
        assert result.exit_code == 0


def test_default_memory_run_storage():
    cli_args = {
        'workspace': (file_relative_path(__file__, 'repository_file.yaml'),),
        'pipeline': 'foo',
        'python_file': None,
        'module_name': None,
        'attribute': None,
    }
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        result = execute_execute_command(env_file_list=None, cli_args=cli_args)
    assert result.success


def test_override_with_in_memory_storage():
    cli_args = {
        'workspace': (file_relative_path(__file__, 'repository_file.yaml'),),
        'pipeline': 'foo',
        'python_file': None,
        'module_name': None,
        'attribute': None,
    }
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        result = execute_execute_command(
            env_file_list=[file_relative_path(__file__, 'in_memory_env.yaml')], cli_args=cli_args
        )
    assert result.success


def test_override_with_filesystem_storage():
    cli_args = {
        'workspace': (file_relative_path(__file__, 'repository_file.yaml'),),
        'pipeline': 'foo',
        'python_file': None,
        'module_name': None,
        'attribute': None,
    }
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        result = execute_execute_command(
            env_file_list=[file_relative_path(__file__, 'filesystem_env.yaml')], cli_args=cli_args
        )
    assert result.success


def test_run_list():
    runner = CliRunner()
    result = runner.invoke(run_list_command)
    assert result.exit_code == 0


def test_run_wipe_correct_delete_message():
    runner = CliRunner()
    result = runner.invoke(run_wipe_command, input="DELETE\n")
    assert 'Deleted all run history and event logs' in result.output
    assert result.exit_code == 0


def test_run_wipe_incorrect_delete_message():
    runner = CliRunner()
    result = runner.invoke(run_wipe_command, input="WRONG\n")
    assert 'Exiting without deleting all run history and event logs' in result.output
    assert result.exit_code == 0


@pytest.fixture(name="scheduler_instance")
def define_scheduler_instance():
    with seven.TemporaryDirectory() as temp_dir:
        yield DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            schedule_storage=SqliteScheduleStorage.from_local(temp_dir),
            scheduler=FilesystemTestScheduler(temp_dir),
            compute_log_manager=NoOpComputeLogManager(),
            run_launcher=SyncInMemoryRunLauncher(),
        )


@pytest.fixture(name="_patch_scheduler_instance")
def mock_scheduler_instance(mocker, scheduler_instance):
    mocker.patch(
        'dagster.core.instance.DagsterInstance.get', return_value=scheduler_instance,
    )


def test_schedules_list(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_list_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    if result.exception:
        raise result.exception

    assert result.exit_code == 0
    assert result.output == ('Repository bar\n' '**************\n')


def test_schedules_up(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )
    assert result.exit_code == 0
    assert 'Changes:\n  + foo_schedule (add)' in result.output


def test_schedules_up_and_list(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_list_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    assert result.exit_code == 0
    assert (
        result.output == 'Repository bar\n'
        '**************\n'
        'Schedule: foo_schedule [STOPPED]\n'
        'Cron Schedule: * * * * *\n'
    )


def test_schedules_start_and_stop(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')],
    )

    result = runner.invoke(
        schedule_start_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    assert result.exit_code == 0
    assert 'Started schedule foo_schedule\n' == result.output

    result = runner.invoke(
        schedule_stop_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    assert result.exit_code == 0
    assert 'Stopped schedule foo_schedule\n' == result.output


def test_schedules_start_empty(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_start_command, ['-w', file_relative_path(__file__, 'workspace.yaml')],
    )

    assert result.exit_code == 0
    assert 'Noop: dagster schedule start was called without any arguments' in result.output


def test_schedules_start_all(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_start_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), '--start-all'],
    )

    assert result.exit_code == 0
    assert result.output == 'Started all schedules for repository bar\n'


def test_schedules_wipe_correct_delete_message(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_wipe_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml')],
        input="DELETE\n",
    )

    if result.exception:
        raise result.exception

    assert result.exit_code == 0
    assert 'Wiped all schedules and schedule cron jobs' in result.output

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml'), '--preview'],
    )

    # Verify schedules were wiped
    assert result.exit_code == 0
    assert 'Planned Schedule Changes:\n  + foo_schedule (add)' in result.output


def test_schedules_wipe_incorrect_delete_message(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_wipe_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml')],
        input="WRONG\n",
    )

    assert result.exit_code == 0
    assert 'Exiting without deleting all schedules and schedule cron jobs' in result.output

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml'), '--preview'],
    )

    # Verify schedules were not wiped
    assert result.exit_code == 0
    assert result.output == 'No planned changes to schedules.\n1 schedules will remain unchanged\n'


def test_schedules_restart(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_start_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    result = runner.invoke(
        schedule_restart_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    assert result.exit_code == 0
    assert 'Restarted schedule foo_schedule' in result.output


def test_schedules_restart_all(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_up_command, ['-w', file_relative_path(__file__, 'workspace.yaml')]
    )

    result = runner.invoke(
        schedule_start_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    result = runner.invoke(
        schedule_restart_command,
        [
            '-w',
            file_relative_path(__file__, 'workspace.yaml'),
            'foo_schedule',
            '--restart-all-running',
        ],
    )
    assert result.exit_code == 0
    assert result.output == 'Restarted all running schedules for repository bar\n'


def test_schedules_logs(_patch_scheduler_instance):
    runner = CliRunner()

    result = runner.invoke(
        schedule_logs_command,
        ['-w', file_relative_path(__file__, 'workspace.yaml'), 'foo_schedule'],
    )

    assert result.exit_code == 0
    assert result.output.endswith('scheduler.log\n')


def test_multiproc():
    with test_instance():
        runner = CliRunner()
        add_result = runner_pipeline_execute(
            runner,
            [
                '-w',
                file_relative_path(__file__, '../../workspace.yaml'),
                '--preset',
                'multiproc',
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )
        assert add_result.exit_code == 0

        assert 'PIPELINE_SUCCESS' in add_result.output


def test_multiproc_invalid():
    # force ephemeral instance by removing out DAGSTER_HOME
    runner = CliRunner(env={'DAGSTER_HOME': None})
    add_result = runner_pipeline_execute(
        runner,
        [
            '-w',
            file_relative_path(__file__, '../../workspace.yaml'),
            '--preset',
            'multiproc',
            '-p',
            'multi_mode_with_resources',  # pipeline name
        ],
    )
    # which is invalid for multiproc
    assert 'DagsterUnmetExecutorRequirementsError' in add_result.output


class InMemoryRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data
        self._queue = []

    def launch_run(self, instance, run, external_pipeline):
        self._queue.append(run)
        return run

    def queue(self):
        return self._queue

    @classmethod
    def config_type(cls):
        return Shape({})

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data,)

    @property
    def inst_data(self):
        return self._inst_data

    def can_terminate(self, run_id):
        return False

    def terminate(self, run_id):
        check.not_implemented('Termintation not supported')


def backfill_cli_runner_args(execution_args):
    return [
        '-w',
        file_relative_path(__file__, 'repository_file.yaml'),
        '--noprompt',
    ] + execution_args


def run_test_backfill(execution_args, expected_count=None, error_message=None):
    runner = CliRunner()
    run_launcher = InMemoryRunLauncher()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(),
            run_launcher=run_launcher,
        )
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance

            result = runner.invoke(
                pipeline_backfill_command, backfill_cli_runner_args(execution_args),
            )
            if error_message:
                assert result.exit_code == 2, result.stdout
            else:
                assert result.exit_code == 0, result.stdout
                if expected_count:
                    assert len(run_launcher.queue()) == expected_count


def test_backfill_no_pipeline():
    args = ['--pipeline', 'nonexistent']
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        run_test_backfill(args, error_message='No pipeline found')


def test_backfill_no_partition_sets():
    args = ['--pipeline', 'foo']
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        run_test_backfill(args, error_message='No partition sets found')


def test_backfill_no_named_partition_set():
    args = ['--pipeline', 'baz', '--partition-set', 'nonexistent']
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        run_test_backfill(args, error_message='No partition set found')


def test_backfill_launch():
    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions']
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        run_test_backfill(args, expected_count=len(string.ascii_lowercase))


def test_backfill_partition_range():
    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions', '--from', 'x']
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        run_test_backfill(args, expected_count=3)

    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions', '--to', 'c']
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        run_test_backfill(args, expected_count=3)

    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions', '--from', 'c', '--to', 'f']
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        run_test_backfill(args, expected_count=4)


def test_backfill_partition_enum():
    args = ['--pipeline', 'baz', '--partition-set', 'baz_partitions', '--partitions', 'c,x,z']
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'You are using the legacy repository yaml format. Please update your file '
        ),
    ):
        run_test_backfill(args, expected_count=3)


def run_launch(execution_args, expected_count=None):
    runner = CliRunner()
    run_launcher = InMemoryRunLauncher()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(),
            run_launcher=run_launcher,
        )
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance

            result = runner.invoke(pipeline_launch_command, execution_args)
            assert result.exit_code == 0, result.stdout
            if expected_count:
                assert len(run_launcher.queue()) == expected_count


@pytest.mark.parametrize('execute_cli_args', valid_cli_args())
def test_launch_pipeline(execute_cli_args):
    cli_args, uses_legacy_repository_yaml_format = execute_cli_args
    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            run_launch(cli_args, expected_count=1)
    else:
        run_launch(cli_args, expected_count=1)


def test_tags_pipeline():
    runner = CliRunner()
    with test_instance() as instance:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            result = runner.invoke(
                pipeline_execute_command,
                [
                    '-w',
                    file_relative_path(__file__, 'repository_module.yaml'),
                    '--tags',
                    '{ "foo": "bar" }',
                    '-p',
                    'foo',
                ],
            )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) == 1
        assert run.tags.get('foo') == 'bar'

    with test_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-w',
                file_relative_path(__file__, '../../workspace.yaml'),
                '--preset',
                'add',
                '--tags',
                '{ "foo": "bar" }',
                '-p',
                'multi_mode_with_resources',  # pipeline name
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) == 1
        assert run.tags.get('foo') == 'bar'


def test_backfill_tags_pipeline():
    with test_instance() as instance:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            execute_backfill_command(
                {
                    'workspace': (file_relative_path(__file__, 'repository_file.yaml'),),
                    'noprompt': True,
                    'parittion_set': 'baz_partitions',
                    'partitions': 'c',
                    'tags': '{ "foo": "bar" }',
                    'pipeline': 'baz',
                },
                print,
                instance,
            )
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) >= 1
        assert run.tags.get('foo') == 'bar'


def test_execute_subset_pipeline_single_clause_solid_name():
    runner = CliRunner()
    with test_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                'do_something',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ['do_something']
        assert run.solids_to_execute == {'do_something'}


def test_execute_subset_pipeline_single_clause_dsl():
    runner = CliRunner()
    with test_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                '*do_something+',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ['*do_something+']
        assert run.solids_to_execute == {'do_something', 'do_input'}


def test_execute_subset_pipeline_multiple_clauses_dsl_and_solid_name():
    runner = CliRunner()
    with test_instance() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                '*do_something+,do_input',
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert set(run.solid_selection) == set(['*do_something+', 'do_input'])
        assert run.solids_to_execute == {'do_something', 'do_input'}


def test_execute_subset_pipeline_invalid():
    runner = CliRunner()
    with test_instance():
        result = runner.invoke(
            pipeline_execute_command,
            [
                '-f',
                file_relative_path(__file__, 'test_cli_commands.py'),
                '-a',
                'foo_pipeline',
                '--solid-selection',
                'a, b',
            ],
        )
        assert result.exit_code == 1
        assert 'No qualified solids to execute found for solid_selection' in str(result.exception)


def test_launch_subset_pipeline():
    # single clause, solid name
    with test_instance() as instance:
        execute_launch_command(
            instance,
            {
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'attribute': 'foo_pipeline',
                'solid_selection': 'do_something',
            },
        )
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ['do_something']
        assert run.solids_to_execute == {'do_something'}

    # single clause, DSL query
    with test_instance() as instance:
        execute_launch_command(
            instance,
            {
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'attribute': 'foo_pipeline',
                'solid_selection': '*do_something+',
            },
        )

        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ['*do_something+']
        assert run.solids_to_execute == {'do_something', 'do_input'}

    # multiple clauses, DSL query and solid name
    with test_instance() as instance:
        execute_launch_command(
            instance,
            {
                'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                'attribute': 'foo_pipeline',
                'solid_selection': '*do_something+,do_input',
            },
        )
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert set(run.solid_selection) == set(['*do_something+', 'do_input'])
        assert run.solids_to_execute == {'do_something', 'do_input'}

    # invalid value
    with test_instance() as instance:
        with pytest.raises(
            DagsterLaunchFailedError,
            match=re.escape('No qualified solids to execute found for solid_selection'),
        ):
            execute_launch_command(
                instance,
                {
                    'python_file': file_relative_path(__file__, 'test_cli_commands.py'),
                    'attribute': 'foo_pipeline',
                    'solid_selection': 'a, b',
                },
            )

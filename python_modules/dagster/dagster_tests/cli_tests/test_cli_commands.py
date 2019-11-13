from __future__ import print_function

import os

import mock
import pytest
from click import UsageError
from click.testing import CliRunner
from dagster_tests.utils import FilesytemTestScheduler

from dagster import (
    DagsterInvariantViolationError,
    RepositoryDefinition,
    ScheduleDefinition,
    lambda_solid,
    pipeline,
    schedules,
    seven,
    solid,
)
from dagster.check import CheckError
from dagster.cli.pipeline import (
    execute_execute_command,
    execute_list_command,
    execute_print_command,
    execute_scaffold_command,
    pipeline_execute_command,
    pipeline_list_command,
    pipeline_print_command,
    pipeline_scaffold_command,
)
from dagster.cli.run import run_list_command, run_wipe_command
from dagster.cli.schedule import (
    schedule_list_command,
    schedule_restart_command,
    schedule_start_command,
    schedule_stop_command,
    schedule_up_command,
    schedule_wipe_command,
)
from dagster.utils import script_relative_path


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
    do_something()


def define_foo_pipeline():
    return foo_pipeline


@pipeline(name='baz', description='Not much tbh')
def baz_pipeline():
    do_input()


def define_bar_repo():
    return RepositoryDefinition('bar', {'foo': define_foo_pipeline, 'baz': lambda: baz_pipeline})


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


def test_list_command():
    runner = CliRunner()

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': script_relative_path('test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'define_bar_repo',
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command,
        ['-f', script_relative_path('test_cli_commands.py'), '-n', 'define_bar_repo'],
    )

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
    )

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'fn_name': 'define_repo',
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command, ['-m', 'dagster_examples.intro_tutorial.repos', '-n', 'define_repo']
    )
    assert result.exit_code == 0
    assert result.output == (
        'Repository hello_cereal_repository\n'
        '**********************************\n'
        'Pipeline: complex_pipeline\n'
        'Solids: (Execution Order)\n'
        '    load_cereals\n'
        '    sort_by_calories\n'
        '    sort_by_protein\n'
        '    display_results\n'
        '*******************************\n'
        'Pipeline: hello_cereal_pipeline\n'
        'Solids: (Execution Order)\n'
        '    hello_cereal\n'
    )

    execute_list_command(
        {
            'repository_yaml': script_relative_path('repository_module.yaml'),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command, ['-y', script_relative_path('repository_module.yaml')]
    )
    assert result.exit_code == 0
    assert result.output == (
        'Repository hello_cereal_repository\n'
        '**********************************\n'
        'Pipeline: complex_pipeline\n'
        'Solids: (Execution Order)\n'
        '    load_cereals\n'
        '    sort_by_calories\n'
        '    sort_by_protein\n'
        '    display_results\n'
        '*******************************\n'
        'Pipeline: hello_cereal_pipeline\n'
        'Solids: (Execution Order)\n'
        '    hello_cereal\n'
    )

    with pytest.raises(UsageError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': 'foo.py',
                'module_name': 'dagster_examples.intro_tutorial.repos',
                'fn_name': 'define_repo',
            },
            no_print,
        )

    result = runner.invoke(
        pipeline_list_command,
        ['-f', 'foo.py', '-m', 'dagster_examples.intro_tutorial.repos', '-n', 'define_repo'],
    )
    assert result.exit_code == 2

    with pytest.raises(UsageError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': None,
                'module_name': 'dagster_examples.intro_tutorial.repos',
                'fn_name': None,
            },
            no_print,
        )

    result = runner.invoke(pipeline_list_command, ['-m', 'dagster_examples.intro_tutorial.repos'])
    assert result.exit_code == 2

    with pytest.raises(UsageError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': script_relative_path('test_cli_commands.py'),
                'module_name': None,
                'fn_name': None,
            },
            no_print,
        )

    result = runner.invoke(
        pipeline_list_command, ['-f', script_relative_path('test_cli_commands.py')]
    )
    assert result.exit_code == 2


def valid_execute_args():
    return [
        {
            'repository_yaml': script_relative_path('repository_file.yaml'),
            'pipeline_name': ('foo',),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        {
            'repository_yaml': script_relative_path('repository_module.yaml'),
            'pipeline_name': ('hello_cereal_pipeline',),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        {
            'repository_yaml': None,
            'pipeline_name': ('foo',),
            'python_file': script_relative_path('test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'define_bar_repo',
        },
        {
            'repository_yaml': None,
            'pipeline_name': ('hello_cereal_pipeline',),
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'fn_name': 'define_repo',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'fn_name': 'hello_cereal_pipeline',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': script_relative_path('test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'define_foo_pipeline',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': script_relative_path('test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'foo_pipeline',
        },
    ]


def valid_cli_args():
    return [
        ['-y', script_relative_path('repository_file.yaml'), 'foo'],
        ['-y', script_relative_path('repository_module.yaml'), 'hello_cereal_pipeline'],
        ['-f', script_relative_path('test_cli_commands.py'), '-n', 'define_bar_repo', 'foo'],
        [
            '-m',
            'dagster_examples.intro_tutorial.repos',
            '-n',
            'define_repo',
            'hello_cereal_pipeline',
        ],
        ['-m', 'dagster_examples.intro_tutorial.repos', '-n', 'hello_cereal_pipeline'],
        ['-f', script_relative_path('test_cli_commands.py'), '-n', 'define_foo_pipeline'],
    ]


def test_print_command():
    for cli_args in valid_execute_args():
        execute_print_command(verbose=True, cli_args=cli_args, print_fn=no_print)

    for cli_args in valid_execute_args():
        execute_print_command(verbose=False, cli_args=cli_args, print_fn=no_print)

    runner = CliRunner()

    for cli_args in valid_cli_args():
        result = runner.invoke(pipeline_print_command, cli_args)
        assert result.exit_code == 0

        result = runner.invoke(pipeline_print_command, ['--verbose'] + cli_args)
        assert result.exit_code == 0

    res = runner.invoke(
        pipeline_print_command,
        [
            '--verbose',
            '-f',
            script_relative_path('test_cli_commands.py'),
            '-n',
            'define_bar_repo',
            'baz',
        ],
    )
    assert res.exit_code == 0


def test_execute_mode_command():
    runner = CliRunner()

    add_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '--env',
            script_relative_path('../environments/multi_mode_with_resources/add_mode.yaml'),
            '-d',
            'add_mode',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert add_result

    mult_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '--env',
            script_relative_path('../environments/multi_mode_with_resources/mult_mode.yaml'),
            '-d',
            'mult_mode',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert mult_result

    double_adder_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '--env',
            script_relative_path(
                '../environments/multi_mode_with_resources/double_adder_mode.yaml'
            ),
            '-d',
            'double_adder_mode',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert double_adder_result


def test_execute_preset_command():
    runner = CliRunner()
    add_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '-p',
            'add',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert 'PIPELINE_SUCCESS' in add_result.output

    # Can't use -p with --env
    bad_res = runner.invoke(
        pipeline_execute_command,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '-p',
            'add',
            '--env',
            script_relative_path(
                '../environments/multi_mode_with_resources/double_adder_mode.yaml'
            ),
            'multi_mode_with_resources',  # pipeline name
        ],
    )
    assert bad_res.exit_code == 2


def test_execute_command():
    for cli_args in valid_execute_args():
        execute_execute_command(env=None, cli_args=cli_args)

    for cli_args in valid_execute_args():
        execute_execute_command(
            env=[script_relative_path('default_log_error_env.yaml')], cli_args=cli_args
        )

    runner = CliRunner()

    for cli_args in valid_cli_args():
        runner_pipeline_execute(runner, cli_args)

        runner_pipeline_execute(
            runner, ['--env', script_relative_path('default_log_error_env.yaml')] + cli_args
        )

    res = runner.invoke(
        pipeline_execute_command,
        ['-y', script_relative_path('repository_module.yaml'), 'hello_cereal_pipeline', 'foo'],
    )
    assert res.exit_code == 1
    assert isinstance(res.exception, CheckError)
    assert 'Can only handle zero or one pipeline args.' in str(res.exception)


def test_stdout_execute_command():
    runner = CliRunner()
    result = runner_pipeline_execute(
        runner, ['-f', script_relative_path('test_cli_commands.py'), '-n', 'stdout_pipeline']
    )
    assert 'HELLO WORLD' in result.output


def test_stderr_execute_command():
    runner = CliRunner()
    result = runner_pipeline_execute(
        runner, ['-f', script_relative_path('test_cli_commands.py'), '-n', 'stderr_pipeline']
    )
    assert 'I AM SUPPOSED TO FAIL' in result.output


def test_fn_not_found_execute():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_execute_command(
            env=None,
            cli_args={
                'repository_yaml': None,
                'pipeline_name': (),
                'python_file': script_relative_path('test_cli_commands.py'),
                'module_name': None,
                'fn_name': 'nope',
            },
        )

    assert 'nope not found in module' in str(exc_info.value)


def not_a_repo_or_pipeline_fn():
    return 'kdjfkjdf'


not_a_repo_or_pipeline = 123


def test_fn_is_wrong_thing():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_execute_command(
            env={},
            cli_args={
                'repository_yaml': None,
                'pipeline_name': (),
                'python_file': script_relative_path('test_cli_commands.py'),
                'module_name': None,
                'fn_name': 'not_a_repo_or_pipeline',
            },
        )

    assert str(exc_info.value) == (
        'not_a_repo_or_pipeline must be a function that returns a '
        'PipelineDefinition or a RepositoryDefinition, or a function '
        'decorated with @pipeline.'
    )


def test_fn_returns_wrong_thing():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_execute_command(
            env={},
            cli_args={
                'repository_yaml': None,
                'pipeline_name': (),
                'python_file': script_relative_path('test_cli_commands.py'),
                'module_name': None,
                'fn_name': 'not_a_repo_or_pipeline_fn',
            },
        )

    assert str(exc_info.value) == (
        'not_a_repo_or_pipeline_fn is a function but must return a '
        'PipelineDefinition or a RepositoryDefinition, or be decorated '
        'with @pipeline.'
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


def test_scaffold_command():
    for cli_args in valid_execute_args():
        cli_args['print_only_required'] = True
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

        cli_args['print_only_required'] = False
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

    runner = CliRunner()

    for cli_args in valid_cli_args():
        result = runner.invoke(pipeline_scaffold_command, cli_args)
        assert result.exit_code == 0

        result = runner.invoke(pipeline_scaffold_command, ['-p'] + cli_args)
        assert result.exit_code == 0


def test_default_memory_run_storage():
    cli_args = {
        'repository_yaml': script_relative_path('repository_file.yaml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(env=None, cli_args=cli_args)
    assert result.success


def test_override_with_in_memory_storage():
    cli_args = {
        'repository_yaml': script_relative_path('repository_file.yaml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(
        env=[script_relative_path('in_memory_env.yaml')], cli_args=cli_args
    )
    assert result.success


def test_override_with_filesystem_storage():
    cli_args = {
        'repository_yaml': script_relative_path('repository_file.yaml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(
        env=[script_relative_path('filesystem_env.yaml')], cli_args=cli_args
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


@schedules(scheduler=FilesytemTestScheduler)
def define_bar_scheduler():
    return [
        ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            pipeline_name="test_pipeline",
            environment_dict={},
        )
    ]


def test_schedules_list_without_dagster_home():
    runner = CliRunner()

    result = runner.invoke(
        schedule_list_command, ['-y', script_relative_path('repository_file.yaml')]
    )

    assert result.exit_code == 2
    assert 'Error: $DAGSTER_HOME is not set' in result.output


def test_schedules_list():
    runner = CliRunner()

    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_list_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            assert result.exit_code == 0
            assert result.output == ('Repository bar\n' '**************\n')


def test_schedules_up():
    runner = CliRunner()

    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_up_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            assert result.exit_code == 0
            assert result.output == 'Changes:\n  + foo_schedule (add)\n'


def test_schedules_up_and_list():
    runner = CliRunner()

    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_up_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            result = runner.invoke(
                schedule_list_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            assert result.exit_code == 0
            assert (
                result.output == 'Repository bar\n'
                '**************\n'
                'Schedule: foo_schedule [STOPPED]\n'
                'Cron Schedule: * * * * *\n'
            )


def test_schedules_start_and_stop():
    runner = CliRunner()

    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_up_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            result = runner.invoke(
                schedule_start_command,
                ['-y', script_relative_path('repository_file.yaml'), 'foo_schedule'],
            )

            assert result.exit_code == 0
            assert 'Started schedule foo_schedule with ' in result.output

            result = runner.invoke(
                schedule_stop_command,
                ['-y', script_relative_path('repository_file.yaml'), 'foo_schedule'],
            )

            assert result.exit_code == 0
            assert 'Stopped schedule foo_schedule with ' in result.output


def test_schedules_start_all():
    runner = CliRunner()
    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_up_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            result = runner.invoke(
                schedule_start_command,
                ['-y', script_relative_path('repository_file.yaml'), '--start-all'],
            )

            assert result.exit_code == 0
            assert result.output == 'Started all schedules for repository bar\n'


def test_schedules_wipe_correct_delete_message():
    runner = CliRunner()

    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_up_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            result = runner.invoke(
                schedule_wipe_command,
                ['-y', script_relative_path('repository_file.yaml')],
                input="DELETE\n",
            )

            assert result.exit_code == 0
            assert 'Wiped all schedules and schedule cron jobs' in result.output

            result = runner.invoke(
                schedule_up_command,
                ['-y', script_relative_path('repository_file.yaml'), '--preview'],
            )

            # Verify schedules were wiped
            assert result.exit_code == 0
            assert result.output == 'Planned Changes:\n  + foo_schedule (add)\n'


def test_schedules_wipe_incorrect_delete_message():
    runner = CliRunner()

    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_up_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            result = runner.invoke(
                schedule_wipe_command,
                ['-y', script_relative_path('repository_file.yaml')],
                input="WRONG\n",
            )

            assert result.exit_code == 0
            assert 'Exiting without deleting all schedules and schedule cron jobs' in result.output

            result = runner.invoke(
                schedule_up_command,
                ['-y', script_relative_path('repository_file.yaml'), '--preview'],
            )

            # Verify schedules were not wiped
            assert result.exit_code == 0
            assert (
                result.output
                == 'No planned changes to schedules.\n1 schedules will remain unchanged\n'
            )


def test_schedules_restart():
    runner = CliRunner()

    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_up_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            result = runner.invoke(
                schedule_start_command,
                ['-y', script_relative_path('repository_file.yaml'), 'foo_schedule'],
            )

            result = runner.invoke(
                schedule_restart_command,
                ['-y', script_relative_path('repository_file.yaml'), 'foo_schedule'],
            )

            assert result.exit_code == 0
            assert 'Restarted schedule foo_schedule' in result.output


def test_schedules_restart_all():
    runner = CliRunner()

    with seven.TemporaryDirectory() as temp_dir:
        with mock.patch.dict(os.environ, {"DAGSTER_HOME": temp_dir}):
            result = runner.invoke(
                schedule_up_command, ['-y', script_relative_path('repository_file.yaml')]
            )

            result = runner.invoke(
                schedule_start_command,
                ['-y', script_relative_path('repository_file.yaml'), 'foo_schedule'],
            )

            result = runner.invoke(
                schedule_restart_command,
                [
                    '-y',
                    script_relative_path('repository_file.yaml'),
                    'foo_schedule',
                    '--restart-all-running',
                ],
            )

            assert result.exit_code == 0
            assert result.output == 'Restarted all running schedules for repository bar\n'


def test_multiproc():
    with seven.TemporaryDirectory() as temp:
        runner = CliRunner(env={'DAGSTER_HOME': temp})
        add_result = runner_pipeline_execute(
            runner,
            [
                '-y',
                script_relative_path('../repository.yaml'),
                '-p',
                'multiproc',
                'multi_mode_with_resources',  # pipeline name
            ],
        )
        assert 'PIPELINE_SUCCESS' in add_result.output


def test_multiproc_invalid():
    # force ephemeral instance by removing out DAGSTER_HOME
    runner = CliRunner(env={'DAGSTER_HOME': None})
    add_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '-p',
            'multiproc',
            'multi_mode_with_resources',  # pipeline name
        ],
    )
    # which is invalid for multiproc
    assert 'DagsterUnmetExecutorRequirementsError' in add_result.output

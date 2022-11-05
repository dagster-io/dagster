import os
import string
import sys
import tempfile
from contextlib import contextmanager

import mock
import pytest
from click.testing import CliRunner

from dagster import (
    Out,
    Output,
    Partition,
    ScheduleDefinition,
    String,
    graph,
    in_process_executor,
    job,
    op,
    repository,
)
from dagster._cli import ENV_PREFIX, cli
from dagster._cli.job import job_execute_command
from dagster._cli.run import (
    run_delete_command,
    run_list_command,
    run_migrate_command,
    run_wipe_command,
)
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.partition import PartitionedConfig, StaticPartitionsDefinition
from dagster._core.definitions.sensor_definition import RunRequest
from dagster._core.storage.memoizable_io_manager import versioned_filesystem_io_manager
from dagster._core.storage.tags import MEMOIZED_RUN_TAG
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.server import GrpcServerProcess
from dagster._legacy import (
    ModeDefinition,
    PartitionSetDefinition,
    PresetDefinition,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)
from dagster._utils import file_relative_path, merge_dicts
from dagster.version import __version__


@lambda_solid
def do_something():
    return 1


@lambda_solid
def do_input(x):
    return x


@pipeline(
    name="foo",
    preset_defs=[
        PresetDefinition(name="test", tags={"foo": "bar"}),
    ],
)
def foo_pipeline():
    do_input(do_something())


def define_foo_pipeline():
    return foo_pipeline


@op
def do_something_op():
    return 1


@op
def do_input_op(x):
    return x


@graph()
def qux():
    do_input_op(do_something_op())


qux_job = qux.to_job(
    config=PartitionedConfig(
        partitions_def=StaticPartitionsDefinition(["abc"]),
        run_config_for_partition_fn=lambda _: {},
    ),
    tags={"foo": "bar"},
    executor_def=in_process_executor,
)


@job(executor_def=in_process_executor)
def quux_job():
    do_something_op()


def define_qux_job():
    return qux_job


@pipeline(name="baz", description="Not much tbh")
def baz_pipeline():
    do_input()


def not_a_repo_or_pipeline_fn():
    return "kdjfkjdf"


not_a_repo_or_pipeline = 123


@pipeline
def partitioned_scheduled_pipeline():
    do_something()


def define_bar_schedules():
    partition_set = PartitionSetDefinition(
        name="scheduled_partitions",
        pipeline_name="partitioned_scheduled_pipeline",
        partition_fn=lambda: string.digits,
    )
    return {
        "foo_schedule": ScheduleDefinition(
            "foo_schedule",
            cron_schedule="* * * * *",
            job_name="foo",
            run_config={},
        ),
        "union_schedule": ScheduleDefinition(
            "union_schedule",
            cron_schedule=["* * * * *", "* * * * *"],
            job_name="foo",
            run_config={},
        ),
        "partitioned_schedule": partition_set.create_schedule_definition(
            schedule_name="partitioned_schedule",
            cron_schedule="* * * * *",
            partition_selector=lambda _context, _def: Partition("7"),
        ),
    }


def define_bar_partitions():
    def error_name():
        raise Exception("womp womp")

    def error_config(_):
        raise Exception("womp womp")

    return {
        "baz_partitions": PartitionSetDefinition(
            name="baz_partitions",
            pipeline_name="baz",
            partition_fn=lambda: string.digits,
            run_config_fn_for_partition=lambda partition: {
                "solids": {"do_input": {"inputs": {"x": {"value": partition.value}}}}
            },
        ),
        "error_name_partitions": PartitionSetDefinition(
            name="error_name_partitions",
            pipeline_name="baz",
            partition_fn=error_name,
        ),
        "error_config_partitions": PartitionSetDefinition(
            name="error_config_partitions",
            pipeline_name="baz",
            partition_fn=error_config,
        ),
    }


def define_bar_sensors():
    @sensor(job_name="baz")
    def foo_sensor(context):
        run_config = {"foo": "FOO"}
        if context.last_completion_time:
            run_config["since"] = context.last_completion_time
        return RunRequest(run_key=None, run_config=run_config)

    return {"foo_sensor": foo_sensor}


@solid(version="foo")
def my_solid():
    return 5


@pipeline(
    name="memoizable",
    mode_defs=[ModeDefinition(resource_defs={"io_manager": versioned_filesystem_io_manager})],
    tags={MEMOIZED_RUN_TAG: "true"},
)
def memoizable_pipeline():
    my_solid()


@op(version="foo")
def my_op():
    return 5


@job(tags={MEMOIZED_RUN_TAG: "true"}, resource_defs={"io_manager": versioned_filesystem_io_manager})
def memoizable_job():
    my_op()


@repository
def bar():
    return {
        "pipelines": {
            "foo": foo_pipeline,
            "baz": baz_pipeline,
            "partitioned_scheduled_pipeline": partitioned_scheduled_pipeline,
            "memoizable": memoizable_pipeline,
        },
        "jobs": {"qux": qux_job, "quux": quux_job, "memoizable_job": memoizable_job},
        "schedules": define_bar_schedules(),
        "partition_sets": define_bar_partitions(),
        "sensors": define_bar_sensors(),
    }


@solid
def spew(context):
    context.log.info("HELLO WORLD")


@solid
def fail(context):
    raise Exception("I AM SUPPOSED TO FAIL")


@pipeline
def stdout_pipeline():
    spew()


@pipeline
def stderr_pipeline():
    fail()


@op
def spew_op(context):
    context.log.info("SPEW OP")


@op
def fail_op(context):
    raise Exception("FAILURE OP")


@job(executor_def=in_process_executor)
def my_stdout():
    spew_op()


@job(executor_def=in_process_executor)
def my_stderr():
    fail_op()


@op(out={"out_1": Out(String), "out_2": Out(String)})
def root():
    yield Output("foo", "out_1")
    yield Output("bar", "out_2")


@op
def branch_op(_value):
    pass


@graph()
def multiproc():
    out_1, out_2 = root()
    branch_op(out_1)
    branch_op(out_2)


# default executor_def is multiproc
multiproc_job = multiproc.to_job()


@contextmanager
def _default_cli_test_instance_tempdir(temp_dir, overrides=None):
    default_overrides = {
        "run_launcher": {
            "module": "dagster._core.test_utils",
            "class": "MockedRunLauncher",
        }
    }
    with instance_for_test(
        temp_dir=temp_dir,
        overrides=merge_dicts(default_overrides, (overrides if overrides else {})),
    ) as instance:
        with mock.patch("dagster._core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            yield instance


@contextmanager
def default_cli_test_instance(overrides=None):
    with tempfile.TemporaryDirectory() as temp_dir:
        with _default_cli_test_instance_tempdir(temp_dir, overrides) as instance:
            yield instance


@contextmanager
def args_with_instance(gen_instance, *args):
    with gen_instance as instance:
        yield args + (instance,)


def args_with_default_cli_test_instance(*args):
    return args_with_instance(default_cli_test_instance(), *args)


@contextmanager
def grpc_server_bar_kwargs(pipeline_name=None):
    server_process = GrpcServerProcess(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=file_relative_path(__file__, "test_cli_commands.py"),
            attribute="bar",
        ),
    )
    with server_process.create_ephemeral_client() as client:
        args = {"grpc_host": client.host}
        if pipeline_name:
            args["job_name"] = "foo"
        if client.port:
            args["grpc_port"] = client.port
        if client.socket:
            args["grpc_socket"] = client.socket
        yield args
    server_process.wait()


@contextmanager
def python_bar_cli_args(job_name=None):
    args = [
        "-m",
        "dagster_tests.cli_tests.command_tests.test_cli_commands",
        "-a",
        "bar",
    ]
    if job_name:
        args.append("-j")
        args.append(job_name)
    yield args


@contextmanager
def grpc_server_bar_cli_args(job_name=None):
    server_process = GrpcServerProcess(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=file_relative_path(__file__, "test_cli_commands.py"),
            attribute="bar",
        ),
    )
    with server_process.create_ephemeral_client() as client:
        args = ["--grpc-host", client.host]
        if client.port:
            args.append("--grpc-port")
            args.append(client.port)
        if client.socket:
            args.append("--grpc-socket")
            args.append(client.socket)
        if job_name:
            args.append("--job")
            args.append(job_name)

        yield args
    server_process.wait()


@contextmanager
def grpc_server_bar_pipeline_args():
    with default_cli_test_instance() as instance:
        with grpc_server_bar_kwargs(pipeline_name="foo") as kwargs:
            yield kwargs, instance


# This iterates over a list of contextmanagers that can be used to contruct
# (cli_args, instance tuples)
def launch_command_contexts():
    for pipeline_target_args in valid_external_pipeline_target_args():
        yield args_with_default_cli_test_instance(pipeline_target_args)
    yield pytest.param(grpc_server_bar_pipeline_args())


def job_python_origin_contexts():
    return [
        args_with_default_cli_test_instance(target_args)
        for target_args in valid_job_python_origin_target_args()
    ]


@contextmanager
def scheduler_instance(overrides=None):
    with tempfile.TemporaryDirectory() as temp_dir:
        with _default_cli_test_instance_tempdir(
            temp_dir,
            overrides=merge_dicts(
                {
                    "scheduler": {
                        "module": "dagster.utils.test",
                        "class": "FilesystemTestScheduler",
                        "config": {"base_dir": temp_dir},
                    }
                },
                overrides if overrides else {},
            ),
        ) as instance:
            yield instance


@contextmanager
def grpc_server_scheduler_cli_args(overrides=None):
    with scheduler_instance(overrides) as instance:
        with grpc_server_bar_cli_args() as args:
            yield args, instance


# Returns a list of contextmanagers that can be used to contruct
# (cli_args, instance) tuples for schedule calls
def schedule_command_contexts():
    return [
        args_with_instance(
            scheduler_instance(), ["-w", file_relative_path(__file__, "workspace.yaml")]
        ),
        grpc_server_scheduler_cli_args(),
    ]


def sensor_command_contexts():
    return [
        args_with_instance(
            scheduler_instance(),
            ["-w", file_relative_path(__file__, "workspace.yaml")],
        ),
        grpc_server_scheduler_cli_args(),
    ]


# This iterates over a list of contextmanagers that can be used to contruct
# (cli_args, instance) tuples for backfill calls
def backfill_command_contexts():
    repo_args = {
        "noprompt": True,
        "workspace": (file_relative_path(__file__, "repository_file.yaml"),),
    }
    return [
        args_with_instance(default_cli_test_instance(), repo_args),
        grpc_server_backfill_args(),
    ]


@contextmanager
def grpc_server_backfill_args():
    with default_cli_test_instance() as instance:
        with grpc_server_bar_kwargs() as args:
            yield merge_dicts(args, {"noprompt": True}), instance


def non_existant_python_origin_target_args():
    return {
        "workspace": None,
        "job_name": "foo",
        "python_file": file_relative_path(__file__, "made_up_file.py"),
        "module_name": None,
        "attribute": "bar",
    }


def valid_job_python_origin_target_args():
    job_name = "qux"
    job_fn_name = "qux_job"
    job_def_name = "define_qux_job"
    return [
        {
            "workspace": None,
            "job_name": job_name,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "bar",
        },
        {
            "workspace": None,
            "job_name": job_name,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "bar",
            "working_directory": os.path.dirname(__file__),
        },
        {
            "workspace": None,
            "job_name": job_name,
            "python_file": None,
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
        },
        {
            "workspace": None,
            "job_name": job_name,
            "python_file": None,
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
            "working_directory": os.path.dirname(__file__),
        },
        {
            "workspace": None,
            "job_name": job_name,
            "python_file": None,
            "package_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
        },
        {
            "workspace": None,
            "job_name": job_name,
            "python_file": None,
            "package_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
            "working_directory": os.path.dirname(__file__),
        },
        {
            "workspace": None,
            "job_name": None,
            "python_file": None,
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": job_fn_name,
        },
        {
            "workspace": None,
            "job_name": None,
            "python_file": None,
            "package_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": job_fn_name,
        },
        {
            "workspace": None,
            "job_name": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": job_def_name,
        },
        {
            "workspace": None,
            "job_name": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": job_def_name,
            "working_directory": os.path.dirname(__file__),
        },
        {
            "workspace": None,
            "job_name": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": job_fn_name,
        },
    ]


def valid_external_pipeline_target_args():
    return [
        {
            "workspace": (file_relative_path(__file__, "repository_file.yaml"),),
            "job_name": "foo",
            "python_file": None,
            "module_name": None,
            "attribute": None,
        },
        {
            "workspace": (file_relative_path(__file__, "repository_module.yaml"),),
            "job_name": "foo",
            "python_file": None,
            "module_name": None,
            "attribute": None,
        },
    ] + [args for args in valid_job_python_origin_target_args()]


def valid_pipeline_python_origin_target_cli_args():
    return [
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-a",
            "bar",
            "-p",
            "foo",
        ],
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-d",
            os.path.dirname(__file__),
            "-a",
            "bar",
            "-p",
            "foo",
        ],
        [
            "-m",
            "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "-a",
            "bar",
            "-p",
            "foo",
        ],
        [
            "-m",
            "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "-a",
            "foo_pipeline",
        ],
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-a",
            "define_foo_pipeline",
        ],
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-d",
            os.path.dirname(__file__),
            "-a",
            "define_foo_pipeline",
        ],
    ]


def valid_job_python_origin_target_cli_args():
    return [
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-a",
            "bar",
            "-j",
            "qux",
        ],
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-d",
            os.path.dirname(__file__),
            "-a",
            "bar",
            "-j",
            "qux",
        ],
        [
            "-m",
            "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "-a",
            "bar",
            "-j",
            "qux",
        ],
        [
            "-m",
            "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "-a",
            "bar",
            "-d",
            os.path.dirname(__file__),
            "-j",
            "qux",
        ],
        ["-m", "dagster_tests.cli_tests.command_tests.test_cli_commands", "-j", "qux"],
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-a",
            "define_qux_job",
        ],
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-d",
            os.path.dirname(__file__),
            "-a",
            "define_qux_job",
        ],
    ]


def valid_external_pipeline_target_cli_args_no_preset():
    return [
        ["-w", file_relative_path(__file__, "repository_file.yaml"), "-p", "foo"],
        ["-w", file_relative_path(__file__, "repository_module.yaml"), "-p", "foo"],
        ["-w", file_relative_path(__file__, "workspace.yaml"), "-p", "foo"],
        [
            "-w",
            file_relative_path(__file__, "override.yaml"),
            "-w",
            file_relative_path(__file__, "workspace.yaml"),
            "-p",
            "foo",
        ],
    ] + [args for args in valid_pipeline_python_origin_target_cli_args()]


def valid_external_job_target_cli_args():
    return [
        ["-w", file_relative_path(__file__, "repository_file.yaml"), "-j", "qux"],
        ["-w", file_relative_path(__file__, "repository_module.yaml"), "-j", "qux"],
        ["-w", file_relative_path(__file__, "workspace.yaml"), "-j", "qux"],
        [
            "-w",
            file_relative_path(__file__, "override.yaml"),
            "-w",
            file_relative_path(__file__, "workspace.yaml"),
            "-j",
            "qux",
        ],
    ] + [args for args in valid_job_python_origin_target_cli_args()]


def valid_external_pipeline_target_cli_args_with_preset():
    return valid_external_pipeline_target_cli_args_no_preset() + [
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-d",
            os.path.dirname(__file__),
            "-a",
            "define_foo_pipeline",
            "--preset",
            "test",
        ],
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-d",
            os.path.dirname(__file__),
            "-a",
            "define_foo_pipeline",
        ],
    ]


def test_run_list():
    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(run_list_command)
        assert result.exit_code == 0


def test_run_wipe_correct_delete_message():
    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(run_wipe_command, input="DELETE\n")
        assert "Deleted all run history and event logs" in result.output
        assert result.exit_code == 0


@pytest.mark.parametrize("force_flag", ["--force", "-f"])
def test_run_wipe_force(force_flag):
    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(run_wipe_command, args=[force_flag])
        assert "Deleted all run history and event logs" in result.output
        assert result.exit_code == 0


def test_run_wipe_incorrect_delete_message():
    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(run_wipe_command, input="WRONG\n")
        assert "Exiting without deleting all run history and event logs" in result.output
        assert result.exit_code == 1


def test_run_delete_bad_id():
    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(run_delete_command, args=["1234"], input="DELETE\n")
        assert "No run found with id 1234" in result.output
        assert result.exit_code == 1


def test_run_delete_correct_delete_message():
    with instance_for_test() as instance:
        pipeline_result = execute_pipeline(foo_pipeline, instance=instance)
        runner = CliRunner()
        result = runner.invoke(run_delete_command, args=[pipeline_result.run_id], input="DELETE\n")
        assert "Deleted run" in result.output
        assert result.exit_code == 0


@pytest.mark.parametrize("force_flag", ["--force", "-f"])
def test_run_delete_force(force_flag):
    with instance_for_test() as instance:
        run_id = execute_pipeline(foo_pipeline, instance=instance).run_id
        runner = CliRunner()
        result = runner.invoke(run_delete_command, args=[force_flag, run_id])
        assert "Deleted run" in result.output
        assert result.exit_code == 0


def test_run_delete_incorrect_delete_message():
    with instance_for_test() as instance:
        pipeline_result = execute_pipeline(foo_pipeline, instance=instance)
        runner = CliRunner()
        result = runner.invoke(run_delete_command, args=[pipeline_result.run_id], input="Wrong\n")
        assert "Exiting without deleting" in result.output
        assert result.exit_code == 1


def test_run_list_limit():
    with instance_for_test():
        runner = CliRunner()

        runner_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(__file__, "../../environments/double_adder_job.yaml"),
                "-j",
                "double_adder_job",  # job name
            ],
        )

        runner_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(__file__, "../../environments/double_adder_job.yaml"),
                "-j",
                "double_adder_job",  # job name
            ],
        )

        # Should only shows one run because of the limit argument
        result = runner.invoke(run_list_command, args="--limit 1")
        assert result.exit_code == 0
        assert result.output.count("Run: ") == 1
        assert result.output.count("Job: double_adder_job") == 1

        # Shows two runs because of the limit argument is now 2
        two_results = runner.invoke(run_list_command, args="--limit 2")
        assert two_results.exit_code == 0
        assert two_results.output.count("Run: ") == 2
        assert two_results.output.count("Job: double_adder_job") == 2

        # Should only shows two runs although the limit argument is 3 because there are only 2 runs
        shows_two_results = runner.invoke(run_list_command, args="--limit 3")
        assert shows_two_results.exit_code == 0
        assert shows_two_results.output.count("Run: ") == 2
        assert shows_two_results.output.count("Job: double_adder_job") == 2


def runner_job_execute(runner, cli_args):
    result = runner.invoke(
        job_execute_command,
        cli_args,
    )
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                "dagster job execute commands with cli_args {cli_args} "
                'returned exit_code {exit_code} with stdout:\n"{stdout}" and '
                '\nresult as string: "{result}"'
            ).format(
                cli_args=cli_args,
                exit_code=result.exit_code,
                stdout=result.stdout,
                result=result,
            )
        )
    return result


def test_use_env_vars_for_cli_option():
    env_key = "{}_VERSION".format(ENV_PREFIX)
    runner = CliRunner(env={env_key: "1"})
    # use `debug` subcommand to trigger the cli group option flag `--version`
    # see issue: https://github.com/pallets/click/issues/1694
    result = runner.invoke(cli, ["debug"], auto_envvar_prefix=ENV_PREFIX)
    assert __version__ in result.output
    assert result.exit_code == 0


def create_repo_run(instance):
    from dagster._core.test_utils import create_run_for_test
    from dagster._core.workspace.context import WorkspaceProcessContext
    from dagster._core.workspace.load_target import PythonFileTarget

    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=file_relative_path(__file__, "repo_pipeline_and_job.py"),
            attribute=None,
            working_directory=os.path.dirname(__file__),
            location_name=None,
        ),
    ) as workspace_process_context:
        context = workspace_process_context.create_request_context()
        repo = context.repository_locations[0].get_repository("my_repo")
        external_job = repo.get_full_external_job("my_job")
        run = create_run_for_test(
            instance,
            pipeline_name="my_job",
            external_pipeline_origin=external_job.get_external_origin(),
            pipeline_code_origin=external_job.get_python_origin(),
        )
        instance.launch_run(run.run_id, context)
    return run


def get_repo_runs(instance, repo_label):
    from dagster._core.storage.pipeline_run import RunsFilter
    from dagster._core.storage.tags import REPOSITORY_LABEL_TAG

    return instance.get_runs(filters=RunsFilter(tags={REPOSITORY_LABEL_TAG: repo_label}))


def test_run_migrate_command():
    with instance_for_test() as instance:
        create_repo_run(instance)
        old_repo_label = "my_repo@repo_pipeline_and_job.py"
        new_repo_label = "my_other_repo@repo_other_job.py"

        assert len(get_repo_runs(instance, old_repo_label)) == 1
        assert len(get_repo_runs(instance, new_repo_label)) == 0
        runner = CliRunner()
        runner.invoke(
            run_migrate_command,
            args=[
                "--from",
                old_repo_label,
                "-f",
                file_relative_path(__file__, "repo_other_job.py"),
                "-r",
                "my_other_repo",
                "-j",
                "my_job",
            ],
            input="MIGRATE",
        )

        assert len(get_repo_runs(instance, old_repo_label)) == 0
        assert len(get_repo_runs(instance, new_repo_label)) == 1

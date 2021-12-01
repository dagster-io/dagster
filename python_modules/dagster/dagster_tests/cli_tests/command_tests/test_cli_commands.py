import os
import string
import sys
import tempfile
from contextlib import contextmanager

import mock
import pytest
from click.testing import CliRunner
from dagster import (
    ModeDefinition,
    Out,
    Output,
    Partition,
    PartitionSetDefinition,
    PresetDefinition,
    ScheduleDefinition,
    String,
    execute_pipeline,
    graph,
    job,
    lambda_solid,
    op,
    pipeline,
    repository,
    solid,
)
from dagster.cli import ENV_PREFIX, cli
from dagster.cli.job import job_execute_command
from dagster.cli.pipeline import pipeline_execute_command
from dagster.cli.run import run_delete_command, run_list_command, run_wipe_command
from dagster.core.definitions.decorators.sensor import sensor
from dagster.core.definitions.partition import PartitionedConfig, StaticPartitionsDefinition
from dagster.core.definitions.sensor_definition import RunRequest
from dagster.core.storage.memoizable_io_manager import versioned_filesystem_io_manager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.test_utils import instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.utils import file_relative_path, merge_dicts
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
        partitions_def=StaticPartitionsDefinition(["abc"]), run_config_for_partition_fn=lambda _: {}
    ),
    tags={"foo": "bar"},
)


@job
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
            pipeline_name="foo",
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
    @sensor(pipeline_name="baz")
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


@repository
def bar():
    return {
        "pipelines": {
            "foo": foo_pipeline,
            "baz": baz_pipeline,
            "partitioned_scheduled_pipeline": partitioned_scheduled_pipeline,
            "memoizable": memoizable_pipeline,
        },
        "jobs": {"qux": qux_job, "quux": quux_job},
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


@graph()
def my_stdout():
    spew_op()


@graph()
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
            "module": "dagster.core.test_utils",
            "class": "MockedRunLauncher",
        }
    }
    with instance_for_test(
        temp_dir=temp_dir,
        overrides=merge_dicts(default_overrides, (overrides if overrides else {})),
    ) as instance:
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
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
            args["pipeline_or_job"] = "foo"
        if client.port:
            args["grpc_port"] = client.port
        if client.socket:
            args["grpc_socket"] = client.socket
        yield args
    server_process.wait()


@contextmanager
def python_bar_cli_args(pipeline_or_job_name=None, using_job_op_graph_apis=False):
    args = [
        "-m",
        "dagster_tests.cli_tests.command_tests.test_cli_commands",
        "-a",
        "bar",
    ]
    if pipeline_or_job_name:
        args.append("-j" if using_job_op_graph_apis else "-p")
        args.append(pipeline_or_job_name)
    yield args


@contextmanager
def grpc_server_bar_cli_args(pipeline_name=None, using_job_op_graph_apis=False):
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
        if pipeline_name:
            args.append("--job" if using_job_op_graph_apis else "--pipeline")
            args.append(pipeline_name)

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


def pipeline_or_job_python_origin_contexts(using_job_op_graph_apis=False):
    return [
        args_with_default_cli_test_instance(target_args)
        for target_args in valid_pipeline_or_job_python_origin_target_args(using_job_op_graph_apis)
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
        "pipeline_or_job": "foo",
        "python_file": file_relative_path(__file__, "made_up_file.py"),
        "module_name": None,
        "attribute": "bar",
    }


def valid_pipeline_or_job_python_origin_target_args(using_job_op_graph_apis=False):
    pipeline_or_job_name = "qux" if using_job_op_graph_apis else "foo"
    pipeline_or_job_fn_name = "qux_job" if using_job_op_graph_apis else "foo_pipeline"
    pipeline_or_job_def_name = (
        "define_qux_job" if using_job_op_graph_apis else "define_foo_pipeline"
    )
    return [
        {
            "workspace": None,
            "pipeline_or_job": pipeline_or_job_name,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "bar",
        },
        {
            "workspace": None,
            "pipeline_or_job": pipeline_or_job_name,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "bar",
            "working_directory": os.path.dirname(__file__),
        },
        {
            "workspace": None,
            "pipeline_or_job": pipeline_or_job_name,
            "python_file": None,
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
        },
        {
            "workspace": None,
            "pipeline_or_job": pipeline_or_job_name,
            "python_file": None,
            "package_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
        },
        {
            "workspace": None,
            "pipeline_or_job": None,
            "python_file": None,
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": pipeline_or_job_fn_name,
        },
        {
            "workspace": None,
            "pipeline_or_job": None,
            "python_file": None,
            "package_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": pipeline_or_job_fn_name,
        },
        {
            "workspace": None,
            "pipeline_or_job": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": pipeline_or_job_def_name,
        },
        {
            "workspace": None,
            "pipeline_or_job": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": pipeline_or_job_def_name,
            "working_directory": os.path.dirname(__file__),
        },
        {
            "workspace": None,
            "pipeline_or_job": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": pipeline_or_job_fn_name,
        },
    ]


def valid_external_pipeline_target_args():
    return [
        {
            "workspace": (file_relative_path(__file__, "repository_file.yaml"),),
            "pipeline_or_job": "foo",
            "python_file": None,
            "module_name": None,
            "attribute": None,
        },
        {
            "workspace": (file_relative_path(__file__, "repository_module.yaml"),),
            "pipeline_or_job": "foo",
            "python_file": None,
            "module_name": None,
            "attribute": None,
        },
    ] + [args for args in valid_pipeline_or_job_python_origin_target_args()]


def valid_pipeline_python_origin_target_cli_args():
    return [
        ["-f", file_relative_path(__file__, "test_cli_commands.py"), "-a", "bar", "-p", "foo"],
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
        ["-m", "dagster_tests.cli_tests.command_tests.test_cli_commands", "-a", "foo_pipeline"],
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
        ["-f", file_relative_path(__file__, "test_cli_commands.py"), "-a", "bar", "-j", "qux"],
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

        runner_pipeline_or_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--preset",
                "add",
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )

        runner_pipeline_or_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--preset",
                "add",
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )

        # Should only shows one run because of the limit argument
        result = runner.invoke(run_list_command, args="--limit 1")
        assert result.exit_code == 0
        assert result.output.count("Run: ") == 1
        assert result.output.count("Pipeline: multi_mode_with_resources") == 1

        # Shows two runs because of the limit argument is now 2
        two_results = runner.invoke(run_list_command, args="--limit 2")
        assert two_results.exit_code == 0
        assert two_results.output.count("Run: ") == 2
        assert two_results.output.count("Pipeline: multi_mode_with_resources") == 2

        # Should only shows two runs although the limit argument is 3 because there are only 2 runs
        shows_two_results = runner.invoke(run_list_command, args="--limit 3")
        assert shows_two_results.exit_code == 0
        assert shows_two_results.output.count("Run: ") == 2
        assert shows_two_results.output.count("Pipeline: multi_mode_with_resources") == 2


def runner_pipeline_or_job_execute(runner, cli_args, using_job_op_graph_apis=False):
    result = runner.invoke(
        job_execute_command if using_job_op_graph_apis else pipeline_execute_command, cli_args
    )
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                "dagster {pipeline_or_job} execute commands with cli_args {cli_args} "
                'returned exit_code {exit_code} with stdout:\n"{stdout}" and '
                '\nresult as string: "{result}"'
            ).format(
                cli_args=cli_args,
                exit_code=result.exit_code,
                stdout=result.stdout,
                result=result,
                pipeline_or_job="job" if using_job_op_graph_apis else "pipeline",
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

from __future__ import print_function

import json
import os
import string
from contextlib import contextmanager

import mock
import pytest
from click.testing import CliRunner

from dagster import (
    PartitionSetDefinition,
    PresetDefinition,
    ScheduleDefinition,
    Shape,
    check,
    lambda_solid,
    pipeline,
    repository,
    seven,
    solid,
)
from dagster.cli.run import run_list_command, run_wipe_command
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.test_utils import instance_for_test_tempdir
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.serdes import ConfigurableClass
from dagster.utils import file_relative_path, merge_dicts


def no_print(_):
    return None


@lambda_solid
def do_something():
    return 1


@lambda_solid
def do_input(x):
    return x


@pipeline(
    name="foo", preset_defs=[PresetDefinition(name="test", tags={"foo": "bar"}),],
)
def foo_pipeline():
    do_input(do_something())


def define_foo_pipeline():
    return foo_pipeline


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
            "foo_schedule", cron_schedule="* * * * *", pipeline_name="test_pipeline", run_config={},
        ),
        "partitioned_schedule": partition_set.create_schedule_definition(
            schedule_name="partitioned_schedule", cron_schedule="* * * * *"
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
            name="error_name_partitions", pipeline_name="baz", partition_fn=error_name,
        ),
        "error_config_partitions": PartitionSetDefinition(
            name="error_config_partitions", pipeline_name="baz", partition_fn=error_config,
        ),
    }


@repository
def bar():
    return {
        "pipelines": {
            "foo": foo_pipeline,
            "baz": baz_pipeline,
            "partitioned_scheduled_pipeline": partitioned_scheduled_pipeline,
        },
        "schedules": define_bar_schedules(),
        "partition_sets": define_bar_partitions(),
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


class InMemoryRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data
        self._queue = []

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(run, "run", PipelineRun)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
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
        check.not_implemented("Termintation not supported")


@contextmanager
def _default_cli_test_instance_tempdir(temp_dir, overrides=None):
    default_overrides = {
        "run_launcher": {
            "module": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "class": "InMemoryRunLauncher",
        }
    }
    with instance_for_test_tempdir(
        temp_dir, overrides=merge_dicts(default_overrides, (overrides if overrides else {}))
    ) as instance:
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            yield instance


@contextmanager
def default_cli_test_instance(overrides=None):
    with seven.TemporaryDirectory() as temp_dir:
        with _default_cli_test_instance_tempdir(temp_dir, overrides) as instance:
            yield instance


def managed_grpc_instance():
    return default_cli_test_instance(overrides={"opt_in": {"local_servers": True}})


@contextmanager
def args_with_instance(gen_instance, *args):
    with gen_instance as instance:
        yield args + (instance,)


def args_with_default_cli_test_instance(*args):
    return args_with_instance(default_cli_test_instance(), *args)


def args_with_managed_grpc_instance(*args):
    return args_with_instance(managed_grpc_instance(), *args)


@contextmanager
def grpc_server_bar_kwargs(pipeline_name=None):
    server_process = GrpcServerProcess(
        loadable_target_origin=LoadableTargetOrigin(
            python_file=file_relative_path(__file__, "test_cli_commands.py"), attribute="bar"
        ),
    )
    with server_process.create_ephemeral_client() as client:
        args = {"grpc_host": client.host}
        if pipeline_name:
            args["pipeline"] = "foo"
        if client.port:
            args["grpc_port"] = client.port
        if client.socket:
            args["grpc_socket"] = client.socket
        yield args
    server_process.wait()


@contextmanager
def python_bar_cli_args(pipeline_name=None):
    args = [
        "-m",
        "dagster_tests.cli_tests.command_tests.test_cli_commands",
        "-a",
        "bar",
    ]
    if pipeline_name:
        args.append("-p")
        args.append(pipeline_name)
    yield args


@contextmanager
def grpc_server_bar_cli_args(pipeline_name=None):
    server_process = GrpcServerProcess(
        loadable_target_origin=LoadableTargetOrigin(
            python_file=file_relative_path(__file__, "test_cli_commands.py"), attribute="bar"
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
            args.append("--pipeline")
            args.append(pipeline_name)

        yield args
    server_process.wait()


@contextmanager
def grpc_server_bar_pipeline_args():
    with default_cli_test_instance() as instance:
        with grpc_server_bar_kwargs(pipeline_name="foo") as kwargs:
            yield kwargs, False, instance


# This iterates over a list of contextmanagers that can be used to contruct
# (cli_args, uses_legacy_repository_yaml_format, instance tuples)
def launch_command_contexts():
    for pipeline_target_args in valid_external_pipeline_target_args():
        yield args_with_default_cli_test_instance(*pipeline_target_args)
        yield pytest.param(
            args_with_managed_grpc_instance(*pipeline_target_args), marks=pytest.mark.managed_grpc
        )
    yield pytest.param(grpc_server_bar_pipeline_args(), marks=pytest.mark.deployed_grpc)


def pipeline_python_origin_contexts():
    return [
        args_with_default_cli_test_instance(pipeline_target_args)
        for pipeline_target_args in valid_pipeline_python_origin_target_args()
    ]


@contextmanager
def scheduler_instance(overrides=None):
    with seven.TemporaryDirectory() as temp_dir:
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


def managed_grpc_scheduler_instance():
    return scheduler_instance(overrides={"opt_in": {"local_servers": True}})


@contextmanager
def grpc_server_scheduler_cli_args():
    with scheduler_instance() as instance:
        with grpc_server_bar_cli_args() as args:
            yield args, instance


# Returns a list of contextmanagers that can be used to contruct
# (cli_args, instance) tuples for schedule calls
def schedule_command_contexts():
    return [
        args_with_instance(
            scheduler_instance(), ["-w", file_relative_path(__file__, "workspace.yaml")]
        ),
        pytest.param(
            args_with_instance(
                managed_grpc_scheduler_instance(),
                ["-w", file_relative_path(__file__, "workspace.yaml")],
            ),
            marks=pytest.mark.managed_grpc,
        ),
        pytest.param(grpc_server_scheduler_cli_args(), marks=pytest.mark.deployed_grpc),
    ]


# This iterates over a list of contextmanagers that can be used to contruct
# (cli_args, uses_legacy_repository_yaml_format, instance) tuples for backfill calls
def backfill_command_contexts():
    repo_args = {
        "noprompt": True,
        "workspace": (file_relative_path(__file__, "repository_file.yaml"),),
    }
    return [
        args_with_instance(default_cli_test_instance(), repo_args, True),
        pytest.param(
            args_with_instance(managed_grpc_instance(), repo_args, True),
            marks=pytest.mark.managed_grpc,
        ),
        pytest.param(grpc_server_backfill_args(), marks=pytest.mark.deployed_grpc),
    ]


@contextmanager
def grpc_server_backfill_args():
    with default_cli_test_instance() as instance:
        with grpc_server_bar_kwargs() as args:
            yield merge_dicts(args, {"noprompt": True}), False, instance


def valid_pipeline_python_origin_target_args():
    return [
        {
            "workspace": None,
            "pipeline": "foo",
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "bar",
        },
        {
            "workspace": None,
            "pipeline": "foo",
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "bar",
            "working_directory": os.path.dirname(__file__),
        },
        {
            "workspace": None,
            "pipeline": "foo",
            "python_file": None,
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
        },
        {
            "workspace": None,
            "pipeline": None,
            "python_file": None,
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "foo_pipeline",
        },
        {
            "workspace": None,
            "pipeline": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "define_foo_pipeline",
        },
        {
            "workspace": None,
            "pipeline": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "define_foo_pipeline",
            "working_directory": os.path.dirname(__file__),
        },
        {
            "workspace": None,
            "pipeline": None,
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": None,
            "attribute": "foo_pipeline",
        },
    ]


# [(cli_args, uses_legacy_repository_yaml_format)]
def valid_external_pipeline_target_args():
    return [
        (
            {
                "workspace": (file_relative_path(__file__, "repository_file.yaml"),),
                "pipeline": "foo",
                "python_file": None,
                "module_name": None,
                "attribute": None,
            },
            True,
        ),
        (
            {
                "workspace": (file_relative_path(__file__, "repository_module.yaml"),),
                "pipeline": "foo",
                "python_file": None,
                "module_name": None,
                "attribute": None,
            },
            True,
        ),
    ] + [(args, False) for args in valid_pipeline_python_origin_target_args()]


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
        ["-f", file_relative_path(__file__, "test_cli_commands.py"), "-a", "define_foo_pipeline",],
        [
            "-f",
            file_relative_path(__file__, "test_cli_commands.py"),
            "-d",
            os.path.dirname(__file__),
            "-a",
            "define_foo_pipeline",
        ],
    ]


# [(cli_args, uses_legacy_repository_yaml_format)]
def valid_external_pipeline_target_cli_args_no_preset():
    return [
        (["-w", file_relative_path(__file__, "repository_file.yaml"), "-p", "foo"], True),
        (["-w", file_relative_path(__file__, "repository_module.yaml"), "-p", "foo"], True),
        (["-w", file_relative_path(__file__, "workspace.yaml"), "-p", "foo"], False),
        (
            [
                "-w",
                file_relative_path(__file__, "override.yaml"),
                "-w",
                file_relative_path(__file__, "workspace.yaml"),
                "-p",
                "foo",
            ],
            False,
        ),
    ] + [(args, False) for args in valid_pipeline_python_origin_target_cli_args()]


def valid_external_pipeline_target_cli_args_with_preset():
    run_config = {"storage": {"filesystem": {"config": {"base_dir": "/tmp"}}}}
    return valid_external_pipeline_target_cli_args_no_preset() + [
        (
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
            False,
        ),
        (
            [
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-d",
                os.path.dirname(__file__),
                "-a",
                "define_foo_pipeline",
                "--config-json",
                json.dumps(run_config),
            ],
            False,
        ),
    ]


def test_run_list():
    runner = CliRunner()
    result = runner.invoke(run_list_command)
    assert result.exit_code == 0


def test_run_wipe_correct_delete_message():
    runner = CliRunner()
    result = runner.invoke(run_wipe_command, input="DELETE\n")
    assert "Deleted all run history and event logs" in result.output
    assert result.exit_code == 0


def test_run_wipe_incorrect_delete_message():
    runner = CliRunner()
    result = runner.invoke(run_wipe_command, input="WRONG\n")
    assert "Exiting without deleting all run history and event logs" in result.output
    assert result.exit_code == 0

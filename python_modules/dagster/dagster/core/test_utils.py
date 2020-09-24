import os
import time
from contextlib import contextmanager

import yaml

from dagster import (
    DagsterInvariantViolationError,
    Output,
    SolidDefinition,
    composite_solid,
    pipeline,
    seven,
    solid,
)
from dagster.core.instance import DagsterInstance
from dagster.core.launcher.default_run_launcher import DefaultRunLauncher
from dagster.core.launcher.grpc_run_launcher import GrpcRunLauncher
from dagster.utils import merge_dicts


def step_output_event_filter(pipe_iterator):
    for step_event in pipe_iterator:
        if step_event.is_successful_output:
            yield step_event


def single_output_solid(name, input_defs, compute_fn, output_def, description=None):
    """It is commmon to want a Solid that has only inputs, a single output (with the default
    name), and no config. So this is a helper function to do that. This compute function
    must return the naked return value (as opposed to a Output object).

    Args:
        name (str): Name of the solid.
        input_defs (List[InputDefinition]): Inputs of solid.
        compute_fn (callable):
            Callable with the signature
            (context: ExecutionContext, inputs: Dict[str, Any]) : Any
        output_def (OutputDefinition): Output of the solid.
        description (str): Descripion of the solid.

    Returns:
        SolidDefinition:

    Examples:

        .. code-block:: python

            single_output_compute(
                'add_one',
                input_defs=InputDefinition('num', types.Int),
                output_def=OutputDefinition(types.Int),
                compute_fn=lambda context, inputs: inputs['num'] + 1
            )

    """

    def _new_compute_fn(context, input_defs):
        value = compute_fn(context, input_defs)
        if isinstance(value, Output):
            raise DagsterInvariantViolationError(
                """Single output compute Solid {name} returned a Output. Just return
                value directly without wrapping it in Output"""
            )
        yield Output(value=value)

    return SolidDefinition(
        name=name,
        input_defs=input_defs,
        compute_fn=_new_compute_fn,
        output_defs=[output_def],
        description=description,
    )


def nesting_composite_pipeline(depth, num_children, *args, **kwargs):
    """Creates a pipeline of nested composite solids up to "depth" layers, with a fan-out of
    num_children at each layer.

    Total number of solids will be num_children ^ depth
    """

    @solid
    def leaf_node(_):
        return 1

    def create_wrap(inner, name):
        @composite_solid(name=name)
        def wrap():
            for i in range(num_children):
                solid_alias = "%s_node_%d" % (name, i)
                inner.alias(solid_alias)()

        return wrap

    @pipeline(*args, **kwargs)
    def nested_pipeline():
        comp_solid = create_wrap(leaf_node, "layer_%d" % depth)

        for i in range(depth):
            comp_solid = create_wrap(comp_solid, "layer_%d" % (depth - (i + 1)))

        comp_solid.alias("outer")()

    return nested_pipeline


@contextmanager
def environ(env):
    """Temporarily set environment variables inside the context manager and
    fully restore previous environment afterwards
    """
    previous_values = {key: os.getenv(key) for key in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for key, value in previous_values.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value


@contextmanager
def instance_for_test(overrides=None, enable_telemetry=False):
    with seven.TemporaryDirectory() as temp_dir:
        with instance_for_test_tempdir(temp_dir, overrides, enable_telemetry) as instance:
            yield instance


@contextmanager
def instance_for_test_tempdir(temp_dir, overrides=None, enable_telemetry=False):
    # Disable telemetry by default to avoid writing to the tempdir while cleaning it up
    overrides = merge_dicts(
        overrides if overrides else {}, {"telemetry": {"enabled": enable_telemetry}}
    )
    # Write any overrides to disk and set DAGSTER_HOME so that they will still apply when
    # DagsterInstance.get() is called from a different process
    with environ({"DAGSTER_HOME": temp_dir}):
        with open(os.path.join(temp_dir, "dagster.yaml"), "w") as fd:
            yaml.dump(overrides, fd, default_flow_style=False)
        with DagsterInstance.get() as instance:
            try:
                yield instance
            finally:
                # To avoid filesystem contention when we close the temporary directory, wait for
                # all runs to reach a terminal state, and close any subprocesses or threads
                # that might be accessing the run history DB.
                instance.run_launcher.join()
                if isinstance(instance.run_launcher, (DefaultRunLauncher, GrpcRunLauncher)):
                    instance.run_launcher.cleanup_managed_grpc_servers()


def create_run_for_test(
    instance,
    pipeline_name=None,
    run_id=None,
    run_config=None,
    mode=None,
    solids_to_execute=None,
    step_keys_to_execute=None,
    status=None,
    tags=None,
    root_run_id=None,
    parent_run_id=None,
    pipeline_snapshot=None,
    execution_plan_snapshot=None,
    parent_pipeline_snapshot=None,
):
    return instance.create_run(
        pipeline_name,
        run_id,
        run_config,
        mode,
        solids_to_execute,
        step_keys_to_execute,
        status,
        tags,
        root_run_id,
        parent_run_id,
        pipeline_snapshot,
        execution_plan_snapshot,
        parent_pipeline_snapshot,
    )


def register_managed_run_for_test(
    instance,
    pipeline_name=None,
    run_id=None,
    run_config=None,
    mode=None,
    solids_to_execute=None,
    step_keys_to_execute=None,
    tags=None,
    root_run_id=None,
    parent_run_id=None,
    pipeline_snapshot=None,
    execution_plan_snapshot=None,
    parent_pipeline_snapshot=None,
):
    return instance.register_managed_run(
        pipeline_name,
        run_id,
        run_config,
        mode,
        solids_to_execute,
        step_keys_to_execute,
        tags,
        root_run_id,
        parent_run_id,
        pipeline_snapshot,
        execution_plan_snapshot,
        parent_pipeline_snapshot,
    )


def poll_for_finished_run(instance, run_id, timeout=20):
    total_time = 0
    interval = 0.01

    while True:
        run = instance.get_run_by_id(run_id)
        if run.is_finished:
            return run
        else:
            time.sleep(interval)
            total_time += interval
            if total_time > timeout:
                raise Exception("Timed out")


def poll_for_step_start(instance, run_id, timeout=10):
    poll_for_event(instance, run_id, event_type="STEP_START", message=None, timeout=timeout)


def poll_for_event(instance, run_id, event_type, message, timeout=10):
    total_time = 0
    backoff = 0.01

    while True:
        time.sleep(backoff)
        logs = instance.all_logs(run_id)
        matching_events = [
            log_record.dagster_event
            for log_record in logs
            if log_record.dagster_event.event_type_value == event_type
        ]
        if matching_events:
            if message is None:
                return
            for matching_message in (event.message for event in matching_events):
                if message in matching_message:
                    return

        total_time += backoff
        backoff = backoff * 2
        if total_time > timeout:
            raise Exception("Timed out")


@contextmanager
def new_cwd(path):
    old = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)

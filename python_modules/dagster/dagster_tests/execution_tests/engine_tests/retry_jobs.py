# pylint: disable=unused-argument
import os
import pickle
import re
from tempfile import TemporaryDirectory
from typing import Any, Callable, Dict, Tuple

from dagster import (
    DynamicOut,
    DynamicOutput,
    ExecutorDefinition,
    JobDefinition,
    ReexecutionOptions,
    execute_job,
    job,
    op,
    reconstructable,
    resource,
)
from dagster._core.test_utils import instance_for_test


def get_dynamic_job_resource_init_failure(
    executor_def: ExecutorDefinition,
) -> Tuple[JobDefinition, Callable[[str, int, int], Dict[str, Any]]]:
    # Induces failure state where among a series of dynamic steps induced from
    # upstream dynamic outputs, some of those steps fail during resource
    # initialization time. Since resource initialization is happening across
    # multiple processes, it is necessary to track the total number of
    # initializations that have already occurred within an external file
    # (count.pkl) so that state can be shared. In multiprocessing case, race
    # conditions are avoided by setting max concurrency to 1.
    @op(out=DynamicOut(), config_schema={"num_dynamic_steps": int})
    def source(context):
        for i in range(context.op_config["num_dynamic_steps"]):
            yield DynamicOutput(i, mapping_key=str(i))

    @resource(config_schema={"path": str, "allowed_initializations": int})
    def resource_for_dynamic_step(init_context):

        # Get the count of successful initializations. If it is already at the
        # allowed initialization number, fail.
        with open(os.path.join(init_context.resource_config["path"], "count.pkl"), "rb") as f:
            init_count = pickle.load(f)
            if init_count == init_context.resource_config["allowed_initializations"]:
                raise Exception("too many initializations.")

        # We have not yet reached the allowed initializaton number, allow
        # initialization to complete and add to total init number.
        with open(os.path.join(init_context.resource_config["path"], "count.pkl"), "wb") as f:
            init_count += 1
            pickle.dump(init_count, f)
        return None

    @op(required_resource_keys={"foo"})
    def mapped_op(x):
        pass

    @op
    def consumer(x):
        pass

    @job(resource_defs={"foo": resource_for_dynamic_step}, executor_def=executor_def)
    def the_job():
        consumer(source().map(mapped_op).collect())

    return (
        the_job,
        lambda temp_dir, init_count, dynamic_steps: {
            "resources": {
                "foo": {"config": {"path": temp_dir, "allowed_initializations": init_count}}
            },
            "ops": {"source": {"config": {"num_dynamic_steps": dynamic_steps}}},
        },
    )


def get_dynamic_job_op_failure(
    executor_def: ExecutorDefinition,
) -> Tuple[JobDefinition, Callable[[str, int, int], Dict[str, Any]]]:
    # Induces failure state where among a series of dynamic steps induced from
    # upstream dynamic outputs, some of those steps fail during op runtime.
    # Since step runs are happening across multiple processes, it is necessary
    # to track the total number of initializations that have already occurred
    # within an external file (count.pkl) so that state can be shared. In
    # multiprocessing case, race conditions are avoided by setting max
    # concurrency to 1.
    @op(out=DynamicOut())
    def source():
        for i in range(3):
            yield DynamicOutput(i, mapping_key=str(i))

    @op(config_schema={"path": str, "allowed_runs": int})
    def mapped_op(context, x):

        # Get the count of successful initializations. If it is already at the
        # allowed initialization number, fail.
        with open(os.path.join(context.op_config["path"], "count.pkl"), "rb") as f:
            run_count = pickle.load(f)
            if run_count == context.op_config["allowed_runs"]:
                raise Exception("oof")

        # We have not yet reached the allowed initializaton number, allow
        # initialization to complete and add to total init number.
        with open(os.path.join(context.op_config["path"], "count.pkl"), "wb") as f:
            run_count += 1
            pickle.dump(run_count, f)

    @op
    def consumer(x):
        return 4

    @job
    def the_job():
        consumer(source().map(mapped_op).collect())

    return (
        the_job,
        lambda temp_dir, run_count, dynamic_steps: {
            "ops": {
                "mapped_op": {"config": {"path": temp_dir, "allowed_runs": run_count}},
                "source": {"config": {"num_dynamic_steps": dynamic_steps}},
            }
        },
    )


def _regexes_match(regexes, the_list):
    return all([re.match(regex, item) for regex, item in zip(regexes, the_list)])


def _write_blank_count(path):
    with open(os.path.join(path, "count.pkl"), "wb") as f:
        pickle.dump(0, f)


def assert_expected_failure_behavior(job_fn, config_fn):
    num_dynamic_steps = 3
    with TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            _write_blank_count(temp_dir)
            result = execute_job(
                reconstructable(job_fn),
                instance,
                run_config=config_fn(
                    temp_dir, 1, num_dynamic_steps
                ),  # Only allow one dynamic step to pass
            )
            assert not result.success
            assert len(result.get_step_success_events()) == 2
            assert _regexes_match(
                [r"source", r"mapped_op\[\d\]"],
                [event.step_key for event in result.get_step_success_events()],
            )
            assert len(result.get_failed_step_keys()) == 2
            assert _regexes_match(
                [r"mapped_op\[\d\]", r"mapped_op\[\d\]"],
                list(result.get_failed_step_keys()),
            )
            _write_blank_count(temp_dir)
            retry_result = execute_job(
                reconstructable(job_fn),
                instance,
                run_config=config_fn(
                    temp_dir, num_dynamic_steps, num_dynamic_steps
                ),  # Allows all dynamic steps to pass
                reexecution_options=ReexecutionOptions.from_failure(
                    run_id=result.run_id, instance=instance
                ),
            )
            assert retry_result.success
            assert len(retry_result.get_step_success_events()) == 3
            assert _regexes_match(
                [r"mapped_op\[\d\]", r"mapped_op\[\d\]", "consumer"],
                [event.step_key for event in retry_result.get_step_success_events()],
            )

import pytest

from dagster import (
    DagsterExecutionStepNotFoundError,
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
    Field,
    ReexecutionOptions,
    execute_job,
    graph,
    job,
    op,
    reconstructable,
)
import dagster._check as check
from dagster._core.test_utils import instance_for_test


@pytest.fixture(scope="session")
def instance():
    with instance_for_test() as instance:
        yield instance


def emit_job():
    @op
    def emit_five():
        return 5

    @op
    def returns_six(x):
        return x + 1

    @graph
    def nested():
        return returns_six(emit_five())

    @op(config_schema={"baz": Field(str, default_value="blah")})
    def conditional_return(context, x):
        if context.op_config["baz"] == "blah":
            return x + 1
        else:
            return x + 2

    @job
    def the_job():
        conditional_return(nested())

    return the_job


def emit_error_job():
    @op
    def the_op_fails():
        raise Exception()

    @job
    def the_job_fails():
        the_op_fails()

    return the_job_fails


def test_basic_success(instance):
    result = execute_job(reconstructable(emit_job), instance)
    assert result.success


def test_no_raise_on_error(instance):
    result = execute_job(reconstructable(emit_error_job), instance)
    assert not result.success


def test_tags_for_run(instance):
    result = execute_job(reconstructable(emit_job), instance, tags={"foo": "bar"})
    assert result.success
    run = instance.get_run_by_id(result.run_id)
    assert run.tags == {"foo": "bar"}


def test_run_config(instance):
    with execute_job(
        reconstructable(emit_job),
        instance,
        run_config={"ops": {"conditional_return": {"config": {"baz": "not_blah"}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("conditional_return") == 8

    with pytest.raises(DagsterInvalidConfigError):
        execute_job(
            reconstructable(emit_job),
            instance,
            run_config={"ops": {"conditional_return": "bad_config"}},
            raise_on_error=True,
        )


def test_retrieve_outputs_not_context_manager(instance):
    result = execute_job(reconstructable(emit_job), instance)
    with pytest.raises(DagsterInvariantViolationError, match="must be opened as a context manager"):
        result.output_for_node("nested")


def test_op_selection(instance):
    with execute_job(
        reconstructable(emit_job),
        instance,
        op_selection=["nested.returns_six"],
        run_config={
            "ops": {
                "nested": {
                    "ops": {
                        "returns_six": {"inputs": {"x": {"value": 5}}},
                    }
                }
            }
        },
    ) as result:
        assert result.success
        assert result.output_for_node("nested.returns_six") == 6
        with pytest.raises(DagsterInvariantViolationError):
            result.output_for_node("conditional_return")


def test_result_output_access(instance):
    result = execute_job(reconstructable(emit_job), instance)
    with result:
        assert result.output_for_node("conditional_return") == 7

    with pytest.raises(DagsterInvariantViolationError):
        result.output_for_node("conditional_return")


def emit_based_on_config():
    @op(config_schema=str)
    def the_op(context):
        return context.op_config

    @op
    def ingest(x):
        return x

    @job
    def the_job():
        ingest(the_op())

    return the_job


def test_reexecution_with_steps(instance):
    with execute_job(
        reconstructable(emit_based_on_config),
        instance,
        run_config={"ops": {"the_op": {"config": "blah"}}},
    ) as result:
        assert result.success
        assert result.output_for_node("ingest") == "blah"

    reexecution_options = ReexecutionOptions(parent_run_id=result.run_id, step_selection=["ingest"])

    # Ensure that re-execution successfully used output from previous
    # execution, even though the config required to get that output was not
    # provided.
    with execute_job(
        reconstructable(emit_based_on_config), instance, reexecution_options=reexecution_options
    ) as result:
        assert result.success
        assert result.output_for_node("ingest") == "blah"
        assert len(result.get_step_success_events()) == 1


def error_on_config():
    @op
    def start():
        return 5

    @op(config_schema=str)
    def the_op_errors(context, x):
        if context.op_config == "blah":
            raise Exception()
        else:
            return x

    @job
    def the_job():
        the_op_errors(start())

    return the_job


def test_reexecution_from_failure(instance):
    with execute_job(
        reconstructable(error_on_config),
        instance,
        run_config={"ops": {"the_op_errors": {"config": "blah"}}},
    ) as result:
        assert not result.success

    reexecution_options = ReexecutionOptions.from_failure(result.run_id, instance)

    with execute_job(
        reconstructable(error_on_config),
        instance,
        run_config={"ops": {"the_op_errors": {"config": "no"}}},
        reexecution_options=reexecution_options,
    ) as result:
        assert result.success
        assert result.output_for_node("the_op_errors") == 5
        assert len(result.get_step_success_events()) == 1


def test_reexecution_steps_dont_match(instance):
    with execute_job(
        reconstructable(emit_job),
        instance,
        op_selection=["conditional_return"],
        run_config={"ops": {"conditional_return": {"inputs": {"x": {"value": 4}}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("conditional_return") == 5

    reexecution_options = ReexecutionOptions(
        result.run_id, step_selection=["nested.returns_six", "nested.emit_five"]
    )
    with pytest.raises(DagsterExecutionStepNotFoundError, match="unknown steps"):
        execute_job(reconstructable(emit_job), instance, reexecution_options=reexecution_options)

    # Show that if you use the same reexecution options from a parent
    # execution that contains the correct steps, it works.

    with execute_job(reconstructable(emit_job), instance) as result:
        assert result.success
        assert result.output_for_node("conditional_return") == 7

    reexecution_options = ReexecutionOptions(
        result.run_id, step_selection=["nested.returns_six", "nested.emit_five"]
    )
    with execute_job(
        reconstructable(emit_job), instance, reexecution_options=reexecution_options
    ) as result:
        assert result.success
        assert result.output_for_node("nested") == 6
        assert len(result.get_step_success_events()) == 2


def test_reexecute_from_failure_successful_run(instance):
    with execute_job(
        reconstructable(emit_job),
        instance,
        op_selection=["conditional_return"],
        run_config={"ops": {"conditional_return": {"inputs": {"x": {"value": 4}}}}},
    ) as result:
        assert result.success

    with pytest.raises(check.CheckError, match="run that is not failed"):
        ReexecutionOptions.from_failure(result.run_id, instance)

import pytest

from dagster import DagsterInvalidConfigError, Field, execute_job, graph, job, op, reconstructable
from dagster.check import CheckError
from dagster.core.test_utils import instance_for_test


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
    with execute_job(reconstructable(emit_job), instance) as result:
        assert result.success


def test_no_raise_on_error(instance):
    with execute_job(
        reconstructable(emit_error_job),
        instance,
        raise_on_error=False,
    ) as result:
        assert not result.success


def test_tags_for_run(instance):
    with execute_job(reconstructable(emit_job), instance, tags={"foo": "bar"}) as result:
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
        )


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
        with pytest.raises(CheckError):
            result.output_for_node("conditional_return")

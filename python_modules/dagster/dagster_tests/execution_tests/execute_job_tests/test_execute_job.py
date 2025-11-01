import dagster as dg
import pytest
from dagster import OpExecutionContext, ReexecutionOptions, in_process_executor


@pytest.fixture(scope="session")
def instance():
    with dg.instance_for_test() as instance:
        yield instance


def emit_job():
    @dg.op
    def emit_five():
        return 5

    @dg.op
    def returns_six(x):
        return x + 1

    @dg.graph
    def nested():
        return returns_six(emit_five())

    @dg.op(config_schema={"baz": dg.Field(str, default_value="blah")})
    def conditional_return(context, x):
        if context.op_config["baz"] == "blah":
            return x + 1
        else:
            return x + 2

    @dg.job
    def the_job():
        conditional_return(nested())

    return the_job


def emit_error_job():
    @dg.op
    def the_op_fails():
        raise Exception()

    @dg.job
    def the_job_fails():
        the_op_fails()

    return the_job_fails


def build_warn_job():
    @dg.asset
    def upstream():
        return 1

    @dg.asset_check(asset=upstream, name="warn_check")
    def warn_check(_):
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.WARN)

    job = dg.define_asset_job(
        "the_job_warns",
        selection=[upstream],
        executor_def=dg.in_process_executor,
    )

    defs = dg.Definitions(assets=[upstream], asset_checks=[warn_check], jobs=[job])
    return defs.get_job_def("the_job_warns")


def build_error_and_warn_job():
    """Job with an asset that raises ERROR and also has a WARN-failing check.
    Final run status should be FAILURE (ERROR wins over WARN).
    """

    @dg.asset
    def bad_asset():
        # Simulate a real failure in the asset step
        raise Exception("boom")

    @dg.asset_check(asset=bad_asset, name="warn_check")
    def warn_check(_):
        # Even though this fails at WARN, the asset itself errors.
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.WARN)

    # Pin in-process so event/status resolution happens synchronously
    job = dg.define_asset_job(
        "the_job_error_and_warn",
        selection=[bad_asset],
        executor_def=dg.in_process_executor,
    )

    defs = dg.Definitions(assets=[bad_asset], asset_checks=[warn_check], jobs=[job])
    return defs.get_job_def("the_job_error_and_warn")


def test_basic_success(instance):
    result = dg.execute_job(dg.reconstructable(emit_job), instance)
    assert result.success


def test_no_raise_on_error(instance):
    result = dg.execute_job(dg.reconstructable(emit_error_job), instance)
    assert not result.success


def test_success_with_warnings(instance):
    result = dg.execute_job(dg.reconstructable(build_warn_job), instance)

    run = instance.get_run_by_id(result.run_id)
    assert run.status == dg.DagsterRunStatus.SUCCESS_WITH_WARNINGS


def test_error_precedence_over_warn(instance):
    result = dg.execute_job(dg.reconstructable(build_error_and_warn_job), instance)

    assert not result.success
    run = instance.get_run_by_id(result.run_id)
    assert run.status == dg.DagsterRunStatus.FAILURE


def test_tags_for_run(instance):
    result = dg.execute_job(dg.reconstructable(emit_job), instance, tags={"foo": "bar"})
    assert result.success
    run = instance.get_run_by_id(result.run_id)
    assert run.tags == {"foo": "bar"}


def test_run_config(instance):
    with dg.execute_job(
        dg.reconstructable(emit_job),
        instance,
        run_config={"ops": {"conditional_return": {"config": {"baz": "not_blah"}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("conditional_return") == 8

    with pytest.raises(dg.DagsterInvalidConfigError):
        dg.execute_job(
            dg.reconstructable(emit_job),
            instance,
            run_config={"ops": {"conditional_return": "bad_config"}},
            raise_on_error=True,
        )


def test_retrieve_outputs_not_context_manager(instance):
    result = dg.execute_job(dg.reconstructable(emit_job), instance)
    with pytest.raises(
        dg.DagsterInvariantViolationError, match="must be opened as a context manager"
    ):
        result.output_for_node("nested")


def test_op_selection(instance):
    with dg.execute_job(
        dg.reconstructable(emit_job),
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
        with pytest.raises(dg.DagsterInvariantViolationError):
            result.output_for_node("conditional_return")


def test_result_output_access(instance):
    result = dg.execute_job(dg.reconstructable(emit_job), instance)
    with result:
        assert result.output_for_node("conditional_return") == 7

    with pytest.raises(dg.DagsterInvariantViolationError):
        result.output_for_node("conditional_return")


def emit_based_on_config():
    @dg.op(config_schema=str)
    def the_op(context):
        return context.op_config

    @dg.op
    def ingest(x):
        return x

    @dg.job
    def the_job():
        ingest(the_op())

    return the_job


def test_reexecution_with_steps(instance):
    with dg.execute_job(
        dg.reconstructable(emit_based_on_config),
        instance,
        run_config={"ops": {"the_op": {"config": "blah"}}},
    ) as result:
        assert result.success
        assert result.output_for_node("ingest") == "blah"

    reexecution_options = dg.ReexecutionOptions(
        parent_run_id=result.run_id, step_selection=["ingest"]
    )

    # Ensure that re-execution successfully used output from previous
    # execution, even though the config required to get that output was not
    # provided.
    with dg.execute_job(
        dg.reconstructable(emit_based_on_config), instance, reexecution_options=reexecution_options
    ) as result:
        assert result.success
        assert result.output_for_node("ingest") == "blah"
        assert len(result.get_step_success_events()) == 1


def error_on_config():
    @dg.op
    def start():
        return 5

    @dg.op(config_schema=str)
    def the_op_errors(context, x):
        if context.op_config == "blah":
            raise Exception()
        else:
            return x

    @dg.job
    def the_job():
        the_op_errors(start())

    return the_job


def test_reexecution_from_failure(instance):
    with dg.execute_job(
        dg.reconstructable(error_on_config),
        instance,
        run_config={"ops": {"the_op_errors": {"config": "blah"}}},
    ) as result:
        assert not result.success

    reexecution_options = ReexecutionOptions.from_failure(result.run_id, instance)

    with dg.execute_job(
        dg.reconstructable(error_on_config),
        instance,
        run_config={"ops": {"the_op_errors": {"config": "no"}}},
        reexecution_options=reexecution_options,
    ) as result:
        assert result.success
        assert result.output_for_node("the_op_errors") == 5
        assert len(result.get_step_success_events()) == 1


def test_reexecution_steps_dont_match(instance):
    with dg.execute_job(
        dg.reconstructable(emit_job),
        instance,
        op_selection=["conditional_return"],
        run_config={"ops": {"conditional_return": {"inputs": {"x": {"value": 4}}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("conditional_return") == 5

    reexecution_options = dg.ReexecutionOptions(
        result.run_id, step_selection=["nested.returns_six", "nested.emit_five"]
    )
    with pytest.raises(dg.DagsterExecutionStepNotFoundError, match="unknown steps"):
        dg.execute_job(
            dg.reconstructable(emit_job), instance, reexecution_options=reexecution_options
        )

    # Show that if you use the same reexecution options from a parent
    # execution that contains the correct steps, it works.

    with dg.execute_job(dg.reconstructable(emit_job), instance) as result:
        assert result.success
        assert result.output_for_node("conditional_return") == 7

    reexecution_options = dg.ReexecutionOptions(
        result.run_id, step_selection=["nested.returns_six", "nested.emit_five"]
    )
    with dg.execute_job(
        dg.reconstructable(emit_job), instance, reexecution_options=reexecution_options
    ) as result:
        assert result.success
        assert result.output_for_node("nested") == 6
        assert len(result.get_step_success_events()) == 2


def test_reexecute_from_failure_successful_run(instance):
    with dg.execute_job(
        dg.reconstructable(emit_job),
        instance,
        op_selection=["conditional_return"],
        run_config={"ops": {"conditional_return": {"inputs": {"x": {"value": 4}}}}},
    ) as result:
        assert result.success

    with pytest.raises(dg.DagsterInvariantViolationError, match="run that is not failed"):
        dg.execute_job(
            dg.reconstructable(emit_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result.run_id, instance),
        )


def highly_nested_job():
    @dg.op
    def emit_one():
        return 1

    @dg.op
    def add_one(x):
        return x + 1

    @dg.job(executor_def=in_process_executor)
    def the_job():
        add_one.alias("add_one_outer")(
            add_one.alias("add_one_middle")(add_one.alias("add_one_inner")(emit_one()))
        )

    return the_job


def test_reexecution_selection_syntax(instance):
    result = dg.execute_job(dg.reconstructable(highly_nested_job), instance)
    assert result.success

    # should execute every step, as ever step is upstream of add_one_outer
    options_upstream = dg.ReexecutionOptions(
        parent_run_id=result.run_id, step_selection=["*add_one_middle"]
    )
    result = dg.execute_job(
        dg.reconstructable(highly_nested_job), instance, reexecution_options=options_upstream
    )
    assert result.success
    assert len(result.get_step_success_events()) == 3

    # should execute every step, as ever step is upstream of add_one_outer
    options_downstream = dg.ReexecutionOptions(
        parent_run_id=result.run_id, step_selection=["*add_one_middle"]
    )
    result = dg.execute_job(
        dg.reconstructable(highly_nested_job), instance, reexecution_options=options_downstream
    )
    assert result.success
    assert len(result.get_step_success_events()) == 3

    # two levels up upstream
    options_upstream = dg.ReexecutionOptions(
        parent_run_id=result.run_id, step_selection=["++add_one_outer"]
    )
    result = dg.execute_job(
        dg.reconstructable(highly_nested_job), instance, reexecution_options=options_upstream
    )
    assert result.success
    assert len(result.get_step_success_events()) == 3

    # two levels up downstream
    options_downstream = dg.ReexecutionOptions(
        parent_run_id=result.run_id, step_selection=["emit_one++"]
    )
    result = dg.execute_job(
        dg.reconstructable(highly_nested_job), instance, reexecution_options=options_downstream
    )
    assert result.success
    assert len(result.get_step_success_events()) == 3

    # combine overlapping step selections
    options_overlap = dg.ReexecutionOptions(
        parent_run_id=result.run_id, step_selection=["++add_one_outer", "emit_one++"]
    )
    result = dg.execute_job(
        dg.reconstructable(highly_nested_job), instance, reexecution_options=options_overlap
    )
    assert result.success
    assert len(result.get_step_success_events()) == 4


def get_asset_job():
    @dg.asset
    def downstream_asset(upstream_asset):
        return upstream_asset

    @dg.asset
    def upstream_asset():
        return 5

    the_job = dg.define_asset_job(name="the_job", selection=["downstream_asset", "upstream_asset"])

    @dg.repository
    def the_repo():
        return [the_job, downstream_asset, upstream_asset]

    job_def = the_repo.get_job("the_job")
    return job_def


def test_asset_selection():
    with dg.instance_for_test() as instance:
        result = dg.execute_job(
            dg.reconstructable(get_asset_job),
            instance,
            asset_selection=[dg.AssetKey("upstream_asset")],
        )
        assert result.success
        assert len(result.get_step_success_events()) == 1
        assert result.get_step_success_events()[0].step_key == "upstream_asset"


@dg.op(out={"a": dg.Out(is_required=False), "b": dg.Out(is_required=False)})
def a_or_b():
    yield dg.Output("wow", "a")


@dg.op
def echo(x):
    return x


@dg.op
def fail_once(context: OpExecutionContext, x):
    key = context.op_handle.name
    if context.instance.run_storage.get_cursor_values({key}).get(key):
        return x
    context.instance.run_storage.set_cursor_values({key: "true"})
    raise Exception("failed (just this once)")


@dg.job(executor_def=in_process_executor)
def branching_job():
    a, b = a_or_b()
    echo(
        [
            fail_once.alias("fail_once_a")(a),
            fail_once.alias("fail_once_b")(b),
        ]
    )


def test_branching():
    with dg.instance_for_test() as instance:
        result = dg.execute_job(dg.reconstructable(branching_job), instance)
        assert not result.success

        result_2 = dg.execute_job(
            dg.reconstructable(branching_job),
            instance,
            reexecution_options=ReexecutionOptions.from_failure(result.run_id, instance),
        )
        assert result_2.success
        success_steps = {ev.step_key for ev in result_2.get_step_success_events()}
        assert success_steps == {"fail_once_a", "echo"}

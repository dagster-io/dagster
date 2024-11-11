import pytest
from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    Definitions,
    ExecuteInProcessResult,
    MaterializeResult,
    OpExecutionContext,
    asset,
    asset_check,
    instance_for_test,
    job,
    load_assets_from_current_module,
    multi_asset,
    op,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.compute import AssetCheckExecutionContext
from dagster_pipes import DagsterPipesError, PipesContext

from dagster_tests.execution_tests.pipes_tests.in_process_client import InProcessPipesClient


def execute_asset_through_def(assets_def, resources) -> ExecuteInProcessResult:
    return (
        Definitions(assets=[assets_def], resources={"inprocess_client": InProcessPipesClient()})
        .get_implicit_global_asset_job_def()
        .execute_in_process()
    )


def test_op() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.log.info("hello")
        called["yes"] = True

    @op
    def an_op(context: OpExecutionContext, inprocess_client: InProcessPipesClient):
        return inprocess_client.run(context=context, fn=_impl).get_results()

    @job
    def a_job():
        an_op()

    with instance_for_test() as instance:
        result = a_job.execute_in_process(
            resources={"inprocess_client": InProcessPipesClient()}, instance=instance
        )
    assert called["yes"]
    assert result.success


def test_basic_materialization() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_materialization(metadata={"some_key": "some_value"})
        called["yes"] = True

    @asset
    def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient):
        return inprocess_client.run(
            context=context, fn=_impl, metadata={"extra_key": "value"}
        ).get_results()

    result = execute_asset_through_def(
        an_asset, resources={"inprocess_client": InProcessPipesClient()}
    )
    assert called["yes"]
    assert result.success
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    assert mat_events[0].materialization.metadata["some_key"].value == "some_value"
    assert mat_events[0].materialization.metadata["extra_key"].value == "value"


def test_implicit_materialization() -> None:
    called = {}

    def _impl(context: PipesContext):
        called["yes"] = True

    @asset
    def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient):
        return inprocess_client.run(
            context=context, fn=_impl, metadata={"extra_key": "value"}
        ).get_results()

    result = execute_asset_through_def(
        an_asset, resources={"inprocess_client": InProcessPipesClient()}
    )
    assert called["yes"]
    assert result.success
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    assert mat_events[0].materialization.metadata["extra_key"].value == "value"


def test_get_materialize_result() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_materialization(metadata={"some_key": "some_value"})
        called["yes"] = True

    @asset
    def an_asset(
        context: AssetExecutionContext, inprocess_client: InProcessPipesClient
    ) -> MaterializeResult:
        return inprocess_client.run(
            context=context, fn=_impl, metadata={"extra_metadata": "my_value"}
        ).get_materialize_result()

    result = execute_asset_through_def(
        an_asset, resources={"inprocess_client": InProcessPipesClient()}
    )
    assert result.success
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    assert mat_events[0].materialization.metadata["some_key"].value == "some_value"
    assert mat_events[0].materialization.metadata["extra_metadata"].value == "my_value"
    assert called["yes"]


@asset(
    key=["key0"],
    check_specs=[
        AssetCheckSpec(name="check_one", asset="key0"),
    ],
)
def key_will_contain_slashes_implicit(
    context: AssetExecutionContext, inprocess_client: InProcessPipesClient
):
    def _impl(context: PipesContext):
        context.report_asset_materialization(
            metadata={"some_key": "some_value"},
        )

        context.report_asset_check("check_one", passed=True, metadata={"key_one": "value_one"})

    mat_result = inprocess_client.run(context=context, fn=_impl).get_materialize_result()

    check_result_one = mat_result.check_result_named("check_one")
    assert check_result_one.passed is True
    assert check_result_one.metadata["key_one"].value == "value_one"

    return mat_result


def test_asset_key_with_slashes_implicit() -> None:
    all_assets = load_assets_from_current_module(key_prefix="foo/bar")
    an_asset_with_slash = next(a for a in all_assets if a.key == AssetKey(["foo/bar", "key0"]))  # type: ignore

    result = execute_asset_through_def(
        an_asset_with_slash, resources={"inprocess_client": InProcessPipesClient()}
    )
    assert result.success
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    assert mat_events[0].materialization.metadata["some_key"].value == "some_value"


@asset(
    key=["key1"],
    check_specs=[
        AssetCheckSpec(name="check_one", asset="key1"),
    ],
)
def key_will_contain_slashes_explicit(
    context: AssetExecutionContext, inprocess_client: InProcessPipesClient
):
    def _impl(context: PipesContext):
        context.report_asset_materialization(
            metadata={"some_key": "some_value"}, asset_key=r"foo\/bar/key1"
        )

        context.report_asset_check(
            "check_one", passed=True, asset_key=r"foo\/bar/key1", metadata={"key_one": "value_one"}
        )

    mat_result = inprocess_client.run(context=context, fn=_impl).get_materialize_result()

    check_result_one = mat_result.check_result_named("check_one")
    assert check_result_one.passed is True
    assert check_result_one.metadata["key_one"].value == "value_one"

    return mat_result


def test_asset_key_with_slashes_explicit() -> None:
    all_assets = load_assets_from_current_module(key_prefix="foo/bar")
    an_asset_with_slash = next(a for a in all_assets if a.key == AssetKey(["foo/bar", "key1"]))  # type: ignore

    result = execute_asset_through_def(
        an_asset_with_slash, resources={"inprocess_client": InProcessPipesClient()}
    )
    assert result.success
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    assert mat_events[0].materialization.metadata["some_key"].value == "some_value"


def test_get_double_report_error() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_materialization(asset_key="one", metadata={"some_key": "some_value"})
        context.report_asset_materialization(asset_key="two", metadata={"some_key": "some_value"})
        called["yes"] = True

    @asset
    def an_asset(
        context: AssetExecutionContext, inprocess_client: InProcessPipesClient
    ) -> MaterializeResult:
        return inprocess_client.run(context=context, fn=_impl).get_materialize_result()

    with pytest.raises(DagsterPipesError) as exc_info:
        execute_asset_through_def(an_asset, resources={"inprocess_client": InProcessPipesClient()})

    assert "Invalid asset key." in str(exc_info.value)


def test_multi_asset_get_materialize_result_error() -> None:
    called = {}

    def _impl(context: PipesContext):
        called["yes"] = True
        pass

    @multi_asset(specs=[AssetSpec(key="one"), AssetSpec(key="two")])
    def some_assets(context: AssetExecutionContext, inprocess_client: InProcessPipesClient):
        inprocess_client.run(context=context, fn=_impl).get_materialize_result()

    with pytest.raises(DagsterPipesError) as exc_info:
        execute_asset_through_def(
            some_assets, resources={"inprocess_client": InProcessPipesClient()}
        )

    assert (
        "Multiple materialize results returned with asset keys ['one', 'two']. If you are"
        " materializing multiple assets in a pipes invocation, use get_results() instead."
        in str(exc_info.value)
    )
    assert called["yes"]


def test_with_asset_checks() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_materialization(metadata={"some_key": "some_value"})
        context.report_asset_check(
            check_name="check_one", passed=True, severity="ERROR", metadata={"key_one": "value_one"}
        )
        context.report_asset_check(
            check_name="check_two", passed=False, severity="WARN", metadata={"key_two": "value_two"}
        )

    @asset(
        check_specs=[
            AssetCheckSpec(name="check_one", asset="an_asset"),
            AssetCheckSpec(name="check_two", asset="an_asset"),
        ]
    )
    # Bug in MaterializeResult type inference
    # def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient) -> MaterializeResult:
    def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient):
        mat_result = inprocess_client.run(
            context=context, fn=_impl, metadata={"extra_metadata": "my_value"}
        ).get_materialize_result()
        assert len(mat_result.check_results) == 2

        check_result_one = mat_result.check_result_named("check_one")
        assert check_result_one.passed is True
        assert check_result_one.severity == AssetCheckSeverity.ERROR
        assert check_result_one.metadata["key_one"].value == "value_one"
        assert check_result_one.metadata["extra_metadata"].value == "my_value"

        check_result_two = mat_result.check_result_named("check_two")
        assert check_result_two.passed is False
        assert check_result_two.severity == AssetCheckSeverity.WARN
        assert check_result_two.metadata["key_two"].value == "value_two"
        assert check_result_two.metadata["extra_metadata"].value == "my_value"

        called["yes"] = True
        return mat_result

    result = execute_asset_through_def(
        an_asset, resources={"inprocess_client": InProcessPipesClient()}
    )
    assert called["yes"]
    assert result.success


def test_wrong_asset_check_name() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_check(check_name="wrong_name", passed=True)

    @asset(
        check_specs=[
            AssetCheckSpec(name="check_one", asset="an_asset"),
        ]
    )
    # Bug in MaterializeResult type inference
    # def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient) -> MaterializeResult:
    def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient):
        mat_result = inprocess_client.run(context=context, fn=_impl).get_materialize_result()
        called["yes"] = True
        return mat_result

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_asset_through_def(an_asset, resources={"inprocess_client": InProcessPipesClient()})
    assert (
        "Received unexpected AssetCheckResult. No checks currently being evaluated target asset"
        " 'an_asset' and have name 'wrong_name'" in str(exc_info.value)
    )
    assert called["yes"]


def test_forget_to_return_materialize_result() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_materialization(metadata={"some_key": "some_value"})
        called["yes"] = True

    @asset
    def an_asset(context: AssetExecutionContext, inprocess_client: InProcessPipesClient):
        inprocess_client.run(context=context, fn=_impl).get_materialize_result()

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_asset_through_def(an_asset, resources={"inprocess_client": InProcessPipesClient()})

    assert "op 'an_asset' did not yield or return expected outputs {'result'}" in str(
        exc_info.value
    )
    assert (
        "If using `<PipesClient>.run`, you should always return"
        " `<PipesClient>.run(...).get_results()` or"
        " `<PipesClient>.run(...).get_materialize_result()" in str(exc_info.value)
    )


def test_get_asset_check_result() -> None:
    called = {}

    def _impl(context: PipesContext):
        context.report_asset_check(
            check_name="an_asset_check",
            asset_key="an_asset",
            passed=True,
            metadata={"some_key": "some_value"},
        )
        called["yes"] = True

    @asset_check(asset="an_asset")
    def an_asset_check(
        context: AssetCheckExecutionContext, inprocess_client: InProcessPipesClient
    ) -> AssetCheckResult:
        return inprocess_client.run(
            context=context.op_execution_context, fn=_impl
        ).get_asset_check_result()

    result = (
        Definitions(
            asset_checks=[an_asset_check],
            resources={"inprocess_client": InProcessPipesClient()},
        )
        .get_implicit_global_asset_job_def()
        .execute_in_process()
    )
    assert result.success
    chk_events = result.get_asset_check_evaluations()
    assert len(chk_events) == 1
    assert chk_events[0].metadata["some_key"].value == "some_value"
    assert called["yes"]

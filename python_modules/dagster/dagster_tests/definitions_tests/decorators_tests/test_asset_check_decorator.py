import re
from collections.abc import Iterable
from typing import Any, NamedTuple, Optional

import dagster as dg
import pytest
from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetKey,
    AssetSelection,
    DagsterEventType,
    DagsterInstance,
    Definitions,
    ExecuteInProcessResult,
    MetadataValue,
    _check as check,
)
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import AssetCheckExecutionContext
from dagster._utils.error import SerializableErrorInfo


def execute_assets_and_checks(
    assets=None,
    asset_checks=None,
    raise_on_error: bool = True,
    resources=None,
    instance=None,
    selection: Optional[dg.AssetSelection] = None,
) -> dg.ExecuteInProcessResult:
    defs = dg.Definitions(
        assets=assets,
        asset_checks=asset_checks,
        resources=resources,
        jobs=[
            dg.define_asset_job(
                "job1",
                selection=selection or (AssetSelection.all() | AssetSelection.all_asset_checks()),
            )
        ],
    )
    job_def = defs.resolve_job_def("job1")
    return job_def.execute_in_process(raise_on_error=raise_on_error, instance=instance)


def test_asset_check_decorator() -> None:
    @dg.asset_check(asset="asset1", description="desc", metadata={"foo": "bar"})
    def check1() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    spec = check1.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert spec.name == "check1"
    assert spec.description == "desc"
    assert spec.asset_key == dg.AssetKey("asset1")
    assert spec.metadata == {"foo": "bar"}


def test_asset_check_decorator_name() -> None:
    @dg.asset_check(asset="asset1", description="desc", name="check1")
    def _check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    spec = _check.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert spec.name == "check1"


def test_asset_check_decorator_docstring_description() -> None:
    @dg.asset_check(asset="asset1")  # pyright: ignore[reportArgumentType]
    def check1():
        """Docstring."""
        pass

    assert (
        check1.get_spec_for_check_key(
            dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1")
        ).description
        == "Docstring."
    )


def test_asset_check_decorator_parameter_description() -> None:
    @dg.asset_check(asset="asset1", description="parameter")  # pyright: ignore[reportArgumentType]
    def check1():
        """Docstring."""

    assert (
        check1.get_spec_for_check_key(
            dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1")
        ).description
        == "parameter"
    )


def test_asset_check_with_prefix() -> None:
    @dg.asset(key_prefix="prefix")
    def asset1() -> None: ...

    @dg.asset_check(asset=asset1)
    def my_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    spec = my_check.get_spec_for_check_key(
        dg.AssetCheckKey(dg.AssetKey(["prefix", "asset1"]), "my_check")
    )
    assert spec.asset_key == dg.AssetKey(["prefix", "asset1"])


def test_asset_check_input() -> None:
    @dg.asset
    def asset1() -> int:
        return 5

    @dg.asset_check(asset=asset1)
    def my_check1(asset1: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=asset1 == 5)

    @dg.asset_check(asset=asset1)
    def my_check2(random_name: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=random_name == 5)

    @dg.asset_check(asset=asset1)
    def my_check3(context, random_name: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=random_name == 5)

    @dg.asset_check(asset=asset1)
    def my_check4(context, asset1: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=asset1 == 5)

    result = execute_assets_and_checks(
        assets=[asset1], asset_checks=[my_check1, my_check2, my_check3, my_check4]
    )

    assert result.success
    assert len(result.get_asset_check_evaluations()) == 4
    assert all(check.passed for check in result.get_asset_check_evaluations())


def test_asset_check_additional_ins() -> None:
    @dg.asset
    def asset1() -> int:
        return 5

    @dg.asset
    def asset2() -> int:
        return 4

    @dg.asset_check(asset=asset1, additional_ins={"asset2": dg.AssetIn(key=asset2.key)})
    def my_check(asset1: int, asset2: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=asset1 == 5 and asset2 == 4)

    assert my_check.keys_by_input_name == {
        "asset1": dg.AssetKey("asset1"),
        "asset2": dg.AssetKey("asset2"),
    }

    @dg.asset_check(asset=asset1, additional_ins={"asset2": dg.AssetIn(key=asset2.key)})
    def my_check2(asset2: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=asset2 == 4)

    assert my_check2.keys_by_input_name == {
        "asset1": dg.AssetKey("asset1"),
        "asset2": dg.AssetKey("asset2"),
    }

    @dg.asset_check(asset=asset1, additional_ins={"asset2": dg.AssetIn(key=asset2.key)})
    def my_check3(context, asset2: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=asset2 == 4)

    assert my_check3.keys_by_input_name == {
        "asset1": dg.AssetKey("asset1"),
        "asset2": dg.AssetKey("asset2"),
    }

    # If the input name matches the asset key, then the asset in can be empty.
    @dg.asset_check(asset=asset1, additional_ins={"asset2": dg.AssetIn()})
    def my_check4(asset2: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=asset2 == 4)

    assert my_check4.keys_by_input_name == {
        "asset1": dg.AssetKey("asset1"),
        "asset2": dg.AssetKey("asset2"),
    }

    # Error bc asset2 is in additional_ins but not in the function signature
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset_check(asset=asset1, additional_ins={"asset2": dg.AssetIn(key=asset2.key)})
        def my_check4():
            return dg.AssetCheckResult(passed=True)

    # Error bc asset1 is in both additional_ins and the function signature
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset_check(asset=asset1, additional_ins={"asset1": dg.AssetIn(key=asset1.key)})
        def my_check5(asset1: int) -> dg.AssetCheckResult:
            return dg.AssetCheckResult(passed=asset1 == 5)

    # Error bc asset2 is in the function signature but not additional_ins
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset_check(asset=asset1, additional_ins={"asset2": dg.AssetIn(key=asset2.key)})
        def my_check6(asset1: int) -> dg.AssetCheckResult:
            return dg.AssetCheckResult(passed=asset1 == 5)

    result = execute_assets_and_checks(
        assets=[asset1, asset2], asset_checks=[my_check, my_check2, my_check3]
    )

    assert result.success
    assert len(result.get_asset_check_evaluations()) == 3
    assert all(check.passed for check in result.get_asset_check_evaluations())


def test_asset_check_input_with_prefix() -> None:
    @dg.asset(key_prefix="prefix")
    def asset1() -> int:
        return 5

    @dg.asset_check(asset=asset1)
    def my_check(unrelated_name: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=unrelated_name == 5)

    spec = my_check.get_spec_for_check_key(
        dg.AssetCheckKey(dg.AssetKey(["prefix", "asset1"]), "my_check")
    )
    assert spec.asset_key == dg.AssetKey(["prefix", "asset1"])

    result = execute_assets_and_checks(assets=[asset1], asset_checks=[my_check])
    assert result.success
    assert len(result.get_asset_check_evaluations()) == 1


def test_execute_asset_and_check() -> None:
    @dg.asset
    def asset1() -> None: ...

    @dg.asset_check(asset=asset1, description="desc")
    def check1(context: AssetCheckExecutionContext):
        assert context.op_execution_context.asset_key_for_input("asset1") == asset1.key
        return dg.AssetCheckResult(
            asset_key=asset1.key,
            check_name="check1",
            passed=True,
            metadata={"foo": "bar"},
        )

    instance = DagsterInstance.ephemeral()
    result = execute_assets_and_checks(assets=[asset1], asset_checks=[check1], instance=instance)
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == asset1.key
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}

    assert check_eval.target_materialization_data is not None
    assert check_eval.target_materialization_data.run_id == result.run_id
    materialization_record = instance.fetch_materializations(asset1.key, limit=1).records[0]
    assert check_eval.target_materialization_data.storage_id == materialization_record.storage_id
    assert check_eval.target_materialization_data.timestamp == materialization_record.timestamp

    assert (
        len(
            instance.get_records_for_run(
                result.run_id, of_type=DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED
            ).records
        )
        == 1
    )
    assert (
        len(
            instance.get_records_for_run(
                result.run_id, of_type=DagsterEventType.ASSET_CHECK_EVALUATION
            ).records
        )
        == 1
    )
    assert (
        len(
            instance.event_log_storage.get_asset_check_execution_history(
                dg.AssetCheckKey(asset_key=dg.AssetKey("asset1"), name="check1"), limit=10
            )
        )
        == 1
    )


def test_execute_check_without_asset() -> None:
    @dg.asset_check(asset="asset1", description="desc")
    def check1() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True, metadata={"foo": "bar"})

    result = execute_assets_and_checks(asset_checks=[check1])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}

    assert check_eval.target_materialization_data is None


def test_execute_check_and_asset_in_separate_run():
    @dg.asset
    def asset1(): ...

    @dg.asset_check(asset=asset1, description="desc")
    def check1(context: AssetCheckExecutionContext):
        assert context.op_execution_context.asset_key_for_input("asset1") == asset1.key
        return dg.AssetCheckResult(
            asset_key=asset1.key,
            check_name="check1",
            passed=True,
            metadata={"foo": "bar"},
        )

    instance = DagsterInstance.ephemeral()
    materialize_result = execute_assets_and_checks(assets=[asset1], instance=instance)

    result = execute_assets_and_checks(asset_checks=[check1], instance=instance)
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]

    assert check_eval.target_materialization_data is not None
    assert check_eval.target_materialization_data.run_id == materialize_result.run_id
    materialization_record = instance.fetch_materializations(asset1.key, limit=1).records[0]
    assert check_eval.target_materialization_data.storage_id == materialization_record.storage_id
    assert check_eval.target_materialization_data.timestamp == materialization_record.timestamp


def test_execute_check_and_unrelated_asset() -> None:
    @dg.asset
    def asset2() -> None: ...

    @dg.asset_check(asset="asset1", description="desc")
    def check1() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    result = execute_assets_and_checks(assets=[asset2], asset_checks=[check1])
    assert result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 1

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"


def test_check_doesnt_execute_if_asset_fails() -> None:
    check_executed = [False]

    @dg.asset
    def asset1() -> None:
        raise ValueError()

    @dg.asset_check(asset=asset1)
    def asset1_check(context: AssetCheckExecutionContext) -> dg.AssetCheckResult:
        check_executed[0] = True
        raise Exception("Should not execute")

    result = execute_assets_and_checks(
        assets=[asset1], asset_checks=[asset1_check], raise_on_error=False
    )
    assert not result.success

    assert not check_executed[0]


def test_check_decorator_unexpected_asset_key() -> None:
    @dg.asset_check(asset="asset1", description="desc")
    def asset1_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(asset_key=dg.AssetKey("asset2"), passed=True)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=re.escape(
            "Received unexpected AssetCheckResult. It targets asset 'asset2' which is not targeted"
            " by any of the checks currently being evaluated. Targeted assets: ['asset1']."
        ),
    ):
        execute_assets_and_checks(asset_checks=[asset1_check])


def test_asset_check_separate_op_downstream_still_executes() -> None:
    @dg.asset
    def asset1() -> None: ...

    @dg.asset_check(asset=asset1)
    def asset1_check(context) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=False)

    @dg.asset(deps=[asset1])
    def asset2() -> None: ...

    result = execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[asset1_check])
    assert result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "asset1_check"
    assert not check_eval.passed


def error_for_node(result: ExecuteInProcessResult, node_name: str) -> SerializableErrorInfo:
    failure_data = result.failure_data_for_node(node_name)
    assert failure_data
    assert failure_data.error
    return failure_data.error


def test_blocking_check_skip_downstream() -> None:
    @dg.asset
    def asset1() -> None: ...

    @dg.asset_check(asset=asset1, blocking=True)
    def check1(context) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=False)

    @dg.asset(deps=[asset1])
    def asset2() -> None: ...

    result = execute_assets_and_checks(
        assets=[asset1, asset2], asset_checks=[check1], raise_on_error=False
    )
    assert not result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 1

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert not check_eval.passed

    error = error_for_node(result, "asset1_check1")
    assert error.message.startswith(
        "dagster._core.errors.DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity:\nasset1: check1"
    )


def test_blocking_check_with_source_asset_fail() -> None:
    asset1 = dg.SourceAsset("asset1")

    @dg.asset_check(asset=asset1, blocking=True)
    def check1(context) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=False)

    @dg.asset(deps=[asset1])
    def asset2() -> None: ...

    result = execute_assets_and_checks(
        assets=[asset1, asset2], asset_checks=[check1], raise_on_error=False
    )
    assert not result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 0

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert not check_eval.passed

    error = error_for_node(result, "asset1_check1")
    assert error.message.startswith(
        "dagster._core.errors.DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity:\nasset1: check1"
    )


def test_error_severity_with_source_asset_success() -> None:
    asset1 = dg.SourceAsset("asset1", io_manager_key="asset1_io_manager")

    @dg.asset_check(asset=asset1)
    def check1(context) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True, severity=AssetCheckSeverity.ERROR)

    @dg.asset
    def asset2(asset1) -> None:
        assert asset1 == 5

    class MyIOManager(dg.IOManager):
        def load_input(self, context) -> int:
            return 5

        def handle_output(self, context, obj) -> None:
            raise NotImplementedError()

    result = execute_assets_and_checks(
        assets=[asset1, asset2],
        asset_checks=[check1],
        raise_on_error=False,
        resources={"asset1_io_manager": MyIOManager()},
    )
    assert result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 1

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert check_eval.passed


def test_definitions_conflicting_checks() -> None:
    def make_check() -> dg.AssetChecksDefinition:
        @dg.asset_check(asset="asset1")
        def check1(context) -> dg.AssetCheckResult: ...

        return check1

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Duplicate asset check key.+asset1.+check1",
    ):
        Definitions.validate_loadable(dg.Definitions(asset_checks=[make_check(), make_check()]))


def test_definitions_same_name_different_asset() -> None:
    def make_check_for_asset(asset_key: str):
        @dg.asset_check(asset=asset_key)
        def check1(context) -> dg.AssetCheckResult:
            return dg.AssetCheckResult(passed=True)

        return check1

    Definitions.validate_loadable(
        dg.Definitions(
            asset_checks=[make_check_for_asset("asset1"), make_check_for_asset("asset2")]
        )
    )


def test_definitions_same_asset_different_name() -> None:
    def make_check(check_name: str):
        @dg.asset_check(asset="asset1", name=check_name)
        def _check(context) -> dg.AssetCheckResult:
            return dg.AssetCheckResult(passed=True)

        return _check

    Definitions.validate_loadable(
        dg.Definitions(asset_checks=[make_check("check1"), make_check("check2")])
    )


def test_resource_params() -> None:
    class MyResource(NamedTuple):
        value: int

    @dg.asset_check(asset=dg.AssetKey("asset1"))
    def check1(my_resource: dg.ResourceParam[MyResource]):
        assert my_resource.value == 5
        return dg.AssetCheckResult(passed=True)

    execute_assets_and_checks(asset_checks=[check1], resources={"my_resource": MyResource(5)})


def test_resource_params_with_resource_defs() -> None:
    class MyResource(NamedTuple):
        value: int

    @dg.asset_check(asset=dg.AssetKey("asset1"), resource_defs={"my_resource": MyResource(5)})
    def check1(my_resource: dg.ResourceParam[MyResource]):
        assert my_resource.value == 5
        return dg.AssetCheckResult(passed=True)

    execute_assets_and_checks(asset_checks=[check1])


def test_required_resource_keys() -> None:
    @dg.asset
    def my_asset() -> None:
        pass

    @dg.asset_check(asset=my_asset, required_resource_keys={"my_resource"})
    def my_check(context) -> dg.AssetCheckResult:
        assert context.resources.my_resource == "foobar"
        return dg.AssetCheckResult(passed=True)

    execute_assets_and_checks(
        assets=[my_asset], asset_checks=[my_check], resources={"my_resource": "foobar"}
    )


def test_resource_definitions() -> None:
    @dg.asset
    def my_asset() -> None:
        pass

    class MyResource(dg.ConfigurableResource):
        name: str

    @dg.asset_check(asset=my_asset, resource_defs={"my_resource": MyResource(name="foobar")})
    def my_check(context: AssetCheckExecutionContext) -> dg.AssetCheckResult:
        assert context.resources.my_resource.name == "foobar"
        return dg.AssetCheckResult(passed=True)

    execute_assets_and_checks(assets=[my_asset], asset_checks=[my_check])


def test_resource_definitions_satisfy_required_keys() -> None:
    @dg.asset
    def my_asset() -> None:
        pass

    class MyResource(dg.ConfigurableResource):
        name: str

    @dg.asset_check(
        asset=my_asset,
        resource_defs={"my_resource": MyResource(name="foobar")},
        required_resource_keys={"my_resource"},
    )
    def my_check(context: AssetCheckExecutionContext):
        assert context.resources.my_resource.name == "foobar"
        return dg.AssetCheckResult(passed=True)

    execute_assets_and_checks(assets=[my_asset], asset_checks=[my_check])


def test_job_only_execute_checks_downstream_of_selected_assets() -> None:
    @dg.asset
    def asset1() -> None: ...

    @dg.asset
    def asset2() -> None: ...

    @dg.asset_check(asset=asset1)
    def check1() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=False)

    @dg.asset_check(asset=asset2)
    def check2() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=False)

    defs = dg.Definitions(
        assets=[asset1, asset2],
        asset_checks=[check1, check2],
        jobs=[dg.define_asset_job("job1", selection=[asset1])],
    )
    job_def = defs.resolve_job_def("job1")
    result = job_def.execute_in_process()
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == asset1.key
    assert check_eval.check_name == "check1"


def test_asset_not_provided() -> None:
    with pytest.raises(Exception):
        # testing case that fails typechecking
        @dg.asset_check(description="desc")  # type: ignore
        def check1() -> dg.AssetCheckResult: ...


def test_managed_input() -> None:
    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset_check(asset=asset1, description="desc")
    def check1(asset1) -> dg.AssetCheckResult:
        assert asset1 == 4
        return dg.AssetCheckResult(passed=True)

    class MyIOManager(dg.IOManager):
        def load_input(self, context) -> int:
            assert context.asset_key == asset1.key
            return 4

        def handle_output(self, context, obj) -> None: ...

    spec = check1.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert spec.name == "check1"
    assert spec.asset_key == asset1.key

    assert execute_assets_and_checks(
        assets=[asset1], asset_checks=[check1], resources={"io_manager": MyIOManager()}
    ).success

    assert execute_assets_and_checks(
        assets=[asset1],
        asset_checks=[check1],
        resources={"io_manager": MyIOManager()},
        selection=AssetSelection.all_asset_checks(),
    ).success


def test_multiple_managed_inputs() -> None:
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "When defining check 'check1', multiple assets provided as parameters:"
            " ['asset1', 'asset2']. These should either match the target asset or be specified "
            "in 'additional_ins'."
        ),
    ):

        @dg.asset_check(asset="asset1", description="desc")
        def check1(asset1, asset2) -> dg.AssetCheckResult: ...


def test_managed_input_with_context() -> None:
    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset_check(asset=asset1, description="desc")
    def check1(context: AssetCheckExecutionContext, asset1):
        assert context
        assert asset1 == 4
        return dg.AssetCheckResult(passed=True)

    spec = check1.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert spec.name == "check1"
    assert spec.asset_key == asset1.key

    execute_assets_and_checks(assets=[asset1], asset_checks=[check1])


def test_doesnt_invoke_io_manager() -> None:
    class DummyIOManager(dg.IOManager):
        def handle_output(self, context, obj) -> None:
            assert False

        def load_input(self, context) -> None:
            assert False

    @dg.asset_check(asset="asset1", description="desc")
    def check1(context: AssetCheckExecutionContext):
        return dg.AssetCheckResult(passed=True)

    execute_assets_and_checks(asset_checks=[check1], resources={"io_manager": DummyIOManager()})


def assert_check_eval(
    check_eval,
    asset_key: AssetKey,
    check_name: str,
    passed: bool,
    run_id: str,
    instance: DagsterInstance,
):
    assert check_eval.asset_key == asset_key
    assert check_eval.check_name == check_name
    assert check_eval.passed == passed

    assert check_eval.target_materialization_data is not None
    assert check_eval.target_materialization_data.run_id == run_id
    materialization_record = instance.fetch_materializations(
        records_filter=asset_key, limit=1
    ).records[0]
    assert check_eval.target_materialization_data.storage_id == materialization_record.storage_id
    assert check_eval.target_materialization_data.timestamp == materialization_record.timestamp


def test_multi_asset_check() -> None:
    @dg.asset
    def asset1() -> None: ...

    @dg.asset
    def asset2() -> None: ...

    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec("check1", asset=asset1),
            dg.AssetCheckSpec("check2", asset=asset1),
            dg.AssetCheckSpec("check3", asset=asset2),
        ]
    )
    def checks(context) -> Iterable[dg.AssetCheckResult]:
        asset1_records = instance.fetch_materializations(asset1.key, limit=1000).records
        asset2_records = instance.fetch_materializations(asset2.key, limit=1000).records
        materialization_records = [*asset1_records, *asset2_records]
        assert len(materialization_records) == 2
        assert {record.asset_key for record in materialization_records} == {asset1.key, asset2.key}

        yield dg.AssetCheckResult(passed=True, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=False, asset_key="asset1", check_name="check2")
        yield dg.AssetCheckResult(passed=True, asset_key="asset2", check_name="check3")

    instance = DagsterInstance.ephemeral()
    result = execute_assets_and_checks(
        assets=[asset1, asset2],
        asset_checks=[checks],
        instance=instance,
    )

    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 3

    assert_check_eval(check_evals[0], asset1.key, "check1", True, result.run_id, instance)
    assert_check_eval(check_evals[1], asset1.key, "check2", False, result.run_id, instance)
    assert_check_eval(check_evals[2], asset2.key, "check3", True, result.run_id, instance)

    assert (
        len(
            instance.get_records_for_run(
                result.run_id, of_type=DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED
            ).records
        )
        == 3
    )
    assert (
        len(
            instance.get_records_for_run(
                result.run_id, of_type=DagsterEventType.ASSET_CHECK_EVALUATION
            ).records
        )
        == 3
    )
    assert (
        len(
            instance.event_log_storage.get_asset_check_execution_history(
                dg.AssetCheckKey(asset_key=dg.AssetKey("asset1"), name="check1"), limit=10
            )
        )
        == 1
    )

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        execute_assets_and_checks(
            asset_checks=[checks],
            instance=instance,
            selection=AssetSelection.checks(dg.AssetCheckKey(asset2.key, "check3")),
        )


def test_multi_asset_check_subset() -> None:
    @dg.asset
    def asset1() -> None: ...

    @dg.asset
    def asset2() -> None: ...

    asset1_check1 = dg.AssetCheckSpec("check1", asset=asset1)
    asset2_check3 = dg.AssetCheckSpec("check3", asset=asset2)

    @dg.multi_asset_check(
        specs=[asset1_check1, dg.AssetCheckSpec("check2", asset=asset1), asset2_check3],
        can_subset=True,
    )
    def checks(context) -> Iterable[dg.AssetCheckResult]:
        assert context.selected_asset_check_keys == {asset1_check1.key, asset2_check3.key}

        yield dg.AssetCheckResult(passed=True, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=False, asset_key="asset2", check_name="check3")

    instance = DagsterInstance.ephemeral()
    result = execute_assets_and_checks(
        assets=[asset1, asset2],
        asset_checks=[checks],
        instance=instance,
        selection=AssetSelection.assets(asset1, asset2).without_checks()
        | AssetSelection.checks(
            dg.AssetCheckKey(asset1.key, "check1"), dg.AssetCheckKey(asset2.key, "check3")
        ),
    )

    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2

    assert_check_eval(check_evals[0], asset1.key, "check1", True, result.run_id, instance)
    assert_check_eval(check_evals[1], asset2.key, "check3", False, result.run_id, instance)

    assert (
        len(
            instance.get_records_for_run(
                result.run_id, of_type=DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED
            ).records
        )
        == 2
    )
    assert (
        len(
            instance.get_records_for_run(
                result.run_id, of_type=DagsterEventType.ASSET_CHECK_EVALUATION
            ).records
        )
        == 2
    )
    assert (
        len(
            instance.event_log_storage.get_asset_check_execution_history(
                dg.AssetCheckKey(asset_key=dg.AssetKey("asset1"), name="check1"), limit=10
            )
        )
        == 1
    )


def test_target_materialization_observable_source_asset() -> None:
    @dg.observable_source_asset
    def asset1() -> dg.ObserveResult:
        return dg.ObserveResult()

    @dg.asset_check(asset=asset1)
    def check1() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    result = execute_assets_and_checks(assets=[asset1], asset_checks=[check1])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"

    assert check_eval.target_materialization_data is None


def test_direct_invocation() -> None:
    @dg.asset_check(asset="asset1")
    def check1() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    result = check1()
    assert isinstance(result, dg.AssetCheckResult)
    assert result.passed


def test_direct_invocation_with_context() -> None:
    @dg.asset_check(asset="asset1")
    def check1(context) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    result = check1(dg.build_op_context())
    assert isinstance(result, dg.AssetCheckResult)
    assert result.passed


def test_direct_invocation_with_input() -> None:
    @dg.asset_check(asset="asset1")
    def check1(asset1) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    result = check1(5)
    assert isinstance(result, dg.AssetCheckResult)
    assert result.passed


def test_direct_invocation_with_context_and_input() -> None:
    @dg.asset_check(asset="asset1")
    def check1(context, asset1) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    result = check1(dg.build_op_context(), 5)
    assert isinstance(result, dg.AssetCheckResult)
    assert result.passed


def test_multi_check_direct_invocation() -> None:
    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec("check1", asset="asset1"),
            dg.AssetCheckSpec("check2", asset="asset1"),
            dg.AssetCheckSpec("check3", asset="asset2"),
        ]
    )
    def checks() -> Iterable[dg.AssetCheckResult]:
        yield dg.AssetCheckResult(passed=True, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=False, asset_key="asset1", check_name="check2")
        yield dg.AssetCheckResult(passed=True, asset_key="asset2")

    results = check.is_list(list(check.is_iterable(checks())), of_type=AssetCheckResult)
    assert len(results) == 3
    assert all(isinstance(result, dg.AssetCheckResult) for result in results)
    assert results[0].passed
    assert not results[1].passed
    assert results[2].passed


def test_direct_invocation_with_inputs() -> None:
    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset
    def asset2() -> int:
        return 5

    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec("check1", asset=asset1),
            dg.AssetCheckSpec("check2", asset=asset2),
        ]
    )
    def multi_check(asset1: int, asset2: int) -> Iterable[dg.AssetCheckResult]:
        yield dg.AssetCheckResult(passed=asset1 == 4, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=asset2 == 5, asset_key="asset2", check_name="check2")

    result = list(multi_check(4, 5))  # type: ignore
    assert len(result) == 2
    assert all(isinstance(r, dg.AssetCheckResult) for r in result)
    assert all(r.passed for r in result)


def test_direct_invocation_remapped_inputs() -> None:
    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset
    def asset2() -> int:
        return 5

    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec("check1", asset=asset1),
            dg.AssetCheckSpec("check2", asset=asset2),
        ],
        ins={"remapped": asset1.key},
    )
    def multi_check(remapped: int, asset2: int) -> Iterable[dg.AssetCheckResult]:
        yield dg.AssetCheckResult(passed=remapped == 4, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=asset2 == 5, asset_key="asset2", check_name="check2")

    result = list(multi_check(4, 5))  # type: ignore
    assert len(result) == 2
    assert all(isinstance(r, dg.AssetCheckResult) for r in result)
    assert all(r.passed for r in result)


def test_multi_check_asset_with_inferred_inputs() -> None:
    """Test automatic inference of asset inputs in a multi-check."""

    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset
    def asset2() -> int:
        return 5

    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec("check1", asset=asset1),
            dg.AssetCheckSpec("check2", asset=asset2),
        ]
    )
    def multi_check(asset1: int, asset2: int) -> Iterable[dg.AssetCheckResult]:
        yield dg.AssetCheckResult(passed=asset1 == 4, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=asset2 == 5, asset_key="asset2", check_name="check2")

    result = execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[multi_check])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    assert all(check_eval.passed for check_eval in check_evals)


def test_multi_check_input_remapping() -> None:
    """Test remapping an asset input to a different name in a multi-check."""

    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset
    def asset2() -> int:
        return 5

    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec("check1", asset=asset1),
            dg.AssetCheckSpec("check2", asset=asset2),
        ],
        ins={"remapped": asset1.key},
    )
    def multi_check(remapped: int, asset2: int) -> Iterable[dg.AssetCheckResult]:
        yield dg.AssetCheckResult(passed=remapped == 4, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=asset2 == 5, asset_key="asset2", check_name="check2")

    result = execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[multi_check])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    assert all(check_eval.passed for check_eval in check_evals)


def test_multi_check_input_remapping_with_context() -> None:
    """Test remapping an asset input to a different name in a multi-check."""

    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset
    def asset2() -> int:
        return 5

    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec("check1", asset=asset1),
            dg.AssetCheckSpec("check2", asset=asset2),
        ],
        ins={"remapped": asset1.key},
    )
    def multi_check(context, remapped: int, asset2: int) -> Iterable[dg.AssetCheckResult]:
        assert isinstance(context, dg.AssetCheckExecutionContext)
        yield dg.AssetCheckResult(passed=remapped == 4, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=asset2 == 5, asset_key="asset2", check_name="check2")

    result = execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[multi_check])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    assert all(check_eval.passed for check_eval in check_evals)


def test_input_manager_overrides_multi_asset_check_decorator() -> None:
    """Test overriding input manager key for a particular asset in a multi-check, ensure that it is correctly mapped."""

    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset
    def asset2() -> int:
        return 5

    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec("check1", asset=asset1),
            dg.AssetCheckSpec("check2", asset=asset2),
        ],
        ins={"asset1": dg.AssetIn(key="asset1", input_manager_key="override_manager")},
    )
    def my_check(asset1: int, asset2: int) -> Iterable[dg.AssetCheckResult]:
        yield dg.AssetCheckResult(passed=asset1 == 4, asset_key="asset1", check_name="check1")
        yield dg.AssetCheckResult(passed=asset2 == 5, asset_key="asset2", check_name="check2")

    called = []

    class MyIOManager(dg.IOManager):
        def load_input(self, context) -> int:
            called.append(context.asset_key)
            return 4

        def handle_output(self, context, obj) -> None:
            raise NotImplementedError()

    result = execute_assets_and_checks(
        assets=[asset1, asset2],
        asset_checks=[my_check],
        resources={"override_manager": MyIOManager()},
    )

    assert result.success
    assert called == [dg.AssetKey("asset1")]
    assert all(check_eval.passed for check_eval in result.get_asset_check_evaluations())


def test_nonsense_input_name() -> None:
    """Test a nonsensical input name in a multi-check."""

    @dg.asset
    def asset1() -> int:
        return 4

    @dg.asset
    def asset2() -> int:
        return 5

    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.multi_asset_check(
            specs=[
                dg.AssetCheckSpec("check1", asset=asset1),
                dg.AssetCheckSpec("check2", asset=asset2),
            ],
        )
        def my_check(nonsense: int, asset2: int):
            pass


def _assert_test_succeeded(res: Any) -> None:
    assert isinstance(res, dg.AssetCheckResult)
    assert res.passed


def test_asset_check_direct_invocation() -> None:
    @dg.asset
    def asset1() -> int:
        return 5

    @dg.asset_check(asset=asset1)
    def my_check1(asset1: int) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=asset1 == 5)

    _assert_test_succeeded(my_check1(asset1()))


def test_asset_check_direct_invocation_ctx() -> None:
    @dg.asset
    def asset1(context: AssetExecutionContext) -> int:
        assert context.asset_key == dg.AssetKey("asset1")
        return 5

    @dg.asset_check(asset=asset1)
    def my_check1(context: AssetCheckExecutionContext, asset1: int) -> dg.AssetCheckResult:
        assert context.selected_asset_check_keys == {
            dg.AssetCheckKey(dg.AssetKey("asset1"), "my_check1")
        }
        return dg.AssetCheckResult(passed=asset1 == 5)

    _assert_test_succeeded(
        my_check1(dg.build_asset_check_context(), asset1(dg.build_asset_context()))
    )


def test_asset_check_direct_invocation_resource() -> None:
    class MyResource(dg.ConfigurableResource):
        name: str

    @dg.asset
    def asset1(): ...

    @dg.asset_check(asset=asset1)
    def my_check1(my_resource: MyResource) -> dg.AssetCheckResult:
        assert my_resource.name == "my_resource"
        return dg.AssetCheckResult(passed=True)

    _assert_test_succeeded(
        my_check1(
            dg.build_asset_check_context(resources={"my_resource": MyResource(name="my_resource")})
        )
    )
    _assert_test_succeeded(my_check1(my_resource=MyResource(name="my_resource")))


def test_asset_check_direct_invocation_ctx_resource() -> None:
    class MyResource(dg.ConfigurableResource):
        name: str

    @dg.asset
    def asset1(): ...

    @dg.asset_check(asset=asset1)
    def my_check1(
        context: AssetCheckExecutionContext, my_resource: MyResource
    ) -> dg.AssetCheckResult:
        assert my_resource.name == "my_resource"
        return dg.AssetCheckResult(passed=True)

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        my_check1(dg.build_asset_check_context())

    _assert_test_succeeded(
        my_check1(
            dg.build_asset_check_context(resources={"my_resource": MyResource(name="my_resource")})
        )
    )
    _assert_test_succeeded(
        my_check1(dg.build_asset_check_context(), my_resource=MyResource(name="my_resource"))
    )


def test_asset_check_pool() -> None:
    @dg.asset
    def asset1() -> int:
        return 5

    @dg.asset_check(asset=asset1, pool="my_pool")
    def my_check1(asset1: int) -> dg.AssetCheckResult: ...

    assert my_check1.op.pool == "my_pool"


def test_multi_asset_check_pool() -> None:
    @dg.asset
    def asset1() -> int:
        return 5

    @dg.multi_asset_check(specs=[dg.AssetCheckSpec("check1", asset=asset1)], pool="my_pool")
    def my_check1(asset1: int) -> dg.AssetCheckResult: ...

    assert my_check1.op.pool == "my_pool"


def test_asset_check_with_mismatched_partitions_def() -> None:
    """Test that a partitioned asset check with a different partitions_def than its target asset raises an error."""
    daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")
    weekly_partitions = dg.WeeklyPartitionsDefinition(start_date="2024-01-01")

    @dg.asset(partitions_def=daily_partitions)
    def my_asset() -> None: ...
    @dg.asset_check(asset=my_asset, partitions_def=weekly_partitions)
    def my_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Asset check 'my_asset:my_check' targets asset 'my_asset' but has a different partitions definition",
    ):
        dg.Definitions.validate_loadable(dg.Definitions(assets=[my_asset], asset_checks=[my_check]))


def test_unpartitioned_check_on_partitioned_asset() -> None:
    """Test that an unpartitioned asset check can target a partitioned asset."""
    daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")

    @dg.asset(partitions_def=daily_partitions)
    def my_asset() -> None: ...
    @dg.asset_check(asset=my_asset)
    def my_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    # This should not raise an error - unpartitioned checks can target partitioned assets
    dg.Definitions.validate_loadable(dg.Definitions(assets=[my_asset], asset_checks=[my_check]))

import asyncio
from collections.abc import Generator
from typing import Any

import dagster as dg
import pytest
from dagster import AssetExecutionContext, InputContext, OutputContext
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus


def _exec_asset(asset_def, selection=None, partition_key=None, resources=None):
    result = dg.materialize(
        [asset_def], selection=selection, partition_key=partition_key, resources=resources
    )
    assert result.success
    return result.asset_materializations_for_node(asset_def.node_def.name)


def test_materialize_result_asset():
    @dg.asset
    def ret_untyped(context: AssetExecutionContext):
        return dg.MaterializeResult(
            metadata={"one": 1},
            tags={"foo": "bar"},
        )

    mats = _exec_asset(ret_untyped)
    assert len(mats) == 1, mats
    assert "one" in mats[0].metadata
    assert mats[0].tags
    assert mats[0].tags["foo"] == "bar"

    # key mismatch
    @dg.asset
    def ret_mismatch(context: AssetExecutionContext):
        return dg.MaterializeResult(
            asset_key="random",
            metadata={"one": 1},
        )

    # core execution
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        dg.materialize([ret_mismatch])

    # direct invocation
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        ret_mismatch(dg.build_asset_context())

    # tuple
    @dg.asset
    def ret_two():
        return dg.MaterializeResult(metadata={"one": 1}), dg.MaterializeResult(metadata={"two": 2})

    # core execution
    result = dg.materialize([ret_two])
    assert result.success

    # direct invocation
    direct_results = ret_two()
    assert len(direct_results) == 2  # pyright: ignore[reportArgumentType]


def test_return_materialization_with_asset_checks():
    with dg.instance_for_test() as instance:

        @dg.asset(
            check_specs=[dg.AssetCheckSpec(name="foo_check", asset=dg.AssetKey("ret_checks"))]
        )
        def ret_checks(context: AssetExecutionContext):
            return dg.MaterializeResult(
                check_results=[
                    dg.AssetCheckResult(check_name="foo_check", metadata={"one": 1}, passed=True)
                ]
            )

        # core execution
        dg.materialize([ret_checks], instance=instance)
        asset_check_executions = instance.event_log_storage.get_asset_check_execution_history(
            dg.AssetCheckKey(asset_key=ret_checks.key, name="foo_check"),
            limit=1,
        )
        assert len(asset_check_executions) == 1
        assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED

        # direct invocation
        context = dg.build_asset_context()
        direct_results = ret_checks(context)
        assert direct_results


def test_materialize_result_check_targets_current_materialization():
    with dg.instance_for_test() as instance:

        @dg.asset(check_specs=[dg.AssetCheckSpec(name="my_check", asset=dg.AssetKey("my_asset"))])
        def my_asset(context: AssetExecutionContext):
            return dg.MaterializeResult(
                check_results=[dg.AssetCheckResult(check_name="my_check", passed=True)]
            )

        # First materialization
        result1 = dg.materialize([my_asset], instance=instance)
        assert result1.success

        # Get first check evaluation
        check_evals1 = result1.get_asset_check_evaluations()
        assert len(check_evals1) == 1
        check_eval1 = check_evals1[0]

        # Get first materialization
        mat_record1 = instance.fetch_materializations(my_asset.key, limit=1).records[0]

        # Verify first check references first materialization
        assert check_eval1.target_materialization_data is not None
        assert check_eval1.target_materialization_data.storage_id == mat_record1.storage_id
        assert check_eval1.target_materialization_data.run_id == result1.run_id

        # Second materialization
        result2 = dg.materialize([my_asset], instance=instance)
        assert result2.success

        # Get second check evaluation
        check_evals2 = result2.get_asset_check_evaluations()
        assert len(check_evals2) == 1
        check_eval2 = check_evals2[0]

        # Get second materialization (most recent)
        mat_record2 = instance.fetch_materializations(my_asset.key, limit=1).records[0]

        # Verify we have a *new* materialization (different storage_id)
        assert mat_record2.storage_id != mat_record1.storage_id

        # Second check must reference *second* materialization, not first
        assert check_eval2.target_materialization_data is not None
        assert check_eval2.target_materialization_data.storage_id == mat_record2.storage_id, (
            "Check from run 2 should reference materialization from run 2, not run 1. "
        )
        assert check_eval2.target_materialization_data.storage_id != mat_record1.storage_id, (
            "Check should not reference old materialization"
        )
        assert check_eval2.target_materialization_data.run_id == result2.run_id


def test_multi_asset():
    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def outs_multi_asset():
        return dg.MaterializeResult(asset_key="one", metadata={"foo": "bar"}), dg.MaterializeResult(
            asset_key="two", metadata={"baz": "qux"}
        )

    assert dg.materialize([outs_multi_asset]).success

    res = outs_multi_asset()
    assert res[0].metadata["foo"] == "bar"  # pyright: ignore[reportIndexIssue]
    assert res[1].metadata["baz"] == "qux"  # pyright: ignore[reportIndexIssue]

    @dg.multi_asset(specs=[dg.AssetSpec(["prefix", "one"]), dg.AssetSpec(["prefix", "two"])])
    def specs_multi_asset():
        return dg.MaterializeResult(
            asset_key=["prefix", "one"], metadata={"foo": "bar"}
        ), dg.MaterializeResult(asset_key=["prefix", "two"], metadata={"baz": "qux"})

    assert dg.materialize([specs_multi_asset]).success

    res = specs_multi_asset()
    assert res[0].metadata["foo"] == "bar"  # pyright: ignore[reportIndexIssue]
    assert res[1].metadata["baz"] == "qux"  # pyright: ignore[reportIndexIssue]


def test_return_materialization_multi_asset():
    #
    # yield successful
    #
    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def multi():
        yield dg.MaterializeResult(
            asset_key="one",
            metadata={"one": 1},
        )
        yield dg.MaterializeResult(
            asset_key="two",
            metadata={"two": 2},
        )

    mats = _exec_asset(multi)

    assert len(mats) == 2, mats
    assert "one" in mats[0].metadata
    assert mats[0].tags
    assert "two" in mats[1].metadata
    assert mats[1].tags

    direct_results = list(multi())  # pyright: ignore[reportArgumentType]
    assert len(direct_results) == 2

    #
    # missing a non optional out
    #
    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def missing():
        yield dg.MaterializeResult(
            asset_key="one",
            metadata={"one": 1},
        )

    # currently a less than ideal error
    with pytest.raises(
        dg.DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "missing" did not return an output for non-optional output "two"'
        ),
    ):
        _exec_asset(missing)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match='Invocation of op "missing" did not return an output for non-optional output "two"',
    ):
        list(missing())  # pyright: ignore[reportArgumentType]

    #
    # missing asset_key
    #
    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def no_key():
        yield dg.MaterializeResult(
            metadata={"one": 1},
        )
        yield dg.MaterializeResult(
            metadata={"two": 2},
        )

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "MaterializeResult did not include asset_key and it can not be inferred. Specify which"
            " asset_key, options are:"
        ),
    ):
        _exec_asset(no_key)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "MaterializeResult did not include asset_key and it can not be inferred. Specify which"
            " asset_key, options are:"
        ),
    ):
        list(no_key())  # pyright: ignore[reportArgumentType]

    #
    # return tuple success
    #
    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def ret_multi():
        return (
            dg.MaterializeResult(
                asset_key="one",
                metadata={"one": 1},
            ),
            dg.MaterializeResult(
                asset_key="two",
                metadata={"two": 2},
            ),
        )

    mats = _exec_asset(ret_multi)

    assert len(mats) == 2, mats
    assert "one" in mats[0].metadata
    assert mats[0].tags
    assert "two" in mats[1].metadata
    assert mats[1].tags

    res = ret_multi()
    assert len(res) == 2  # pyright: ignore[reportArgumentType]

    #
    # return list error
    #
    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def ret_list():
        return [
            dg.MaterializeResult(
                asset_key="one",
                metadata={"one": 1},
            ),
            dg.MaterializeResult(
                asset_key="two",
                metadata={"two": 2},
            ),
        ]

    # not the best
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "When using multiple outputs, either yield each output, or return a tuple containing a"
            " value for each output."
        ),
    ):
        _exec_asset(ret_list)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "When using multiple outputs, either yield each output, or return a tuple containing a"
            " value for each output."
        ),
    ):
        ret_list()


def test_materialize_result_output_typing():
    # Test that the return annotation MaterializeResult is interpreted as a Nothing type, since we
    # coerce returned MaterializeResults to Output(None). Then tests that the I/O manager is not invoked.

    class TestingIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert False

    @dg.asset
    def asset_with_type_annotation() -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"foo": "bar"})

    mats = _exec_asset(asset_with_type_annotation, resources={"io_manager": TestingIOManager()})
    assert len(mats) == 1, mats
    assert "foo" in mats[0].metadata
    assert mats[0].metadata["foo"].value == "bar"

    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def multi_asset_with_outs_and_type_annotation() -> tuple[
        dg.MaterializeResult, dg.MaterializeResult
    ]:
        return dg.MaterializeResult(asset_key="one"), dg.MaterializeResult(asset_key="two")

    _exec_asset(
        multi_asset_with_outs_and_type_annotation, resources={"io_manager": TestingIOManager()}
    )

    @dg.multi_asset(specs=[dg.AssetSpec("one"), dg.AssetSpec("two")])
    def multi_asset_with_specs_and_type_annotation() -> tuple[
        dg.MaterializeResult, dg.MaterializeResult
    ]:
        return dg.MaterializeResult(asset_key="one"), dg.MaterializeResult(asset_key="two")

    _exec_asset(
        multi_asset_with_specs_and_type_annotation, resources={"io_manager": TestingIOManager()}
    )

    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec(name="check_one", asset="with_checks"),
            dg.AssetCheckSpec(name="check_two", asset="with_checks"),
        ]
    )
    def with_checks(context: AssetExecutionContext) -> dg.MaterializeResult:
        return dg.MaterializeResult(
            check_results=[
                dg.AssetCheckResult(
                    check_name="check_one",
                    passed=True,
                ),
                dg.AssetCheckResult(
                    check_name="check_two",
                    passed=True,
                ),
            ]
        )

    _exec_asset(
        with_checks,
        resources={"io_manager": TestingIOManager()},
    )

    @dg.multi_asset(
        specs=[
            dg.AssetSpec("asset_one"),
            dg.AssetSpec("asset_two"),
        ],
        check_specs=[
            dg.AssetCheckSpec(name="check_one", asset="asset_one"),
            dg.AssetCheckSpec(name="check_two", asset="asset_two"),
        ],
    )
    def multi_checks(
        context: AssetExecutionContext,
    ) -> tuple[dg.MaterializeResult, dg.MaterializeResult]:
        return dg.MaterializeResult(
            asset_key="asset_one",
            check_results=[
                dg.AssetCheckResult(
                    check_name="check_one",
                    passed=True,
                    asset_key="asset_one",
                ),
            ],
        ), dg.MaterializeResult(
            asset_key="asset_two",
            check_results=[
                dg.AssetCheckResult(
                    check_name="check_two",
                    passed=True,
                    asset_key="asset_two",
                ),
            ],
        )

    _exec_asset(
        multi_checks,
        resources={"io_manager": TestingIOManager()},
    )


def test_materialize_result_no_output_typing_does_not_call_io():
    """Returning MaterializeResult from a vanilla asset or a multi asset that does not use
    AssetSpecs AND with no return type annotation results in an Any typing type for the
    Output. In this case we do not call the IO manager.
    """

    class TestingIOManager(dg.IOManager):
        def __init__(self):
            self.handle_output_calls = 0
            self.handle_input_calls = 0

        def handle_output(self, context, obj):
            self.handle_output_calls += 1

        def load_input(self, context):
            self.load_input_calls += 1  # pyright: ignore[reportAttributeAccessIssue]

        def reset(self):
            self.handle_output_calls = 0
            self.handle_inputs_calls = 0

    io_mgr = TestingIOManager()

    @dg.asset
    def asset_without_type_annotation():
        return dg.MaterializeResult(metadata={"foo": "bar"})

    _exec_asset(asset_without_type_annotation, resources={"io_manager": io_mgr})
    assert io_mgr.handle_output_calls == 0

    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def multi_asset_with_outs():
        return dg.MaterializeResult(asset_key="one"), dg.MaterializeResult(asset_key="two")

    io_mgr.reset()
    _exec_asset(multi_asset_with_outs, resources={"io_manager": io_mgr})
    assert io_mgr.handle_output_calls == 0

    io_mgr.reset()

    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec(name="check_one", asset="with_checks"),
            dg.AssetCheckSpec(name="check_two", asset="with_checks"),
        ]
    )
    def with_checks(context: AssetExecutionContext):
        return dg.MaterializeResult(
            check_results=[
                dg.AssetCheckResult(
                    check_name="check_one",
                    passed=True,
                ),
                dg.AssetCheckResult(
                    check_name="check_two",
                    passed=True,
                ),
            ]
        )

    _exec_asset(
        with_checks,
        resources={"io_manager": io_mgr},
    )
    assert io_mgr.handle_output_calls == 0

    io_mgr.reset()

    @dg.asset
    def generator_asset() -> Generator[dg.MaterializeResult, None, None]:
        yield dg.MaterializeResult(metadata={"foo": "bar"})

    _exec_asset(generator_asset, resources={"io_manager": io_mgr})
    io_mgr.handle_output_calls == 0  # pyright: ignore[reportUnusedExpression]


def test_materialize_result_implicit_output_typing():
    # Test that returned MaterializeResults bypass the I/O manager when the return type is Nothing

    class TestingIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert False

    @dg.multi_asset(specs=[dg.AssetSpec("one"), dg.AssetSpec("two")])
    def multi_asset_with_specs():
        return dg.MaterializeResult(asset_key="one"), dg.MaterializeResult(asset_key="two")

    _exec_asset(multi_asset_with_specs, resources={"io_manager": TestingIOManager()})

    @dg.multi_asset(
        specs=[
            dg.AssetSpec("asset_one"),
            dg.AssetSpec("asset_two"),
        ],
        check_specs=[
            dg.AssetCheckSpec(name="check_one", asset="asset_one"),
            dg.AssetCheckSpec(name="check_two", asset="asset_two"),
        ],
    )
    def multi_checks(context: AssetExecutionContext):
        return dg.MaterializeResult(
            asset_key="asset_one",
            check_results=[
                dg.AssetCheckResult(
                    check_name="check_one",
                    passed=True,
                    asset_key="asset_one",
                ),
            ],
        ), dg.MaterializeResult(
            asset_key="asset_two",
            check_results=[
                dg.AssetCheckResult(
                    check_name="check_two",
                    passed=True,
                    asset_key="asset_two",
                ),
            ],
        )

    _exec_asset(
        multi_checks,
        resources={"io_manager": TestingIOManager()},
    )


def test_materialize_result_generators():
    @dg.asset
    def generator_asset() -> Generator[dg.MaterializeResult, None, None]:
        yield dg.MaterializeResult(metadata={"foo": "bar"})

    res = _exec_asset(generator_asset)
    assert len(res) == 1
    assert res[0].metadata["foo"].value == "bar"

    res = list(generator_asset())  # pyright: ignore[reportArgumentType]
    assert len(res) == 1
    assert res[0].metadata["foo"] == "bar"

    @dg.multi_asset(specs=[dg.AssetSpec("one"), dg.AssetSpec("two")])
    def generator_specs_multi_asset():
        yield dg.MaterializeResult(asset_key="one", metadata={"foo": "bar"})
        yield dg.MaterializeResult(asset_key="two", metadata={"baz": "qux"})

    res = _exec_asset(generator_specs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    res = list(generator_specs_multi_asset())  # pyright: ignore[reportArgumentType]
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()})
    def generator_outs_multi_asset():
        yield dg.MaterializeResult(asset_key="one", metadata={"foo": "bar"})
        yield dg.MaterializeResult(asset_key="two", metadata={"baz": "qux"})

    res = _exec_asset(generator_outs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    res = list(generator_outs_multi_asset())  # pyright: ignore[reportArgumentType]
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @dg.multi_asset(specs=[dg.AssetSpec("one"), dg.AssetSpec("two")])
    async def async_specs_multi_asset():
        return dg.MaterializeResult(asset_key="one", metadata={"foo": "bar"}), dg.MaterializeResult(
            asset_key="two", metadata={"baz": "qux"}
        )

    res = _exec_asset(async_specs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    res = asyncio.run(async_specs_multi_asset())  # pyright: ignore[reportArgumentType]
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @dg.multi_asset(specs=[dg.AssetSpec("one"), dg.AssetSpec("two")])
    async def async_gen_specs_multi_asset():
        yield dg.MaterializeResult(asset_key="one", metadata={"foo": "bar"})
        yield dg.MaterializeResult(asset_key="two", metadata={"baz": "qux"})

    res = _exec_asset(async_gen_specs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    async def _run_async_gen():
        results = []
        async for result in async_gen_specs_multi_asset():  # pyright: ignore[reportGeneralTypeIssues]
            results.append(result)
        return results

    res = asyncio.run(_run_async_gen())
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"


def test_materialize_result_with_partitions():
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["red", "blue", "yellow"]))
    def partitioned_asset(context: AssetExecutionContext) -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"key": context.partition_key})

    mats = _exec_asset(partitioned_asset, partition_key="red")
    assert len(mats) == 1, mats
    assert mats[0].metadata["key"].text == "red"


def test_materialize_result_with_partitions_direct_invocation():
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["red", "blue", "yellow"]))
    def partitioned_asset(context: AssetExecutionContext) -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"key": context.partition_key})

    context = dg.build_asset_context(partition_key="red")

    res = partitioned_asset(context)
    assert res.metadata["key"] == "red"  # pyright: ignore[reportAttributeAccessIssue]


def test_materialize_result_value():
    @dg.asset
    def asset_with_value():
        return dg.MaterializeResult(value="hello")

    result = dg.materialize([asset_with_value])

    assert result.success
    assert result.asset_value("asset_with_value") == "hello"


def test_materialize_result_value_explicit_any_no_value():
    class TestIOManager(dg.InMemoryIOManager):
        def handle_output(self, context: OutputContext, obj: Any):
            raise Exception("Should not be called")

    @dg.asset
    def explicit_any() -> Any:
        return dg.MaterializeResult()

    @dg.asset
    def explicit_result_any() -> dg.MaterializeResult[Any]:
        return dg.MaterializeResult()

    # arguably, this could result in the IOManager being called
    # with a value of None, but that is not the current behavior
    result = dg.materialize(
        [explicit_any, explicit_result_any], resources={"io_manager": TestIOManager()}
    )
    assert result.success


def test_materialize_result_value_annotated_no_type():
    @dg.asset
    def asset_with_value() -> dg.MaterializeResult:
        return dg.MaterializeResult(value="hello")

    result = dg.materialize([asset_with_value])

    assert result.success
    assert result.asset_value("asset_with_value") == "hello"


def test_materialize_result_value_annotated_explicit_type():
    @dg.asset
    def asset_with_value() -> dg.MaterializeResult[str]:
        return dg.MaterializeResult(value="hello")

    result = dg.materialize([asset_with_value])

    assert result.success
    assert result.asset_value("asset_with_value") == "hello"


def test_materialize_result_value_annotated_incorrect_type():
    @dg.asset
    def asset_with_value() -> dg.MaterializeResult[int]:
        return dg.MaterializeResult(value="hello")  # type: ignore

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        dg.materialize([asset_with_value])


def test_materialize_result_value_annotated_no_value():
    @dg.asset
    def asset_with_value() -> dg.MaterializeResult[int]:
        return dg.MaterializeResult()  # type: ignore

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        dg.materialize([asset_with_value])


def test_materialize_result_with_default_io_manager():
    @dg.asset
    def up():
        return dg.MaterializeResult(value="hello")

    @dg.asset(
        deps=[up],
    )
    def down(up: str):
        return dg.MaterializeResult(value=up + " world")

    result = dg.materialize(assets=[up, down])
    assert result.success
    assert result.asset_value("down") == "hello world"


def test_materialize_result_with_custom_io_manager_default_key():
    class CustomIOManager(dg.IOManager):
        def __init__(self):
            self._storage = {}

        def load_input(self, context: InputContext):
            return self._storage[context.asset_key]

        def handle_output(self, context: OutputContext, obj):
            self._storage[context.asset_key] = obj

    @dg.asset
    def up():
        return dg.MaterializeResult(value="hello")

    @dg.asset(
        deps=[up],
    )
    def down(up: str):
        return dg.MaterializeResult(value=up + " world")

    io_manager = CustomIOManager()
    result = dg.materialize(assets=[up, down], resources={"io_manager": io_manager})
    assert result.success
    assert result.asset_value("down") == "hello world"


def test_materialize_result_with_custom_io_manager_custom_key():
    class CustomIOManager(dg.IOManager):
        def __init__(self):
            self._storage = {}

        def load_input(self, context: InputContext):
            return self._storage[context.asset_key]

        def handle_output(self, context: OutputContext, obj):
            self._storage[context.asset_key] = obj

    @dg.asset(io_manager_key="io_whatever_manager")
    def up():
        return dg.MaterializeResult(value="hello")

    @dg.asset(
        deps=[up],
        io_manager_key="io_whatever_manager",
    )
    def down(up: str):
        return dg.MaterializeResult(value=up + " world")

    io_manager = CustomIOManager()
    result = dg.materialize(assets=[up, down], resources={"io_whatever_manager": io_manager})
    assert result.success
    assert result.asset_value("down") == "hello world"


def test_materialize_result_with_asset_key_ref():
    @dg.asset
    def up():
        return dg.MaterializeResult(value="hello")

    @dg.asset(
        deps=["up"],
    )
    def down(up: str):
        return dg.MaterializeResult(value=up + " world")

    result = dg.materialize(assets=[up, down])
    assert result.success
    assert result.asset_value("down") == "hello world"


def test_materialize_result_with_custom_io_manager_type_mutate():
    class CustomIOManager(dg.IOManager):
        def __init__(self):
            self._storage = {}

        def load_input(self, context: InputContext):
            return self._storage[context.asset_key]

        def handle_output(self, context: OutputContext, obj):
            self._storage[context.asset_key] = obj

    @dg.asset
    def up():
        # Not generically typed for now
        return dg.MaterializeResult(value=1)

    @dg.asset(
        deps=[up],
    )
    def down(up: int):
        # Not generically typed for now
        return dg.MaterializeResult(value=up + 1)

    io_manager = CustomIOManager()
    result = dg.materialize(assets=[up, down], resources={"io_manager": io_manager})
    assert result.success
    assert result.asset_value("down") == 2


def test_multi_asset_with_asset_spec_io_manager():
    class CustomIOManager(dg.IOManager):
        def __init__(self):
            self._storage = {}

        def load_input(self, context: InputContext):
            return self._storage[context.asset_key]

        def handle_output(self, context: OutputContext, obj):
            self._storage[context.asset_key] = obj

    @dg.multi_asset(specs=[dg.AssetSpec("one").with_io_manager_key("custom_io_manager")])
    def multi_asset_one(context: AssetExecutionContext):
        return dg.MaterializeResult(value="hello")

    @dg.multi_asset(
        specs=[
            dg.AssetSpec("two", deps=["one"]).with_io_manager_key("custom_io_manager"),
        ],
    )
    def multi_asset_two(context: AssetExecutionContext, one: str):
        return dg.MaterializeResult(value=one + " world")

    io_manager = CustomIOManager()
    result = dg.materialize(
        assets=[multi_asset_one, multi_asset_two], resources={"custom_io_manager": io_manager}
    )
    assert result.success
    assert result.asset_value("two") == "hello world"

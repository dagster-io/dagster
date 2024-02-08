import asyncio
from typing import Generator, Tuple

import pytest
from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    AssetSpec,
    IOManager,
    StaticPartitionsDefinition,
    asset,
    build_op_context,
    instance_for_test,
    materialize,
    multi_asset,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_spec import (
    AssetExecutionType,
)
from dagster._core.definitions.observe import observe
from dagster._core.definitions.result import ObserveResult
from dagster._core.errors import DagsterInvariantViolationError, DagsterStepOutputNotFoundError
from dagster._core.execution.context.invocation import build_asset_context
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus


def _exec_asset(asset_def, selection=None, partition_key=None):
    result = observe([asset_def], partition_key=partition_key)
    assert result.success
    return result.asset_observations_for_node(asset_def.node_def.name)


def test_observe_result_asset():
    @asset(_execution_type=AssetExecutionType.OBSERVATION)
    def ret_untyped(context: AssetExecutionContext):
        return ObserveResult(
            metadata={"one": 1},
        )

    observations = _exec_asset(ret_untyped)
    assert len(observations) == 1, observations
    assert "one" in observations[0].metadata

    # key mismatch
    @asset(_execution_type=AssetExecutionType.OBSERVATION)
    def ret_mismatch(context: AssetExecutionContext):
        return ObserveResult(
            asset_key="random",
            metadata={"one": 1},
        )

    # core execution
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        observe([ret_mismatch])

    # direct invocation
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        ret_mismatch(build_asset_context())

    # tuple
    @asset(_execution_type=AssetExecutionType.OBSERVATION)
    def ret_two():
        return ObserveResult(metadata={"one": 1}), ObserveResult(metadata={"two": 2})

    # core execution
    result = observe([ret_two])
    assert result.success

    # direct invocation
    direct_results = ret_two()
    assert len(direct_results) == 2


def test_return_observe_result_with_asset_checks():
    with instance_for_test() as instance:

        @asset(
            check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey("ret_checks"))],
            _execution_type=AssetExecutionType.OBSERVATION,
        )
        def ret_checks(context: AssetExecutionContext):
            return ObserveResult(
                check_results=[
                    AssetCheckResult(check_name="foo_check", metadata={"one": 1}, passed=True)
                ]
            )

        # core execution
        observe([ret_checks], instance=instance)
        asset_check_executions = instance.event_log_storage.get_asset_check_execution_history(
            AssetCheckKey(asset_key=ret_checks.key, name="foo_check"),
            limit=1,
        )
        assert len(asset_check_executions) == 1
        assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED

        # direct invocation
        context = build_asset_context()
        direct_results = ret_checks(context)
        assert direct_results


def test_multi_asset_observe_result():
    @multi_asset(
        outs={"one": AssetOut(), "two": AssetOut()}, _execution_type=AssetExecutionType.OBSERVATION
    )
    def outs_multi_asset():
        return ObserveResult(asset_key="one", metadata=({"foo": "bar"})), ObserveResult(
            asset_key="two", metadata={"baz": "qux"}
        )

    assert observe([outs_multi_asset]).success

    res = outs_multi_asset()
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @multi_asset(
        specs=[
            AssetSpec(["prefix", "one"]),
            AssetSpec(["prefix", "two"]),
        ],
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def specs_multi_asset():
        return ObserveResult(asset_key=["prefix", "one"], metadata={"foo": "bar"}), ObserveResult(
            asset_key=["prefix", "two"], metadata={"baz": "qux"}
        )

    assert observe([specs_multi_asset]).success

    res = specs_multi_asset()
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"


def test_yield_materialization_multi_asset():
    #
    # yield successful
    #
    @multi_asset(
        outs={"one": AssetOut(), "two": AssetOut()},
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def multi():
        yield ObserveResult(
            asset_key="one",
            metadata={"one": 1},
        )
        yield ObserveResult(
            asset_key="two",
            metadata={"two": 2},
        )

    mats = _exec_asset(multi)

    assert len(mats) == 2, mats
    assert "one" in mats[0].metadata
    assert "two" in mats[1].metadata

    direct_results = list(multi())
    assert len(direct_results) == 2

    #
    # missing a non optional out
    #
    @multi_asset(
        outs={"one": AssetOut(), "two": AssetOut()},
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def missing():
        yield ObserveResult(
            asset_key="one",
            metadata={"one": 1},
        )

    # currently a less than ideal error
    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "missing" did not return an output for non-optional output "two"'
        ),
    ):
        _exec_asset(missing)

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Invocation of op "missing" did not return an output for non-optional output "two"',
    ):
        list(missing())

    #
    # missing asset_key
    #
    @multi_asset(
        outs={"one": AssetOut(), "two": AssetOut()},
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def no_key():
        yield ObserveResult(
            metadata={"one": 1},
        )
        yield ObserveResult(
            metadata={"two": 2},
        )

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "ObserveResult did not include asset_key and it can not be inferred. Specify which"
            " asset_key, options are:"
        ),
    ):
        _exec_asset(no_key)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "ObserveResult did not include asset_key and it can not be inferred. Specify which"
            " asset_key, options are:"
        ),
    ):
        list(no_key())

    #
    # return tuple success
    #
    @multi_asset(
        outs={"one": AssetOut(), "two": AssetOut()},
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def ret_multi():
        return (
            ObserveResult(
                asset_key="one",
                metadata={"one": 1},
            ),
            ObserveResult(
                asset_key="two",
                metadata={"two": 2},
            ),
        )

    mats = _exec_asset(ret_multi)

    assert len(mats) == 2, mats
    assert "one" in mats[0].metadata
    assert "two" in mats[1].metadata

    res = ret_multi()
    assert len(res) == 2

    #
    # return list error
    #
    @multi_asset(
        outs={"one": AssetOut(), "two": AssetOut()},
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def ret_list():
        return [
            ObserveResult(
                asset_key="one",
                metadata={"one": 1},
            ),
            ObserveResult(
                asset_key="two",
                metadata={"two": 2},
            ),
        ]

    # not the best
    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "When using multiple outputs, either yield each output, or return a tuple containing a"
            " value for each output."
        ),
    ):
        _exec_asset(ret_list)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "When using multiple outputs, either yield each output, or return a tuple containing a"
            " value for each output."
        ),
    ):
        ret_list()


def test_observe_result_output_typing():
    # Test that the return annotation ObserveResult is interpreted as a Nothing type, since we
    # coerce returned ObserveResults to Output(None)

    class TestingIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.dagster_type.is_nothing
            return None

        def load_input(self, context):
            return 1

    @asset(_execution_type=AssetExecutionType.OBSERVATION)
    def asset_with_type_annotation() -> ObserveResult:
        return ObserveResult(metadata={"foo": "bar"})

    assert observe(
        [asset_with_type_annotation], resources={"io_manager": TestingIOManager()}
    ).success

    @multi_asset(
        outs={"one": AssetOut(), "two": AssetOut()},
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def multi_asset_with_outs_and_type_annotation() -> Tuple[ObserveResult, ObserveResult]:
        return ObserveResult(asset_key="one"), ObserveResult(asset_key="two")

    assert observe(
        [multi_asset_with_outs_and_type_annotation], resources={"io_manager": TestingIOManager()}
    ).success

    @multi_asset(
        specs=[
            AssetSpec(["one"]),
            AssetSpec(["two"]),
        ],
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def multi_asset_with_specs_and_type_annotation() -> Tuple[ObserveResult, ObserveResult]:
        return ObserveResult(asset_key="one"), ObserveResult(asset_key="two")

    assert observe(
        [multi_asset_with_specs_and_type_annotation], resources={"io_manager": TestingIOManager()}
    ).success

    @multi_asset(
        specs=[
            AssetSpec(["one"]),
            AssetSpec(["two"]),
        ],
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def multi_asset_with_specs_and_no_type_annotation():
        return ObserveResult(asset_key="one"), ObserveResult(asset_key="two")

    assert observe(
        [multi_asset_with_specs_and_no_type_annotation],
        resources={"io_manager": TestingIOManager()},
    ).success

    @asset(
        check_specs=[
            AssetCheckSpec(name="check_one", asset="with_checks"),
            AssetCheckSpec(name="check_two", asset="with_checks"),
        ],
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def with_checks(context: AssetExecutionContext) -> ObserveResult:
        return ObserveResult(
            check_results=[
                AssetCheckResult(
                    check_name="check_one",
                    passed=True,
                ),
                AssetCheckResult(
                    check_name="check_two",
                    passed=True,
                ),
            ]
        )

    assert materialize(
        [with_checks],
        resources={"io_manager": TestingIOManager()},
    ).success

    @multi_asset(
        specs=[
            AssetSpec("asset_one"),
            AssetSpec("asset_two"),
        ],
        check_specs=[
            AssetCheckSpec(name="check_one", asset="asset_one"),
            AssetCheckSpec(name="check_two", asset="asset_two"),
        ],
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def multi_checks(context: AssetExecutionContext) -> Tuple[ObserveResult, ObserveResult]:
        return ObserveResult(
            asset_key="asset_one",
            check_results=[
                AssetCheckResult(
                    check_name="check_one",
                    passed=True,
                    asset_key="asset_one",
                ),
            ],
        ), ObserveResult(
            asset_key="asset_two",
            check_results=[
                AssetCheckResult(
                    check_name="check_two",
                    passed=True,
                    asset_key="asset_two",
                ),
            ],
        )

    assert materialize(
        [multi_checks],
        resources={"io_manager": TestingIOManager()},
    ).success


@pytest.mark.skip(
    "Generator return types are interpreted as Any. See"
    " https://github.com/dagster-io/dagster/pull/16906"
)
def test_generator_return_type_annotation():
    class TestingIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.dagster_type.is_nothing
            return None

        def load_input(self, context):
            return 1

    @asset
    def generator_asset() -> Generator[ObserveResult, None, None]:
        yield ObserveResult(metadata={"foo": "bar"})

    materialize([generator_asset], resources={"io_manager": TestingIOManager()})


def test_observe_result_generators():
    @asset(_execution_type=AssetExecutionType.OBSERVATION)
    def generator_asset() -> Generator[ObserveResult, None, None]:
        yield ObserveResult(metadata={"foo": "bar"})

    res = _exec_asset(generator_asset)
    assert len(res) == 1
    assert res[0].metadata["foo"].value == "bar"

    res = list(generator_asset())
    assert len(res) == 1
    assert res[0].metadata["foo"] == "bar"

    @multi_asset(
        specs=[AssetSpec("one"), AssetSpec("two")],
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def generator_specs_multi_asset():
        yield ObserveResult(asset_key="one", metadata={"foo": "bar"})
        yield ObserveResult(asset_key="two", metadata={"baz": "qux"})

    res = _exec_asset(generator_specs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    res = list(generator_specs_multi_asset())
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @multi_asset(
        outs={"one": AssetOut(), "two": AssetOut()},
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def generator_outs_multi_asset():
        yield ObserveResult(asset_key="one", metadata={"foo": "bar"})
        yield ObserveResult(asset_key="two", metadata={"baz": "qux"})

    res = _exec_asset(generator_outs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    res = list(generator_outs_multi_asset())
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @multi_asset(
        specs=[AssetSpec("one"), AssetSpec("two")],
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    async def async_specs_multi_asset():
        return ObserveResult(asset_key="one", metadata={"foo": "bar"}), ObserveResult(
            asset_key="two", metadata={"baz": "qux"}
        )

    res = _exec_asset(async_specs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    res = asyncio.run(async_specs_multi_asset())
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @multi_asset(
        specs=[AssetSpec("one"), AssetSpec("two")],
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    async def async_gen_specs_multi_asset():
        yield ObserveResult(asset_key="one", metadata={"foo": "bar"})
        yield ObserveResult(asset_key="two", metadata={"baz": "qux"})

    res = _exec_asset(async_gen_specs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    async def _run_async_gen():
        results = []
        async for result in async_gen_specs_multi_asset():
            results.append(result)
        return results

    res = asyncio.run(_run_async_gen())
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"


def test_observe_result_with_partitions():
    @asset(
        partitions_def=StaticPartitionsDefinition(["red", "blue", "yellow"]),
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def partitioned_asset(context: AssetExecutionContext) -> ObserveResult:
        return ObserveResult(metadata={"key": context.partition_key})

    mats = _exec_asset(partitioned_asset, partition_key="red")
    assert len(mats) == 1, mats
    assert mats[0].metadata["key"].text == "red"


def test_observe_result_with_partitions_direct_invocation():
    @asset(
        partitions_def=StaticPartitionsDefinition(["red", "blue", "yellow"]),
        _execution_type=AssetExecutionType.OBSERVATION,
    )
    def partitioned_asset(context: AssetExecutionContext) -> ObserveResult:
        return ObserveResult(metadata={"key": context.partition_key})

    context = build_op_context(partition_key="red")

    res = partitioned_asset(context)
    assert res.metadata["key"] == "red"

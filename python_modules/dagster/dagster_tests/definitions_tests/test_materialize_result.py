import asyncio
from collections.abc import Generator, Iterator
from typing import Any

import pytest
from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    AssetSpec,
    InputContext,
    IOManager,
    MaterializeResult,
    OutputContext,
    StaticPartitionsDefinition,
    asset,
    instance_for_test,
    materialize,
    multi_asset,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.utils import NoValueSentinel
from dagster._core.errors import (
    DagsterInvariantViolationError,
    DagsterStepOutputNotFoundError,
    DagsterTypeCheckDidNotPass,
)
from dagster._core.execution.context.invocation import build_asset_context
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.mem_io_manager import InMemoryIOManager


def _exec_asset(asset_def, selection=None, partition_key=None, resources=None):
    result = materialize(
        [asset_def], selection=selection, partition_key=partition_key, resources=resources
    )
    assert result.success
    return result.asset_materializations_for_node(asset_def.node_def.name)


def test_materialize_result_asset():
    @asset
    def ret_untyped(context: AssetExecutionContext):
        return MaterializeResult(
            metadata={"one": 1},
            tags={"foo": "bar"},
        )

    mats = _exec_asset(ret_untyped)
    assert len(mats) == 1, mats
    assert "one" in mats[0].metadata
    assert mats[0].tags
    assert mats[0].tags["foo"] == "bar"

    # key mismatch
    @asset
    def ret_mismatch(context: AssetExecutionContext):
        return MaterializeResult(
            asset_key="random",
            metadata={"one": 1},
        )

    # core execution
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        materialize([ret_mismatch])

    # direct invocation
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        ret_mismatch(build_asset_context())

    # tuple
    @asset
    def ret_two():
        return MaterializeResult(metadata={"one": 1}), MaterializeResult(metadata={"two": 2})

    # core execution
    result = materialize([ret_two])
    assert result.success

    # direct invocation
    direct_results = ret_two()
    assert len(direct_results) == 2  # pyright: ignore[reportArgumentType]


def test_return_materialization_with_asset_checks():
    with instance_for_test() as instance:

        @asset(check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey("ret_checks"))])
        def ret_checks(context: AssetExecutionContext):
            return MaterializeResult(
                check_results=[
                    AssetCheckResult(check_name="foo_check", metadata={"one": 1}, passed=True)
                ]
            )

        # core execution
        materialize([ret_checks], instance=instance)
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


def test_multi_asset():
    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def outs_multi_asset():
        return MaterializeResult(asset_key="one", metadata={"foo": "bar"}), MaterializeResult(
            asset_key="two", metadata={"baz": "qux"}
        )

    assert materialize([outs_multi_asset]).success

    res = outs_multi_asset()
    assert res[0].metadata["foo"] == "bar"  # pyright: ignore[reportIndexIssue]
    assert res[1].metadata["baz"] == "qux"  # pyright: ignore[reportIndexIssue]

    @multi_asset(specs=[AssetSpec(["prefix", "one"]), AssetSpec(["prefix", "two"])])
    def specs_multi_asset():
        return MaterializeResult(
            asset_key=["prefix", "one"], metadata={"foo": "bar"}
        ), MaterializeResult(asset_key=["prefix", "two"], metadata={"baz": "qux"})

    assert materialize([specs_multi_asset]).success

    res = specs_multi_asset()
    assert res[0].metadata["foo"] == "bar"  # pyright: ignore[reportIndexIssue]
    assert res[1].metadata["baz"] == "qux"  # pyright: ignore[reportIndexIssue]


def test_return_materialization_multi_asset():
    #
    # yield successful
    #
    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def multi():
        yield MaterializeResult(
            asset_key="one",
            metadata={"one": 1},
        )
        yield MaterializeResult(
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
    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def missing():
        yield MaterializeResult(
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
        list(missing())  # pyright: ignore[reportArgumentType]

    #
    # missing asset_key
    #
    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def no_key():
        yield MaterializeResult(
            metadata={"one": 1},
        )
        yield MaterializeResult(
            metadata={"two": 2},
        )

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "MaterializeResult did not include asset_key and it can not be inferred. Specify which"
            " asset_key, options are:"
        ),
    ):
        _exec_asset(no_key)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "MaterializeResult did not include asset_key and it can not be inferred. Specify which"
            " asset_key, options are:"
        ),
    ):
        list(no_key())  # pyright: ignore[reportArgumentType]

    #
    # return tuple success
    #
    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def ret_multi():
        return (
            MaterializeResult(
                asset_key="one",
                metadata={"one": 1},
            ),
            MaterializeResult(
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
    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def ret_list():
        return [
            MaterializeResult(
                asset_key="one",
                metadata={"one": 1},
            ),
            MaterializeResult(
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


def test_materialize_result_output_typing():
    # Test that the return annotation MaterializeResult is interpreted as a Nothing type, since we
    # coerce returned MaterializeResults to Output(None). Then tests that the I/O manager is not invoked.

    class TestingIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert False

    @asset
    def asset_with_type_annotation() -> MaterializeResult:
        return MaterializeResult(metadata={"foo": "bar"})

    mats = _exec_asset(asset_with_type_annotation, resources={"io_manager": TestingIOManager()})
    assert len(mats) == 1, mats
    assert "foo" in mats[0].metadata
    assert mats[0].metadata["foo"].value == "bar"

    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def multi_asset_with_outs_and_type_annotation() -> tuple[MaterializeResult, MaterializeResult]:
        return MaterializeResult(asset_key="one"), MaterializeResult(asset_key="two")

    _exec_asset(
        multi_asset_with_outs_and_type_annotation, resources={"io_manager": TestingIOManager()}
    )

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs_and_type_annotation() -> tuple[MaterializeResult, MaterializeResult]:
        return MaterializeResult(asset_key="one"), MaterializeResult(asset_key="two")

    _exec_asset(
        multi_asset_with_specs_and_type_annotation, resources={"io_manager": TestingIOManager()}
    )

    @asset(
        check_specs=[
            AssetCheckSpec(name="check_one", asset="with_checks"),
            AssetCheckSpec(name="check_two", asset="with_checks"),
        ]
    )
    def with_checks(context: AssetExecutionContext) -> MaterializeResult:
        return MaterializeResult(
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

    _exec_asset(
        with_checks,
        resources={"io_manager": TestingIOManager()},
    )

    @multi_asset(
        specs=[
            AssetSpec("asset_one"),
            AssetSpec("asset_two"),
        ],
        check_specs=[
            AssetCheckSpec(name="check_one", asset="asset_one"),
            AssetCheckSpec(name="check_two", asset="asset_two"),
        ],
    )
    def multi_checks(context: AssetExecutionContext) -> tuple[MaterializeResult, MaterializeResult]:
        return MaterializeResult(
            asset_key="asset_one",
            check_results=[
                AssetCheckResult(
                    check_name="check_one",
                    passed=True,
                    asset_key="asset_one",
                ),
            ],
        ), MaterializeResult(
            asset_key="asset_two",
            check_results=[
                AssetCheckResult(
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

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs_and_iterator() -> Iterator[MaterializeResult]:
        yield MaterializeResult(asset_key="one")
        yield MaterializeResult(asset_key="two")

    _exec_asset(
        multi_asset_with_specs_and_iterator,
        resources={"io_manager": TestingIOManager()},
    )


def test_materialize_result_no_output_typing_does_not_call_io():
    """Returning MaterializeResult from a vanilla asset or a multi asset that does not use
    AssetSpecs AND with no return type annotation results in an Any typing type for the
    Output. In this case we do not call the IO manager.
    """

    class TestingIOManager(IOManager):
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

    @asset
    def asset_without_type_annotation():
        return MaterializeResult(metadata={"foo": "bar"})

    _exec_asset(asset_without_type_annotation, resources={"io_manager": io_mgr})
    assert io_mgr.handle_output_calls == 0

    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def multi_asset_with_outs():
        return MaterializeResult(asset_key="one"), MaterializeResult(asset_key="two")

    io_mgr.reset()
    _exec_asset(multi_asset_with_outs, resources={"io_manager": io_mgr})
    assert io_mgr.handle_output_calls == 0

    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def multi_asset_with_outs_generator():
        yield MaterializeResult(asset_key="one")
        yield MaterializeResult(asset_key="two")

    io_mgr.reset()
    _exec_asset(multi_asset_with_outs_generator, resources={"io_manager": io_mgr})
    assert io_mgr.handle_output_calls == 0

    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def multi_asset_with_outs_generator_annotated() -> Iterator[MaterializeResult]:
        yield MaterializeResult(asset_key="one")
        yield MaterializeResult(asset_key="two")

    io_mgr.reset()
    _exec_asset(multi_asset_with_outs_generator_annotated, resources={"io_manager": io_mgr})
    assert io_mgr.handle_output_calls == 0

    io_mgr.reset()

    @asset(
        check_specs=[
            AssetCheckSpec(name="check_one", asset="with_checks"),
            AssetCheckSpec(name="check_two", asset="with_checks"),
        ]
    )
    def with_checks(context: AssetExecutionContext):
        return MaterializeResult(
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

    _exec_asset(
        with_checks,
        resources={"io_manager": io_mgr},
    )
    assert io_mgr.handle_output_calls == 0

    io_mgr.reset()

    @asset
    def generator_asset() -> Generator[MaterializeResult, None, None]:
        yield MaterializeResult(metadata={"foo": "bar"})

    _exec_asset(generator_asset, resources={"io_manager": io_mgr})
    io_mgr.handle_output_calls == 0  # pyright: ignore[reportUnusedExpression]


def test_materialize_result_implicit_output_typing():
    # Test that returned MaterializeResults bypass the I/O manager when the return type is Nothing

    class TestingIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert False

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs():
        return MaterializeResult(asset_key="one"), MaterializeResult(asset_key="two")

    _exec_asset(multi_asset_with_specs, resources={"io_manager": TestingIOManager()})

    @multi_asset(
        specs=[
            AssetSpec("asset_one"),
            AssetSpec("asset_two"),
        ],
        check_specs=[
            AssetCheckSpec(name="check_one", asset="asset_one"),
            AssetCheckSpec(name="check_two", asset="asset_two"),
        ],
    )
    def multi_checks(context: AssetExecutionContext):
        return MaterializeResult(
            asset_key="asset_one",
            check_results=[
                AssetCheckResult(
                    check_name="check_one",
                    passed=True,
                    asset_key="asset_one",
                ),
            ],
        ), MaterializeResult(
            asset_key="asset_two",
            check_results=[
                AssetCheckResult(
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
    @asset
    def generator_asset() -> Generator[MaterializeResult, None, None]:
        yield MaterializeResult(metadata={"foo": "bar"})

    res = _exec_asset(generator_asset)
    assert len(res) == 1
    assert res[0].metadata["foo"].value == "bar"

    res = list(generator_asset())  # pyright: ignore[reportArgumentType]
    assert len(res) == 1
    assert res[0].metadata["foo"] == "bar"

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def generator_specs_multi_asset():
        yield MaterializeResult(asset_key="one", metadata={"foo": "bar"})
        yield MaterializeResult(asset_key="two", metadata={"baz": "qux"})

    res = _exec_asset(generator_specs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    res = list(generator_specs_multi_asset())  # pyright: ignore[reportArgumentType]
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def generator_outs_multi_asset():
        yield MaterializeResult(asset_key="one", metadata={"foo": "bar"})
        yield MaterializeResult(asset_key="two", metadata={"baz": "qux"})

    res = _exec_asset(generator_outs_multi_asset)
    assert len(res) == 2
    assert res[0].metadata["foo"].value == "bar"
    assert res[1].metadata["baz"].value == "qux"

    res = list(generator_outs_multi_asset())  # pyright: ignore[reportArgumentType]
    assert len(res) == 2
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    async def async_specs_multi_asset():
        return MaterializeResult(asset_key="one", metadata={"foo": "bar"}), MaterializeResult(
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

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    async def async_gen_specs_multi_asset():
        yield MaterializeResult(asset_key="one", metadata={"foo": "bar"})
        yield MaterializeResult(asset_key="two", metadata={"baz": "qux"})

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
    @asset(partitions_def=StaticPartitionsDefinition(["red", "blue", "yellow"]))
    def partitioned_asset(context: AssetExecutionContext) -> MaterializeResult:
        return MaterializeResult(metadata={"key": context.partition_key})

    mats = _exec_asset(partitioned_asset, partition_key="red")
    assert len(mats) == 1, mats
    assert mats[0].metadata["key"].text == "red"


def test_materialize_result_with_partitions_direct_invocation():
    @asset(partitions_def=StaticPartitionsDefinition(["red", "blue", "yellow"]))
    def partitioned_asset(context: AssetExecutionContext) -> MaterializeResult:
        return MaterializeResult(metadata={"key": context.partition_key})

    context = build_asset_context(partition_key="red")

    res = partitioned_asset(context)
    assert res.metadata["key"] == "red"  # pyright: ignore[reportAttributeAccessIssue]


def test_materialize_result_value():
    @asset
    def asset_with_value():
        return MaterializeResult(value="hello")

    result = materialize([asset_with_value])

    assert result.success
    assert result.asset_value("asset_with_value") == "hello"


def test_materialize_result_value_explicit_any_no_value():
    class TestIOManager(InMemoryIOManager):
        def handle_output(self, context: OutputContext, obj: Any):
            raise Exception("Should not be called")

    @asset
    def explicit_any() -> Any:
        return MaterializeResult()

    @asset
    def explicit_result_any() -> MaterializeResult[Any]:
        return MaterializeResult()

    # arguably, this could result in the IOManager being called
    # with a value of None, but that is not the current behavior
    result = materialize(
        [explicit_any, explicit_result_any], resources={"io_manager": TestIOManager()}
    )
    assert result.success


def test_materialize_result_value_annotated_no_type():
    @asset
    def asset_with_value() -> MaterializeResult:
        return MaterializeResult(value="hello")

    result = materialize([asset_with_value])

    assert result.success
    assert result.asset_value("asset_with_value") == "hello"


def test_materialize_result_value_annotated_explicit_type():
    @asset
    def asset_with_value() -> MaterializeResult[str]:
        return MaterializeResult(value="hello")

    result = materialize([asset_with_value])

    assert result.success
    assert result.asset_value("asset_with_value") == "hello"


def test_materialize_result_iterator_no_value():
    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs() -> Iterator[MaterializeResult]:
        yield MaterializeResult(asset_key="one")
        yield MaterializeResult(asset_key="two", value=2)

    result = materialize([multi_asset_with_specs])
    assert result.asset_value("one") == NoValueSentinel
    assert result.asset_value("two") == 2

    assert result.success


def test_materialize_result_iterator_value():
    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs() -> Iterator[MaterializeResult[str]]:
        yield MaterializeResult(asset_key="one", value="hello")
        yield MaterializeResult(asset_key="two", value="world")

    result = materialize([multi_asset_with_specs])

    assert result.success
    assert result.asset_value("one") == "hello"
    assert result.asset_value("two") == "world"


def test_materialize_result_iterator_unannotated_no_value():
    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs():
        yield MaterializeResult(asset_key="one")
        yield MaterializeResult(asset_key="two")

    result = materialize([multi_asset_with_specs])

    assert result.success
    assert result.asset_value("one") == NoValueSentinel
    assert result.asset_value("two") == NoValueSentinel


def test_materialize_result_iterator_unannotated_value():
    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs():
        yield MaterializeResult(asset_key="one", value="hello")
        yield MaterializeResult(asset_key="two", value="world")

    # if the return type is not annotated, it is assumed to be Nothing,
    # meaning we cannot return a value
    with pytest.raises(DagsterTypeCheckDidNotPass):
        materialize([multi_asset_with_specs])


def test_materialize_result_iterator_value_incorrect_type():
    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs() -> Iterator[MaterializeResult[str]]:
        yield MaterializeResult(asset_key="one", value="hello")
        yield MaterializeResult(asset_key="two", value=1)  # type: ignore

    with pytest.raises(DagsterTypeCheckDidNotPass):
        materialize([multi_asset_with_specs])


def test_materialize_result_value_annotated_incorrect_type():
    @asset
    def asset_with_value() -> MaterializeResult[int]:
        return MaterializeResult(value="hello")  # type: ignore

    with pytest.raises(DagsterTypeCheckDidNotPass):
        materialize([asset_with_value])


def test_materialize_result_value_annotated_no_value():
    @asset
    def asset_with_value() -> MaterializeResult[int]:
        return MaterializeResult()  # type: ignore

    with pytest.raises(DagsterTypeCheckDidNotPass):
        materialize([asset_with_value])


def test_materialize_result_with_default_io_manager():
    @asset
    def up():
        return MaterializeResult(value="hello")

    @asset(
        deps=[up],
    )
    def down(up: str):
        return MaterializeResult(value=up + " world")

    result = materialize(assets=[up, down])
    assert result.success
    assert result.asset_value("down") == "hello world"


def test_materialize_result_with_custom_io_manager_default_key():
    class CustomIOManager(IOManager):
        def __init__(self):
            self._storage = {}

        def load_input(self, context: InputContext):
            return self._storage[context.asset_key]

        def handle_output(self, context: OutputContext, obj):
            self._storage[context.asset_key] = obj

    @asset
    def up():
        return MaterializeResult(value="hello")

    @asset(
        deps=[up],
    )
    def down(up: str):
        return MaterializeResult(value=up + " world")

    io_manager = CustomIOManager()
    result = materialize(assets=[up, down], resources={"io_manager": io_manager})
    assert result.success
    assert result.asset_value("down") == "hello world"


def test_materialize_result_with_custom_io_manager_custom_key():
    class CustomIOManager(IOManager):
        def __init__(self):
            self._storage = {}

        def load_input(self, context: InputContext):
            return self._storage[context.asset_key]

        def handle_output(self, context: OutputContext, obj):
            self._storage[context.asset_key] = obj

    @asset(io_manager_key="io_whatever_manager")
    def up():
        return MaterializeResult(value="hello")

    @asset(
        deps=[up],
        io_manager_key="io_whatever_manager",
    )
    def down(up: str):
        return MaterializeResult(value=up + " world")

    io_manager = CustomIOManager()
    result = materialize(assets=[up, down], resources={"io_whatever_manager": io_manager})
    assert result.success
    assert result.asset_value("down") == "hello world"


def test_materialize_result_with_asset_key_ref():
    @asset
    def up():
        return MaterializeResult(value="hello")

    @asset(
        deps=["up"],
    )
    def down(up: str):
        return MaterializeResult(value=up + " world")

    result = materialize(assets=[up, down])
    assert result.success
    assert result.asset_value("down") == "hello world"


def test_materialize_result_with_custom_io_manager_type_mutate():
    class CustomIOManager(IOManager):
        def __init__(self):
            self._storage = {}

        def load_input(self, context: InputContext):
            return self._storage[context.asset_key]

        def handle_output(self, context: OutputContext, obj):
            self._storage[context.asset_key] = obj

    @asset
    def up():
        # Not generically typed for now
        return MaterializeResult(value=1)

    @asset(
        deps=[up],
    )
    def down(up: int):
        # Not generically typed for now
        return MaterializeResult(value=up + 1)

    io_manager = CustomIOManager()
    result = materialize(assets=[up, down], resources={"io_manager": io_manager})
    assert result.success
    assert result.asset_value("down") == 2


def test_multi_asset_with_asset_spec_io_manager():
    class CustomIOManager(IOManager):
        def __init__(self):
            self._storage = {}

        def load_input(self, context: InputContext):
            return self._storage[context.asset_key]

        def handle_output(self, context: OutputContext, obj):
            self._storage[context.asset_key] = obj

    @multi_asset(specs=[AssetSpec("one").with_io_manager_key("custom_io_manager")])
    def multi_asset_one(context: AssetExecutionContext):
        return MaterializeResult(value="hello")

    @multi_asset(
        specs=[
            AssetSpec("two", deps=["one"]).with_io_manager_key("custom_io_manager"),
        ],
    )
    def multi_asset_two(context: AssetExecutionContext, one: str):
        return MaterializeResult(value=one + " world")

    io_manager = CustomIOManager()
    result = materialize(
        assets=[multi_asset_one, multi_asset_two], resources={"custom_io_manager": io_manager}
    )
    assert result.success
    assert result.asset_value("two") == "hello world"

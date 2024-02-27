import random
import time

from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSeverity,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    AssetSelection,
    DailyPartitionsDefinition,
    In,
    MetadataValue,
    Nothing,
    Output,
    asset,
    asset_check,
    define_asset_job,
    graph_asset,
    multi_asset,
    op,
)
from dagster._core.definitions.decorators.asset_decorator import graph_multi_asset


@asset(key_prefix="test_prefix", group_name="asset_checks")
def checked_asset():
    return 1


@asset_check(asset=checked_asset, description="A check that fails half the time.")
def random_fail_check(checked_asset):
    random.seed(time.time())
    return AssetCheckResult(
        passed=random.choice([False, True]),
        metadata={"timestamp": MetadataValue.float(time.time())},
    )


@asset_check(
    asset=checked_asset,
    description="A check that fails half the time.",
)
def severe_random_fail_check():
    random.seed(time.time())
    return AssetCheckResult(
        passed=random.choice([False, True]),
        metadata={"timestamp": MetadataValue.float(time.time())},
        severity=AssetCheckSeverity.ERROR,
    )


@asset_check(
    asset=checked_asset, description="A check that always fails, and has several types of metadata."
)
def always_fail():
    return AssetCheckResult(
        passed=False,
        metadata={
            "foo": MetadataValue.text("bar"),
            "asset_key": MetadataValue.asset(checked_asset.key),
        },
        severity=AssetCheckSeverity.WARN,
    )


@asset_check(asset=checked_asset, description="A check that sleeps 30s then succeeds.")
def slow_check():
    time.sleep(30)
    return AssetCheckResult(passed=True)


@asset(
    group_name="asset_checks",
    check_specs=[
        AssetCheckSpec(
            name="random_fail_check",
            asset="asset_with_check_in_same_op",
            description=(
                "An ERROR check calculated in the same op with the asset. It fails half the time."
            ),
        )
    ],
)
def asset_with_check_in_same_op():
    yield Output(1)
    random.seed(time.time())
    yield AssetCheckResult(check_name="random_fail_check", passed=random.choice([False, True]))


@asset(group_name="asset_checks")
def check_exception_asset():
    return 1


@asset_check(
    asset=check_exception_asset, description="A check that hits an exception half the time."
)
def exception_check():
    random.seed(time.time())
    if random.choice([False, True]):
        raise Exception("This check failed!")
    return AssetCheckResult(passed=True)


@asset_check(
    asset=check_exception_asset,
    description="A severe check that hits an exception half the time.",
)
def severe_exception_check():
    random.seed(time.time())
    if random.choice([False, True]):
        raise Exception("This check failed!")
    return AssetCheckResult(passed=True)


@asset(
    group_name="asset_checks",
    partitions_def=DailyPartitionsDefinition(
        start_date="2020-01-01",
    ),
)
def partitioned_asset(_):
    return 1


@asset_check(
    asset=partitioned_asset,
    description="A check that fails half the time.",
)
def random_fail_check_on_partitioned_asset():
    random.seed(time.time())
    return AssetCheckResult(
        passed=random.choice([False, True]),
    )


@multi_asset(
    outs={
        "one": AssetOut(key="multi_asset_piece_1", group_name="asset_checks", is_required=False),
        "two": AssetOut(key="multi_asset_piece_2", group_name="asset_checks", is_required=False),
    },
    check_specs=[AssetCheckSpec("my_check", asset="multi_asset_piece_1")],
    can_subset=True,
)
def multi_asset_1_and_2(context: AssetExecutionContext):
    if AssetKey("multi_asset_piece_1") in context.selected_asset_keys:
        yield Output(1, output_name="one")
    if (
        AssetCheckKey(AssetKey("multi_asset_piece_1"), "my_check")
        in context.selected_asset_check_keys
    ):
        yield AssetCheckResult(passed=True, metadata={"foo": "bar"})
    if AssetKey("multi_asset_piece_2") in context.selected_asset_keys:
        yield Output(1, output_name="two")


@asset(
    group_name="asset_checks",
    check_specs=[
        AssetCheckSpec(name=f"check_{i}", asset="asset_with_100_checks") for i in range(100)
    ],
)
def asset_with_100_checks(_):
    yield Output(1)
    for i in range(100):
        yield AssetCheckResult(check_name=f"check_{i}", passed=random.random() > 0.2)


@asset(
    group_name="asset_checks",
    check_specs=[
        AssetCheckSpec(name=f"check_{i}", asset="asset_with_1000_checks") for i in range(1000)
    ],
)
def asset_with_1000_checks(_):
    yield Output(1)
    for i in range(1000):
        yield AssetCheckResult(check_name=f"check_{i}", passed=random.random() > 0.2)


@op
def create_staged_asset():
    return 1


@op
def test_staged_asset(staged_asset):
    random.seed(time.time())
    result = AssetCheckResult(
        passed=random.choice([False, True]),
    )
    yield result
    if not result.passed:
        raise Exception("Raising an exception to block promotion.")


@op(ins={"staged_asset": In(), "check_result": In(Nothing)})
def promote_staged_asset(staged_asset):
    return staged_asset


@graph_asset(
    group_name="asset_checks",
    check_specs=[
        AssetCheckSpec("random_fail_and_raise_check", asset="stage_then_promote_graph_asset")
    ],
)
def stage_then_promote_graph_asset():
    staged_asset = create_staged_asset()
    check_result = test_staged_asset(staged_asset)
    return {
        "result": promote_staged_asset(staged_asset, check_result),
        "stage_then_promote_graph_asset_random_fail_and_raise_check": check_result,
    }


@op
def test_1(staged_asset):
    time.sleep(1)
    result = AssetCheckResult(
        check_name="check_1",
        passed=True,
        metadata={"sample": "metadata"},
    )
    yield result
    if not result.passed:
        raise Exception("The check failed, so raising an error to block materializing.")


@op
def test_2(staged_asset):
    result = AssetCheckResult(
        check_name="check_2",
        passed=True,
        metadata={"sample": "metadata"},
    )
    yield result
    if not result.passed:
        raise Exception("The check failed, so raising an error to block materializing.")


@op
def test_3(staged_asset):
    yield AssetCheckResult(
        check_name="check_3",
        passed=False,
        severity=AssetCheckSeverity.WARN,
        metadata={"sample": "metadata"},
    )


@op(ins={"staged_asset": In(), "check_results": In(Nothing)})
def promote_staged_asset_with_tests(staged_asset):
    time.sleep(1)
    return staged_asset


@graph_asset(
    group_name="asset_checks",
    check_specs=[
        AssetCheckSpec(
            "check_1",
            asset="many_tests_graph_asset",
            description="A always passes.",
        ),
        AssetCheckSpec(
            "check_2",
            asset="many_tests_graph_asset",
            description="A always passes.",
        ),
        AssetCheckSpec(
            "check_3",
            asset="many_tests_graph_asset",
            description="A really slow and unimportant check that always fails.",
        ),
    ],
)
def many_tests_graph_asset():
    staged_asset = create_staged_asset()

    blocking_check_results = {
        "many_tests_graph_asset_check_1": test_1(staged_asset),
        "many_tests_graph_asset_check_2": test_2(staged_asset),
    }
    non_blocking_check_results = {"many_tests_graph_asset_check_3": test_3(staged_asset)}

    return {
        "result": promote_staged_asset_with_tests(
            staged_asset, list(blocking_check_results.values())
        ),
        **blocking_check_results,
        **non_blocking_check_results,
    }


@op
def graph_multi_asset_check_1(staged_asset):
    time.sleep(1)
    result = AssetCheckResult(
        asset_key="graph_multi_asset_one",
        check_name="check_1",
        passed=True,
        metadata={"sample": "metadata"},
    )
    yield result
    if not result.passed:
        raise Exception("The check failed, so raising an error to block materializing.")


@op
def graph_multi_asset_check_2(staged_asset):
    result = AssetCheckResult(
        asset_key="graph_multi_asset_one",
        check_name="check_2",
        passed=True,
        metadata={"sample": "metadata"},
    )
    yield result
    if not result.passed:
        raise Exception("The check failed, so raising an error to block materializing.")


@op
def graph_multi_asset_check_3(staged_asset):
    yield AssetCheckResult(
        asset_key="graph_multi_asset_one",
        check_name="check_3",
        passed=False,
        severity=AssetCheckSeverity.WARN,
        metadata={"sample": "metadata"},
    )


@op
def graph_multi_asset_2_check_1(staged_asset):
    result = AssetCheckResult(
        asset_key="graph_multi_asset_two",
        check_name="check_1",
        passed=False,
        metadata={"sample": "metadata"},
    )
    yield result
    if not result.passed:
        raise Exception("The check failed, so raising an error to block materializing.")


@graph_multi_asset(
    group_name="asset_checks",
    outs={"graph_multi_asset_one": AssetOut(), "graph_multi_asset_two": AssetOut()},
    check_specs=[
        AssetCheckSpec(
            "check_1",
            asset="graph_multi_asset_one",
            description="A always passes.",
        ),
        AssetCheckSpec(
            "check_2",
            asset="graph_multi_asset_one",
            description="A always passes.",
        ),
        AssetCheckSpec(
            "check_3",
            asset="graph_multi_asset_one",
            description="A really slow and unimportant check that always fails.",
        ),
        AssetCheckSpec(
            "check_1",
            asset="graph_multi_asset_two",
            description="A always passes.",
        ),
    ],
)
def many_tests_graph_multi_asset():
    staged_asset = create_staged_asset()
    staged_asset_2 = create_staged_asset()

    blocking_asset_1_check_results = {
        "graph_multi_asset_one_check_1": graph_multi_asset_check_1(staged_asset),
        "graph_multi_asset_one_check_2": graph_multi_asset_check_2(staged_asset),
    }

    blocking_asset_2_check_results = {
        "graph_multi_asset_two_check_1": graph_multi_asset_2_check_1(staged_asset_2)
    }

    return {
        "graph_multi_asset_one": promote_staged_asset_with_tests(
            staged_asset, list(blocking_asset_1_check_results.values())
        ),
        **blocking_asset_1_check_results,
        "graph_multi_asset_one_check_3": graph_multi_asset_check_3(staged_asset),
        "graph_multi_asset_two": promote_staged_asset_with_tests(
            staged_asset_2, list(blocking_asset_2_check_results.values())
        ),
        **blocking_asset_2_check_results,
    }


@asset(
    group_name="asset_checks",
    deps=[
        checked_asset,
        asset_with_check_in_same_op,
        check_exception_asset,
        partitioned_asset,
        AssetKey(["multi_asset_piece_2"]),
        AssetKey(["multi_asset_piece_1"]),
        stage_then_promote_graph_asset,
        many_tests_graph_asset,
        asset_with_100_checks,
        asset_with_1000_checks,
    ],
)
def downstream_asset():
    return 1


checks_included_job = define_asset_job(
    name="checks_included_job",
    selection=AssetSelection.assets(checked_asset),
)

checks_excluded_job = define_asset_job(
    name="checks_excluded_job",
    selection=AssetSelection.assets(checked_asset).without_checks(),
)

checks_only_job = define_asset_job(
    name="checks_only_job",
    selection=AssetSelection.checks_for_assets(checked_asset),
)


def get_checks_and_assets():
    return [
        checked_asset,
        random_fail_check,
        severe_random_fail_check,
        always_fail,
        slow_check,
        asset_with_check_in_same_op,
        downstream_asset,
        check_exception_asset,
        exception_check,
        severe_exception_check,
        partitioned_asset,
        random_fail_check_on_partitioned_asset,
        multi_asset_1_and_2,
        stage_then_promote_graph_asset,
        asset_with_100_checks,
        asset_with_1000_checks,
        many_tests_graph_asset,
        many_tests_graph_multi_asset,
        checks_included_job,
        checks_excluded_job,
        checks_only_job,
    ]

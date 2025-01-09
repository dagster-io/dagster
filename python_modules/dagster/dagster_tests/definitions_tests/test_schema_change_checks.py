from collections.abc import Sequence
from typing import Optional

from dagster import (
    AssetSelection,
    DagsterInstance,
    Definitions,
    ExecuteInProcessResult,
    MaterializeResult,
    TableSchema,
    asset,
    build_column_schema_change_checks,
    define_asset_job,
    materialize,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.execution.context.compute import AssetExecutionContext


def execute_checks(asset_checks, instance=None) -> ExecuteInProcessResult:
    defs = Definitions(
        asset_checks=asset_checks,
        jobs=[define_asset_job("job1", selection=AssetSelection.all_asset_checks())],
    )
    job_def = defs.get_job_def("job1")
    return job_def.execute_in_process(instance=instance)


def assert_expected_schema_change(
    old_schema: Optional[TableSchema],
    new_schema: Optional[TableSchema],
    description_substrs: Sequence[str],
    passed: bool,
):
    @asset(name="asset1")
    def my_asset(context: AssetExecutionContext):
        if context.has_tag("old"):
            return MaterializeResult(
                metadata=dict(TableMetadataSet(column_schema=old_schema)) if old_schema else None
            )
        return MaterializeResult(
            metadata=dict(TableMetadataSet(column_schema=new_schema)) if new_schema else None
        )

    instance = DagsterInstance.ephemeral()
    materialize([my_asset], instance=instance, tags={"old": "true"})
    materialize([my_asset], instance=instance)

    checks = build_column_schema_change_checks(assets=[my_asset])
    result = execute_checks(checks, instance=instance)
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]

    assert check_eval.passed == passed
    description = check_eval.description
    assert description is not None
    for substr in description_substrs:
        assert substr in description


def test_missing_schema():
    assert_expected_schema_change(
        None,
        None,
        ["Latest materialization has no column schema metadata"],
        False,
    )
    assert_expected_schema_change(
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        None,
        ["Latest materialization has no column schema metadata"],
        False,
    )
    assert_expected_schema_change(
        None,
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        ["Previous materialization has no column schema metadata"],
        False,
    )


def test_no_change():
    assert_expected_schema_change(
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        ["No changes to column schema between previous and latest materialization"],
        True,
    )


def test_changed():
    assert_expected_schema_change(
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str", "baz": "str", "qux": "str"}),
        ["Column schema changed", "Added columns: baz, qux"],
        False,
    )

    assert_expected_schema_change(
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str", "baz": "str", "qux": "str"}),
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        ["Column schema changed", "Removed columns: baz, qux"],
        False,
    )

    assert_expected_schema_change(
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str", "baz": "int"}),
        TableSchema.from_name_type_dict({"foo": "str", "bar": "int", "baz": "float"}),
        ["Column schema changed", "Column type changes:", "bar: str -> int", "baz: int -> float"],
        False,
    )

    assert_expected_schema_change(
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str", "baz": "int"}),
        TableSchema.from_name_type_dict({"bar": "int", "baz": "float", "qux": "timestamp"}),
        [
            "Column schema changed",
            "Added columns: qux",
            "Removed columns: foo",
            "Column type changes:",
            "bar: str -> int",
            "baz: int -> float",
        ],
        False,
    )


def test_not_enough_materializations():
    @asset(name="asset1")
    def my_asset(context: AssetExecutionContext):
        pass

    checks = build_column_schema_change_checks(assets=[my_asset])
    result = execute_checks(checks)
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]

    assert check_eval.passed
    assert check_eval.description == "The asset has been materialized fewer than 2 times"


def assert_expected_schema_change_two_assets(
    old_schema_1: Optional[TableSchema],
    new_schema_1: Optional[TableSchema],
    old_schema_2: Optional[TableSchema],
    new_schema_2: Optional[TableSchema],
    description_1_substrs: Sequence[str],
    passed_1: bool,
    description_2_substrs: Sequence[str],
    passed_2: bool,
):
    @asset()
    def my_asset_1(context: AssetExecutionContext):
        if context.has_tag("old"):
            return MaterializeResult(
                metadata=dict(TableMetadataSet(column_schema=old_schema_1))
                if old_schema_1
                else None
            )
        return MaterializeResult(
            metadata=dict(TableMetadataSet(column_schema=new_schema_1)) if new_schema_1 else None
        )

    @asset()
    def my_asset_2(context: AssetExecutionContext):
        if context.has_tag("old"):
            return MaterializeResult(
                metadata=dict(TableMetadataSet(column_schema=old_schema_2))
                if old_schema_2
                else None
            )
        return MaterializeResult(
            metadata=dict(TableMetadataSet(column_schema=new_schema_2)) if new_schema_2 else None
        )

    instance = DagsterInstance.ephemeral()
    materialize([my_asset_1, my_asset_2], instance=instance, tags={"old": "true"})
    materialize([my_asset_1, my_asset_2], instance=instance)

    checks = build_column_schema_change_checks(assets=[my_asset_1, my_asset_2])
    result = execute_checks(checks, instance=instance)
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    check_evals_by_key = {check_eval.asset_key: check_eval for check_eval in check_evals}
    check_eval_1 = check_evals_by_key[my_asset_1.key]
    check_eval_2 = check_evals_by_key[my_asset_2.key]

    assert check_eval_1.passed == passed_1
    description = check_eval_1.description
    assert description is not None
    for substr in description_1_substrs:
        assert substr in description

    assert check_eval_2.passed == passed_2
    description = check_eval_2.description
    assert description is not None
    for substr in description_2_substrs:
        assert substr in description


def test_multiple_assets():
    assert_expected_schema_change_two_assets(
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str", "baz": "int"}),
        TableSchema.from_name_type_dict({"foo": "str", "bar": "int", "baz": "float"}),
        ["No changes to column schema between previous and latest materialization"],
        True,
        ["Column schema changed", "Column type changes:", "bar: str -> int", "baz: int -> float"],
        False,
    )


def test_multiple_calls():
    @asset
    def asset_1():
        pass

    @asset
    def asset_2():
        pass

    checks_1 = build_column_schema_change_checks(assets=[asset_1])
    checks_2 = build_column_schema_change_checks(assets=[asset_2], severity=AssetCheckSeverity.WARN)
    result = execute_checks([*checks_1, *checks_2])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    for check_eval in check_evals:
        assert check_eval.passed
        assert check_eval.description == "The asset has been materialized fewer than 2 times"

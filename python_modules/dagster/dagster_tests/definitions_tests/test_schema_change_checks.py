from typing import Sequence

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
from dagster._core.definitions.metadata import TableMetadataSet


def execute_checks(asset_checks, instance=None) -> ExecuteInProcessResult:
    defs = Definitions(
        asset_checks=asset_checks,
        jobs=[define_asset_job("job1", selection=AssetSelection.all_asset_checks())],
    )
    job_def = defs.get_job_def("job1")
    return job_def.execute_in_process(instance=instance)


def assert_expected_schema_change(
    old_schema: TableSchema,
    new_schema: TableSchema,
    description_substrs: Sequence[str],
    passed: bool,
):
    @asset(name="asset1")
    def old():
        return MaterializeResult(metadata=dict(TableMetadataSet(column_schema=old_schema)))

    @asset(name="asset1")
    def new():
        return MaterializeResult(metadata=dict(TableMetadataSet(column_schema=new_schema)))

    instance = DagsterInstance.ephemeral()
    materialize([old], instance=instance)
    materialize([new], instance=instance)

    checks = build_column_schema_change_checks(assets=[new])
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


def test_build_column_schema_change_checks():
    assert_expected_schema_change(
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        TableSchema.from_name_type_dict({"foo": "str", "bar": "str"}),
        ["No changes to column schema between previous and latest materialization"],
        True,
    )

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

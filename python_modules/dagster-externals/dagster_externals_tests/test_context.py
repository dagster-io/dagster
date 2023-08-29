from unittest.mock import MagicMock

import pytest
from dagster_externals._context import ExternalExecutionContext
from dagster_externals._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionDataProvenance,
    ExternalExecutionPartitionKeyRange,
    ExternalExecutionTimeWindow,
)
from dagster_externals._util import DagsterExternalsError

TEST_EXTERNAL_EXECUTION_CONTEXT_DEFAULTS = ExternalExecutionContextData(
    asset_keys=None,
    code_version_by_asset_key=None,
    provenance_by_asset_key=None,
    partition_key=None,
    partition_key_range=None,
    partition_time_window=None,
    job_name="foo_job",
    run_id="123",
    retry_number=1,
    extras={},
)


def _make_external_execution_context(**kwargs):
    kwargs = {**TEST_EXTERNAL_EXECUTION_CONTEXT_DEFAULTS, **kwargs}
    return ExternalExecutionContext(
        data=ExternalExecutionContextData(**kwargs),
        message_reader=MagicMock(),
    )


def _assert_undefined(context, key) -> None:
    with pytest.raises(DagsterExternalsError, match=f"`{key}` is undefined"):
        getattr(context, key)


def test_no_asset_context():
    context = _make_external_execution_context()

    assert not context.is_asset_step
    _assert_undefined(context, "asset_key")
    _assert_undefined(context, "asset_keys")
    _assert_undefined(context, "code_version")
    _assert_undefined(context, "code_version_by_asset_key")
    _assert_undefined(context, "provenance")
    _assert_undefined(context, "provenance_by_asset_key")


def test_single_asset_context():
    foo_provenance = ExternalExecutionDataProvenance(
        code_version="alpha", input_data_versions={"bar": "baz"}, is_user_provided=False
    )

    context = _make_external_execution_context(
        asset_keys=["foo"],
        code_version_by_asset_key={"foo": "beta"},
        provenance_by_asset_key={"foo": foo_provenance},
    )

    assert context.is_asset_step
    assert context.asset_key == "foo"
    assert context.asset_keys == ["foo"]
    assert context.code_version == "beta"
    assert context.code_version_by_asset_key == {"foo": "beta"}
    assert context.provenance == foo_provenance
    assert context.provenance_by_asset_key == {"foo": foo_provenance}


def test_multi_asset_context():
    foo_provenance = ExternalExecutionDataProvenance(
        code_version="alpha", input_data_versions={"bar": "baz"}, is_user_provided=False
    )
    bar_provenance = None

    context = _make_external_execution_context(
        asset_keys=["foo", "bar"],
        code_version_by_asset_key={"foo": "beta", "bar": "gamma"},
        provenance_by_asset_key={
            "foo": foo_provenance,
            "bar": bar_provenance,
        },
    )

    assert context.is_asset_step
    _assert_undefined(context, "asset_key")
    assert context.asset_keys == ["foo", "bar"]
    _assert_undefined(context, "code_version")
    assert context.code_version_by_asset_key == {"foo": "beta", "bar": "gamma"}
    _assert_undefined(context, "provenance")
    assert context.provenance_by_asset_key == {"foo": foo_provenance, "bar": bar_provenance}


def test_no_partition_context():
    context = _make_external_execution_context()

    assert not context.is_partition_step
    _assert_undefined(context, "partition_key")
    _assert_undefined(context, "partition_key_range")
    _assert_undefined(context, "partition_time_window")


def test_single_partition_context():
    partition_key_range = ExternalExecutionPartitionKeyRange(start="foo", end="foo")

    context = _make_external_execution_context(
        partition_key="foo",
        partition_key_range=partition_key_range,
        partition_time_window=None,
    )

    assert context.is_partition_step
    assert context.partition_key == "foo"
    assert context.partition_key_range == partition_key_range
    assert context.partition_time_window is None


def test_multiple_partition_context():
    partition_key_range = ExternalExecutionPartitionKeyRange(start="2023-01-01", end="2023-01-02")
    time_window = ExternalExecutionTimeWindow(start="2023-01-01", end="2023-01-02")

    context = _make_external_execution_context(
        partition_key=None,
        partition_key_range=partition_key_range,
        partition_time_window=time_window,
    )

    assert context.is_partition_step
    _assert_undefined(context, "partition_key")
    assert context.partition_key_range == partition_key_range
    assert context.partition_time_window == time_window


def test_extras_context():
    context = _make_external_execution_context(extras={"foo": "bar"})

    assert context.get_extra("foo") == "bar"
    with pytest.raises(DagsterExternalsError, match="Extra `bar` is undefined"):
        context.get_extra("bar")

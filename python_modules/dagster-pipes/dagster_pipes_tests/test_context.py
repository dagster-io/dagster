from contextlib import contextmanager
from typing import Iterator
from unittest.mock import MagicMock

import jsonschema
import pytest
from dagster_pipes import (
    PIPES_PROTOCOL_VERSION,
    PIPES_PROTOCOL_VERSION_FIELD,
    DagsterPipesError,
    PipesContext,
    PipesContextData,
    PipesContextLoader,
    PipesDataProvenance,
    PipesMessage,
    PipesParams,
    PipesPartitionKeyRange,
    PipesTimeWindow,
    get_pipes_json_schema,
)

TEST_PIPES_CONTEXT_DEFAULTS = PipesContextData(
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


class _DirectContextLoader(PipesContextLoader):
    def __init__(self, context_data: PipesContextData):
        self._context_data = context_data

    @contextmanager
    def load_context(self, params: PipesParams) -> Iterator[PipesContextData]:
        yield self._context_data


def _make_external_execution_context(**kwargs):
    data = PipesContextData(**{**TEST_PIPES_CONTEXT_DEFAULTS, **kwargs})
    jsonschema.validate(data, get_pipes_json_schema("context"))
    return PipesContext(
        params_loader=MagicMock(),
        context_loader=_DirectContextLoader(data),
        message_writer=MagicMock(),
    )


def _assert_undefined(context, key) -> None:
    with pytest.raises(DagsterPipesError, match=f"`{key}` is undefined"):
        getattr(context, key)


def _assert_unknown_asset_key(context, method, *args, **kwargs) -> None:
    with pytest.raises(DagsterPipesError, match="Invalid asset key"):
        getattr(context, method)(*args, **kwargs)


def _assert_undefined_asset_key(context, method, *args, **kwargs) -> None:
    with pytest.raises(
        DagsterPipesError, match=f"Calling `{method}` without passing an asset key is undefined"
    ):
        getattr(context, method)(*args, **kwargs)


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
    foo_provenance = PipesDataProvenance(
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
    context.report_asset_materialization(
        metadata={
            "bar": "boo",
            "baz": {"raw_value": 2, "type": "int"},
        },
        data_version="bar",
    )

    _assert_unknown_asset_key(context, "report_asset_materialization", asset_key="fake")
    context.report_asset_check(
        "foo_check",
        True,
        metadata={
            "meta_1": 1,
            "meta_2": {"raw_value": "foo", "type": "text"},
        },
    )

    _assert_unknown_asset_key(context, "report_asset_check", "foo_check", True, asset_key="fake")


def test_multi_asset_context():
    foo_provenance = PipesDataProvenance(
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

    _assert_undefined_asset_key(context, "report_asset_materialization", "bar")
    _assert_unknown_asset_key(context, "report_asset_materialization", "bar", asset_key="fake")
    _assert_undefined_asset_key(context, "report_asset_check", "foo_check", True)
    _assert_unknown_asset_key(context, "report_asset_check", "foo_check", True, asset_key="fake")


def test_no_partition_context():
    context = _make_external_execution_context()

    assert not context.is_partition_step
    _assert_undefined(context, "partition_key")
    _assert_undefined(context, "partition_key_range")
    _assert_undefined(context, "partition_time_window")


def test_single_partition_context():
    partition_key_range = PipesPartitionKeyRange(start="foo", end="foo")

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
    partition_key_range = PipesPartitionKeyRange(start="2023-01-01", end="2023-01-02")
    time_window = PipesTimeWindow(start="2023-01-01", end="2023-01-02")

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
    with pytest.raises(DagsterPipesError, match="Extra `bar` is undefined"):
        context.get_extra("bar")


def test_report_twice_materialized():
    context = _make_external_execution_context(asset_keys=["foo"])
    with pytest.raises(DagsterPipesError, match="already been materialized"):
        context.report_asset_materialization(asset_key="foo")
        context.report_asset_materialization(asset_key="foo")


def _make_pipes_message(method, params):
    return PipesMessage(
        {
            PIPES_PROTOCOL_VERSION_FIELD: PIPES_PROTOCOL_VERSION,
            "method": method,
            "params": params,
        }
    )


def test_log():
    context = _make_external_execution_context(asset_keys=["foo"])
    context.log.critical("foo")
    context._message_channel.write_message.assert_called_with(  # noqa: SLF001
        _make_pipes_message(method="log", params={"level": "CRITICAL", "message": "foo"})
    )
    context.log.error("foo")
    context._message_channel.write_message.assert_called_with(  # noqa: SLF001
        _make_pipes_message(method="log", params={"level": "ERROR", "message": "foo"})
    )
    context.log.warning("foo")
    context._message_channel.write_message.assert_called_with(  # noqa: SLF001
        _make_pipes_message(method="log", params={"level": "WARNING", "message": "foo"})
    )
    context.log.info("foo")
    context._message_channel.write_message.assert_called_with(  # noqa: SLF001
        _make_pipes_message(method="log", params={"level": "INFO", "message": "foo"})
    )
    context.log.debug("foo")
    context._message_channel.write_message.assert_called_with(  # noqa: SLF001
        _make_pipes_message(method="log", params={"level": "DEBUG", "message": "foo"})
    )


def test_message_after_close():
    context = _make_external_execution_context(asset_keys=["foo"])
    context.close()
    with pytest.raises(
        DagsterPipesError, match="Cannot send message after pipes context is closed"
    ):
        context.log.info("foo")


def test_multiple_close():
    context = _make_external_execution_context(asset_keys=["foo"])
    # `close` is idempotent, multiple calls should not raise an error
    context.close()
    context.close()


def test_message_json_schema_validation():
    message = {
        PIPES_PROTOCOL_VERSION_FIELD: PIPES_PROTOCOL_VERSION,
        "method": "foo",
        "params": {"bar": "baz"},
    }
    jsonschema.validate(message, get_pipes_json_schema("message"))


def test_json_schema_rejects_invalid():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"foo": "bar"}, get_pipes_json_schema("context"))
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"foo": "bar"}, get_pipes_json_schema("message"))

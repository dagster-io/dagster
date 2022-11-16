import time
from hashlib import sha256
from typing import Any, Union

from dagster._core.definitions.events import AssetKey, AssetMaterialization, AssetObservation
from dagster._core.definitions.logical_version import (
    CODE_VERSION_TAG_KEY,
    INPUT_EVENT_POINTER_TAG_KEY_PREFIX,
    INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX,
    LOGICAL_VERSION_TAG_KEY,
    UNKNOWN_LOGICAL_VERSION,
    UNKNOWN_VALUE,
    LogicalVersion,
    LogicalVersionProvenance,
    compute_logical_version,
    extract_logical_version_from_entry,
    extract_logical_version_provenance_from_entry,
)
from dagster._core.events import (
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    StepMaterializationData,
)
from dagster._core.events.log import EventLogEntry


def _create_test_event_log_entry(event_type: DagsterEventType, data: Any) -> EventLogEntry:
    event_specific_data: Union[StepMaterializationData, AssetObservationData]
    if isinstance(data, AssetMaterialization):
        event_specific_data = StepMaterializationData(data, [])
    elif isinstance(data, AssetObservation):
        event_specific_data = AssetObservationData(data)
    else:
        raise Exception("Unsupported event type")

    return EventLogEntry(
        error_info=None,
        user_message="test",
        level="debug",
        run_id="test_run_id",
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            event_type.value,
            "test",
            event_specific_data=event_specific_data,
        ),
    )


def test_extract_logical_version_and_provenance_from_materialization_entry():

    materialization = AssetMaterialization(
        asset_key="foo",
        tags={
            LOGICAL_VERSION_TAG_KEY: "1",
            f"{INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX}/assetgroup/bar": "2",
            f"{INPUT_EVENT_POINTER_TAG_KEY_PREFIX}/assetgroup/bar": "10",
            f"{INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX}/baz": "3",
            f"{INPUT_EVENT_POINTER_TAG_KEY_PREFIX}/baz": "11",
            f"{CODE_VERSION_TAG_KEY}": "3",
        },
    )
    entry = _create_test_event_log_entry(DagsterEventType.ASSET_MATERIALIZATION, materialization)
    assert extract_logical_version_from_entry(entry) == LogicalVersion("1")
    assert extract_logical_version_provenance_from_entry(entry) == LogicalVersionProvenance(
        code_version="3",
        input_logical_versions={
            AssetKey(["assetgroup", "bar"]): LogicalVersion("2"),
            AssetKey(["baz"]): LogicalVersion("3"),
        },
    )


def test_extract_logical_version_from_observation_entry():

    observation = AssetObservation(
        asset_key="foo",
        tags={
            LOGICAL_VERSION_TAG_KEY: "1",
        },
    )
    entry = _create_test_event_log_entry(
        DagsterEventType.ASSET_OBSERVATION,
        observation,
    )
    assert extract_logical_version_from_entry(entry) == LogicalVersion("1")


def test_compute_logical_version():
    result = compute_logical_version(
        "foo", {AssetKey(["beta"]): LogicalVersion("1"), AssetKey(["alpha"]): LogicalVersion("2")}
    )
    hash_sig = sha256()
    hash_sig.update(bytearray("".join(["foo", "2", "1"]), "utf8"))
    assert result == LogicalVersion(hash_sig.hexdigest())


def test_compute_logical_version_unknown_code_version():
    result = compute_logical_version(UNKNOWN_VALUE, {AssetKey(["alpha"]): LogicalVersion("1")})
    assert result == UNKNOWN_LOGICAL_VERSION


def test_compute_logical_version_unknown_dep_version():
    result = compute_logical_version("foo", {AssetKey(["alpha"]): UNKNOWN_LOGICAL_VERSION})
    assert result == UNKNOWN_LOGICAL_VERSION

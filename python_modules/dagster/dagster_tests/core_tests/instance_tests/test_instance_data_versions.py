import time
from hashlib import sha256
from typing import Any, Union

from dagster._core.definitions.data_version import (
    CODE_VERSION_TAG,
    DATA_VERSION_TAG,
    INPUT_DATA_VERSION_TAG_PREFIX,
    INPUT_EVENT_POINTER_TAG_PREFIX,
    UNKNOWN_DATA_VERSION,
    UNKNOWN_VALUE,
    DataProvenance,
    DataVersion,
    compute_logical_data_version,
    extract_data_provenance_from_entry,
    extract_data_version_from_entry,
)
from dagster._core.definitions.events import AssetKey, AssetMaterialization, AssetObservation
from dagster._core.events import (
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    StepMaterializationData,
)
from dagster._core.events.log import EventLogEntry


def create_test_event_log_entry(event_type: DagsterEventType, data: Any) -> EventLogEntry:
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


def test_extract_data_version_and_provenance_from_materialization_entry():
    materialization = AssetMaterialization(
        asset_key="foo",
        tags={
            DATA_VERSION_TAG: "1",
            f"{INPUT_DATA_VERSION_TAG_PREFIX}/assetgroup/bar": "2",
            f"{INPUT_EVENT_POINTER_TAG_PREFIX}/assetgroup/bar": "10",
            f"{INPUT_DATA_VERSION_TAG_PREFIX}/baz": "3",
            f"{INPUT_EVENT_POINTER_TAG_PREFIX}/baz": "11",
            f"{CODE_VERSION_TAG}": "3",
        },
    )
    entry = create_test_event_log_entry(DagsterEventType.ASSET_MATERIALIZATION, materialization)
    assert extract_data_version_from_entry(entry) == DataVersion("1")
    assert extract_data_provenance_from_entry(entry) == DataProvenance(
        code_version="3",
        input_data_versions={
            AssetKey(["assetgroup", "bar"]): DataVersion("2"),
            AssetKey(["baz"]): DataVersion("3"),
        },
        is_user_provided=False,
    )


def test_extract_data_version_from_observation_entry():
    observation = AssetObservation(
        asset_key="foo",
        tags={
            DATA_VERSION_TAG: "1",
        },
    )
    entry = create_test_event_log_entry(
        DagsterEventType.ASSET_OBSERVATION,
        observation,
    )
    assert extract_data_version_from_entry(entry) == DataVersion("1")


def test_compute_logical_data_version():
    result = compute_logical_data_version(
        "foo", {AssetKey(["beta"]): DataVersion("1"), AssetKey(["alpha"]): DataVersion("2")}
    )
    hash_sig = sha256()
    hash_sig.update(bytearray("".join(["foo", "2", "1"]), "utf8"))
    assert result == DataVersion(hash_sig.hexdigest())


def test_compute_logical_data_version_unknown_code_version():
    result = compute_logical_data_version(UNKNOWN_VALUE, {AssetKey(["alpha"]): DataVersion("1")})
    assert result == UNKNOWN_DATA_VERSION


def test_compute_logical_data_version_unknown_dep_version():
    result = compute_logical_data_version("foo", {AssetKey(["alpha"]): UNKNOWN_DATA_VERSION})
    assert result == UNKNOWN_DATA_VERSION

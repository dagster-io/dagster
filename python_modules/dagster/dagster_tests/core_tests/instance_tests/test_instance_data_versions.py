import time
from hashlib import sha256
from typing import Any, Union

import dagster as dg
from dagster import DagsterInstance
from dagster._core.definitions.data_version import (
    CODE_VERSION_TAG,
    DATA_VERSION_TAG,
    INPUT_DATA_VERSION_TAG_PREFIX,
    INPUT_EVENT_POINTER_TAG_PREFIX,
    UNKNOWN_DATA_VERSION,
    UNKNOWN_VALUE,
    compute_logical_data_version,
    extract_data_provenance_from_entry,
    extract_data_version_from_entry,
)
from dagster._core.events import AssetObservationData, DagsterEventType, StepMaterializationData


def create_test_event_log_entry(event_type: DagsterEventType, data: Any) -> dg.EventLogEntry:
    event_specific_data: Union[StepMaterializationData, AssetObservationData]
    if isinstance(data, dg.AssetMaterialization):
        event_specific_data = StepMaterializationData(data, [])
    elif isinstance(data, dg.AssetObservation):
        event_specific_data = AssetObservationData(data)
    else:
        raise Exception("Unsupported event type")

    return dg.EventLogEntry(
        error_info=None,
        user_message="test",
        level="debug",
        run_id="test_run_id",
        timestamp=time.time(),
        dagster_event=dg.DagsterEvent(
            event_type.value,
            "test",
            event_specific_data=event_specific_data,
        ),
    )


def test_extract_data_version_and_provenance_from_materialization_entry():
    materialization = dg.AssetMaterialization(
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
    assert extract_data_version_from_entry(entry) == dg.DataVersion("1")
    assert extract_data_provenance_from_entry(entry) == dg.DataProvenance(
        code_version="3",
        input_storage_ids={
            dg.AssetKey(["assetgroup", "bar"]): 10,
            dg.AssetKey(["baz"]): 11,
        },
        input_data_versions={
            dg.AssetKey(["assetgroup", "bar"]): dg.DataVersion("2"),
            dg.AssetKey(["baz"]): dg.DataVersion("3"),
        },
        is_user_provided=False,
    )


def test_extract_data_version_from_observation_entry():
    observation = dg.AssetObservation(
        asset_key="foo",
        tags={
            DATA_VERSION_TAG: "1",
        },
    )
    entry = create_test_event_log_entry(
        DagsterEventType.ASSET_OBSERVATION,
        observation,
    )
    assert extract_data_version_from_entry(entry) == dg.DataVersion("1")


def test_compute_logical_data_version():
    result = compute_logical_data_version(
        "foo",
        {dg.AssetKey(["beta"]): dg.DataVersion("1"), dg.AssetKey(["alpha"]): dg.DataVersion("2")},
    )
    hash_sig = sha256()
    hash_sig.update(bytearray("".join(["foo", "2", "1"]), "utf8"))
    assert result == dg.DataVersion(hash_sig.hexdigest())


def test_compute_logical_data_version_unknown_code_version():
    result = compute_logical_data_version(
        UNKNOWN_VALUE, {dg.AssetKey(["alpha"]): dg.DataVersion("1")}
    )
    assert result == UNKNOWN_DATA_VERSION


def test_compute_logical_data_version_unknown_dep_version():
    result = compute_logical_data_version("foo", {dg.AssetKey(["alpha"]): UNKNOWN_DATA_VERSION})
    assert result == UNKNOWN_DATA_VERSION


def test_get_latest_materialization_code_versions():
    @dg.asset(code_version="abc")
    def has_code_version(): ...

    @dg.asset
    def has_no_code_version(): ...

    instance = DagsterInstance.ephemeral()
    dg.materialize([has_code_version, has_no_code_version], instance=instance)

    latest_materialization_code_versions = instance.get_latest_materialization_code_versions(
        [has_code_version.key, has_no_code_version.key, dg.AssetKey("something_else")]
    )
    assert len(latest_materialization_code_versions) == 3

    assert latest_materialization_code_versions[has_code_version.key] == "abc"
    assert (
        latest_materialization_code_versions[has_no_code_version.key] is not None
    )  # auto-generated
    assert latest_materialization_code_versions[dg.AssetKey("something_else")] is None

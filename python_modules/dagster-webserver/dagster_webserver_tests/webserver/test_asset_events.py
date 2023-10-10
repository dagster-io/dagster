import inspect

from dagster import (
    DagsterInstance,
)
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._seven import json
from dagster_pipes import PipesContext
from dagster_webserver.external_assets import ReportAssetMatParam
from starlette.testclient import TestClient


def test_report_asset_materialization_endpoint(instance: DagsterInstance, test_client: TestClient):
    # base case
    my_asset_key = "my_asset"
    response = test_client.post(f"/report_asset_materialization/{my_asset_key}")
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(AssetKey(my_asset_key))
    assert evt

    # empty asset key path
    response = test_client.post("/report_asset_materialization/")
    assert response.status_code == 400

    # multipart key
    long_key = AssetKey(["foo", "bar", "baz"])
    response = test_client.post(
        # url / delimiter for multipart keys
        "/report_asset_materialization/foo/bar/baz",  # long_key.to_user_string()
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(long_key)
    assert evt

    # slash in key (have to use query param)
    slash_key = AssetKey("slash/key")
    response = test_client.post(
        # have to urlencode / that are part of they key
        "/report_asset_materialization/",
        params={"asset_key": '["slash/key"]'},  # slash_key.to_string(),
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(slash_key)
    assert evt

    # multi part with slashes (have to use query param)
    nasty_key = AssetKey(["a/b", "c/d"])
    response = test_client.post(
        # have to urlencode / that are part of they key
        "/report_asset_materialization/",
        json={
            "asset_key": ["a/b", "c/d"],  # same args passed to AssetKey
        },
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(nasty_key)
    assert evt

    meta = {"my_metadata": "value"}
    mat = AssetMaterialization(
        asset_key=my_asset_key,
        partition="2021-09-23",
        description="cutest",
        metadata=meta,
        tags={
            DATA_VERSION_TAG: "new",
            DATA_VERSION_IS_USER_PROVIDED_TAG: "true",
        },
    )

    # kitchen sink json body
    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        json={
            "description": mat.description,
            "partition": mat.partition,
            "metadata": meta,  # handled separately to avoid MetadataValue ish
            "data_version": "new",
        },
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(AssetKey(my_asset_key))
    assert evt
    assert evt.asset_materialization
    assert evt.asset_materialization == mat

    # kitchen sink query params
    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        params={
            "description": mat.description,
            "partition": mat.partition,
            "metadata": json.dumps(meta),
            "data_version": "new",
        },
    )
    assert response.status_code == 200, response.json()
    evt = instance.get_latest_materialization_event(AssetKey(my_asset_key))
    assert evt
    assert evt.asset_materialization
    assert evt.asset_materialization == mat

    # bad metadata
    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        params={
            "metadata": meta,  # not json encoded
        },  # type: ignore
    )
    assert response.status_code == 400
    assert "Error parsing metadata json" in response.json()["error"]

    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        json={
            "metadata": "im_just_a_string",
        },
    )
    assert response.status_code == 400
    assert (
        'Error constructing AssetMaterialization: Param "metadata" is not'
        in response.json()["error"]
    )


def test_report_asset_materialization_apis_consistent(
    instance: DagsterInstance, test_client: TestClient
):
    # ensure the ext report_asset_materialization and the API endpoint have the same capabilities
    sample_payload = {
        "asset_key": "sample_key",
        "metadata": {"meta": "data"},
        "data_version": "so_new",
        "partition": "2023-09-23",
        "description": "boo",
    }

    # sample has entry for all supported params (banking on usage of enum)
    assert set(sample_payload.keys()) == set(
        {v for k, v in vars(ReportAssetMatParam).items() if not k.startswith("__")}
    )

    response = test_client.post("/report_asset_materialization/", json=sample_payload)
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(AssetKey(sample_payload["asset_key"]))
    assert evt
    mat = evt.asset_materialization
    assert mat

    for k, v in sample_payload.items():
        if k == "asset_key":
            assert mat.asset_key == AssetKey(v)
        elif k == "metadata":
            assert mat.metadata.keys() == v.keys()
        elif k == "data_version":
            tags = mat.tags
            assert tags
            assert tags[DATA_VERSION_TAG] == v
            assert tags[DATA_VERSION_IS_USER_PROVIDED_TAG]
        elif k == "partition":
            assert mat.partition == v
        elif k == "description":
            assert mat.description == v
        else:
            assert (
                False
            ), "need to add validation that sample payload content was written successfully"

    # all ext report_asset_materialization kwargs should be in sample payload
    sig = inspect.signature(PipesContext.report_asset_materialization)
    skip_set = {"self"}
    params = [p for p in sig.parameters if p not in skip_set]

    KNOWN_DIFF = {"partition", "description"}

    assert set(sample_payload.keys()).difference(set(params)) == KNOWN_DIFF

import base64
import os

import pytest
from dagster import (
    DagsterInstance,
    EnvVar,
    FloatMetadataValue,
    ObserveResult,
    asset,
    materialize,
    observable_source_asset,
)
from dagster._check import CheckError
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.observe import observe
from dagster._time import get_current_timestamp
from dagster_gcp import BigQueryResource, bigquery_resource, fetch_last_updated_timestamps

from dagster_gcp_tests.bigquery_tests.conftest import (
    IS_BUILDKITE,
    SHARED_BUILDKITE_BQ_CONFIG,
    temporary_bigquery_table,
)


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.integration
def test_old_resource_authenticate_via_config():
    asset_info = dict()

    @asset(required_resource_keys={"bigquery"})
    def test_asset() -> int:
        asset_info["gcp_creds_file"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None
        return 1

    old_gcp_creds_file = os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    assert old_gcp_creds_file is not None

    passed = False

    try:
        with open(old_gcp_creds_file, "r") as f:
            gcp_creds = f.read()

        resource_defs = {
            "bigquery": bigquery_resource.configured(
                {
                    "project": os.getenv("GCP_PROJECT_ID"),
                    "gcp_credentials": base64.b64encode(str.encode(gcp_creds)).decode(),
                }
            )
        }

        assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is None

        result = materialize(
            [test_asset],
            resources=resource_defs,
        )
        passed = result.success

        assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is None
        assert not os.path.exists(asset_info["gcp_creds_file"])
    finally:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = old_gcp_creds_file
        assert passed


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.integration
def test_pythonic_resource_authenticate_via_config():
    asset_info = dict()

    @asset
    def test_asset(bigquery: BigQueryResource) -> int:
        with bigquery.get_client():
            asset_info["gcp_creds_file"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None
            return 1

    old_gcp_creds_file = os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    assert old_gcp_creds_file is not None

    passed = False

    try:
        with open(old_gcp_creds_file, "r") as f:
            gcp_creds = f.read()

        resource_defs = {
            "bigquery": BigQueryResource(
                project=EnvVar("GCP_PROJECT_ID"),
                gcp_credentials=base64.b64encode(str.encode(gcp_creds)).decode(),
            ),
        }

        assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is None

        result = materialize(
            [test_asset],
            resources=resource_defs,
        )
        passed = result.success

        assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is None
        assert not os.path.exists(asset_info["gcp_creds_file"])
    finally:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = old_gcp_creds_file
        assert passed


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.integration
def test_pythonic_resource_authenticate_via_env():
    @asset
    def test_asset(bigquery: BigQueryResource) -> int:
        with bigquery.get_client():
            assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None
            return 1

    resource_defs = {
        "bigquery": BigQueryResource(
            project=EnvVar("GCP_PROJECT_ID"),
        ),
    }

    result = materialize(
        [test_asset],
        resources=resource_defs,
    )
    assert result.success


def test_fetch_last_updated_timestamps_no_table():
    with pytest.raises(CheckError):
        fetch_last_updated_timestamps(
            client={},
            dataset_id="foo",
            table_ids=[],
        )


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.integration
def test_fetch_last_updated_timestamps():
    start_timestamp = get_current_timestamp()
    dataset_name = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(schema_name=dataset_name, column_str="FOO string") as table_name:

        @observable_source_asset
        def retrieve_freshness(bigquery: BigQueryResource) -> ObserveResult:
            with bigquery.get_client() as client:
                freshness_datetime = fetch_last_updated_timestamps(
                    client=client, dataset_id=dataset_name, table_ids=[table_name]
                )[table_name]
                if freshness_datetime is None:
                    return ObserveResult(
                        metadata={"freshness_timestamp": None},
                    )
                else:
                    return ObserveResult(
                        data_version=DataVersion("foo"),
                        metadata={
                            "freshness_timestamp": FloatMetadataValue(
                                freshness_datetime.timestamp()
                            )
                        },
                    )

        instance = DagsterInstance.ephemeral()
        result = observe(
            [retrieve_freshness],
            instance=instance,
            resources={"bigquery": BigQueryResource(project=SHARED_BUILDKITE_BQ_CONFIG["project"])},
        )
        observations = result.asset_observations_for_node(retrieve_freshness.op.name)
        assert len(observations) == 1
        observation = observations[0]
        assert observation.tags["dagster/data_version"] == "foo"
        assert observation.metadata["freshness_timestamp"] is not None
        assert isinstance(observation.metadata["freshness_timestamp"], FloatMetadataValue)
        assert start_timestamp < observation.metadata["freshness_timestamp"].value

import base64
import os

import pytest
from dagster import asset, materialize
from dagster_gcs import bigquery_resource

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_authenticate_via_config():
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

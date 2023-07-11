import base64
import os

import pytest
from dagster import EnvVar, asset, materialize
from dagster_gcp import BigQueryResource, bigquery_resource
from dagster_gcp.auth.resources import GoogleAuthResource

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_old_resource_authenticate_via_config():
    @asset(required_resource_keys={"bigquery"})
    def test_asset(context) -> int:
        # this query will fail if credentials aren't set correctly
        context.resources.bigquery.query("SELECT 1").result()
        return 1

    old_gcp_creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    assert old_gcp_creds_file is not None

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

    result = materialize(
        [test_asset],
        resources=resource_defs,
    )
    assert result.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_pythonic_resource_authenticate_via_config():
    @asset
    def test_asset(bigquery: BigQueryResource) -> int:
        assert bigquery.google_auth_resource is not None

        assert bigquery.google_auth_resource.service_account_info is not None
        assert bigquery.google_auth_resource.service_account_file is None
        return 1

    gcp_creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    assert gcp_creds_file is not None

    with open(gcp_creds_file, "r") as f:
        gcp_creds = f.read()

    resource_defs = {
        "bigquery": BigQueryResource(
            project=EnvVar("GCP_PROJECT_ID"),
            gcp_credentials=base64.b64encode(str.encode(gcp_creds)).decode(),
        ),
    }

    result = materialize(
        [test_asset],
        resources=resource_defs,
    )
    assert result.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
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


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_pythonic_resource_authenticate_via_auth_resource():
    @asset
    def test_asset(bigquery: BigQueryResource) -> int:
        assert bigquery.google_auth_resource is not None

        assert bigquery.google_auth_resource.service_account_info is None
        assert bigquery.google_auth_resource.service_account_file is not None
        return 1

    gcp_creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    assert gcp_creds_file is not None

    resource_defs = {
        "bigquery": BigQueryResource(
            project=EnvVar("GCP_PROJECT_ID"),
            google_auth_resource=GoogleAuthResource(service_account_file=gcp_creds_file),
        ),
    }

    result = materialize(
        [test_asset],
        resources=resource_defs,
    )
    assert result.success

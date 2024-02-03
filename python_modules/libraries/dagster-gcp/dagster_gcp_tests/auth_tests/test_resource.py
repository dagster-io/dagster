import os

import pytest
from dagster import (
    asset,
    materialize,
)
from dagster_gcp import GoogleAuthResource

HAS_GCP_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None


@pytest.mark.skipif(
    not HAS_GCP_CREDENTIALS, reason="Requires GOOGLE_APPLICATION_CREDENTIALS be set."
)
def test_auth_resource_via_file():
    @asset
    def test_auth(auth: GoogleAuthResource):
        assert auth.service_account_file is not None
        assert auth.service_account_info is None

    gcp_creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    assert gcp_creds_file is not None

    resource_defs = {"auth": GoogleAuthResource(service_account_file=gcp_creds_file)}

    result = materialize(
        [test_auth],
        resources=resource_defs,
    )
    assert result.success


@pytest.mark.skipif(
    not HAS_GCP_CREDENTIALS, reason="Requires GOOGLE_APPLICATION_CREDENTIALS be set."
)
def test_auth_resource_via_info():
    @asset
    def test_auth(auth: GoogleAuthResource):
        assert auth.service_account_file is None
        assert auth.service_account_info is not None

    gcp_creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    assert gcp_creds_file is not None

    with open(gcp_creds_file, "r") as f:
        gcp_creds = f.read()

    resource_defs = {"auth": GoogleAuthResource(service_account_info=gcp_creds)}

    result = materialize(
        [test_auth],
        resources=resource_defs,
    )
    assert result.success


@pytest.mark.skipif(
    not HAS_GCP_CREDENTIALS, reason="Requires GOOGLE_APPLICATION_CREDENTIALS be set."
)
def test_auth_resource_via_env():
    @asset
    def test_auth(auth: GoogleAuthResource):
        assert auth.service_account_file is None
        assert auth.service_account_info is None

    gcp_creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    assert gcp_creds_file is not None

    resource_defs = {"auth": GoogleAuthResource()}

    result = materialize(
        [test_auth],
        resources=resource_defs,
    )
    assert result.success

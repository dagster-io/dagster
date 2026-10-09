import re

import pytest
from dagster_azure.container_apps.utils import build_acr_registry_credentials, sanitize_aca_name

# Azure's rule for Container Apps and Jobs names.
ACA_NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$")
IDENTITY_ID = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/agent"


class TestSanitizeAcaName:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("dagster-run-abc", "dagster-run-abc"),
            ("Dagster-Run-ABC", "dagster-run-abc"),
            ("my_location", "my-location"),
            ("my.location/v2", "my-location-v2"),
            ("a__b..c", "a-b-c"),
            ("-leading-and-trailing-", "leading-and-trailing"),
            ("a" * 32, "a" * 32),
        ],
    )
    def test_short_names(self, raw, expected):
        assert sanitize_aca_name(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "a" * 33,
            "dagster-run-" + "x" * 64,
            "dagster-run-0123456789abcdef0123456789abcdef",
            "Location_With.Mixed/Chars" * 3,
        ],
    )
    def test_long_names_are_truncated_with_a_hash_suffix(self, raw):
        name = sanitize_aca_name(raw)
        assert len(name) <= 32
        assert ACA_NAME_RE.match(name), name
        assert name == sanitize_aca_name(raw)
        # The suffix is derived from the raw input, so a one-character difference is preserved.
        assert name != sanitize_aca_name(raw + "y")

    @pytest.mark.parametrize(
        "raw",
        ["dagster-run-abc", "a" * 32, "a" * 40, "Run/With.Odd_Chars" * 4, "x-" * 20],
    )
    def test_output_always_satisfies_azure_naming_rule(self, raw):
        assert ACA_NAME_RE.match(sanitize_aca_name(raw))


class TestBuildAcrRegistryCredentials:
    @pytest.mark.parametrize(
        "identity_id,image,expected_server",
        [
            (IDENTITY_ID, "myacr.azurecr.io/user-code:1", "myacr.azurecr.io"),
            (IDENTITY_ID, "myacr.azurecr.io/team/user-code:1", "myacr.azurecr.io"),
            (IDENTITY_ID, "myacr.azurecr.io/user-code@sha256:abcd", "myacr.azurecr.io"),
        ],
    )
    def test_acr_image_with_identity(self, identity_id, image, expected_server):
        (credentials,) = build_acr_registry_credentials(identity_id, image) or []
        assert credentials.server == expected_server
        assert credentials.identity == identity_id
        assert credentials.password_secret_ref is None

    @pytest.mark.parametrize(
        "identity_id,image",
        [
            (None, "myacr.azurecr.io/user-code:1"),
            ("", "myacr.azurecr.io/user-code:1"),
            (IDENTITY_ID, "docker.io/library/python:3.12"),
            (IDENTITY_ID, "ghcr.io/org/image:1"),
            (IDENTITY_ID, "python:3.12"),
            (IDENTITY_ID, "azurecr.io/user-code:1"),
        ],
    )
    def test_no_credentials_without_identity_or_outside_acr(self, identity_id, image):
        assert build_acr_registry_credentials(identity_id, image) is None

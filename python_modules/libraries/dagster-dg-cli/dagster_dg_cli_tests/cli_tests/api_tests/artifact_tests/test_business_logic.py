"""Test artifact business logic functions without mocks."""

import json

from dagster_dg_cli.cli.api.formatters import format_artifact_download, format_artifact_upload
from dagster_rest_resources.schemas.artifact import (
    DgApiArtifactDownloadResult,
    DgApiArtifactUploadResult,
)


class TestFormatArtifactUpload:
    """Test the artifact upload formatting functions."""

    def test_format_upload_deployment_scope_text(self, snapshot):
        """Test formatting upload result with deployment scope."""
        result = DgApiArtifactUploadResult(key="my-artifact", deployment="prod")
        output = format_artifact_upload(result, as_json=False)
        snapshot.assert_match(output)

    def test_format_upload_deployment_scope_json(self, snapshot):
        """Test formatting upload result with deployment scope as JSON."""
        result = DgApiArtifactUploadResult(key="my-artifact", deployment="prod")
        output = format_artifact_upload(result, as_json=True)
        parsed = json.loads(output)
        snapshot.assert_match(parsed)

    def test_format_upload_organization_scope_text(self, snapshot):
        """Test formatting upload result with organization scope."""
        result = DgApiArtifactUploadResult(key="org-artifact")
        output = format_artifact_upload(result, as_json=False)
        snapshot.assert_match(output)

    def test_format_upload_organization_scope_json(self, snapshot):
        """Test formatting upload result with organization scope as JSON."""
        result = DgApiArtifactUploadResult(key="org-artifact")
        output = format_artifact_upload(result, as_json=True)
        parsed = json.loads(output)
        snapshot.assert_match(parsed)


class TestFormatArtifactDownload:
    """Test the artifact download formatting functions."""

    def test_format_download_deployment_scope_text(self, snapshot):
        """Test formatting download result with deployment scope."""
        result = DgApiArtifactDownloadResult(
            key="my-artifact", path="/tmp/artifact.tar.gz", deployment="prod"
        )
        output = format_artifact_download(result, as_json=False)
        snapshot.assert_match(output)

    def test_format_download_deployment_scope_json(self, snapshot):
        """Test formatting download result with deployment scope as JSON."""
        result = DgApiArtifactDownloadResult(
            key="my-artifact", path="/tmp/artifact.tar.gz", deployment="prod"
        )
        output = format_artifact_download(result, as_json=True)
        parsed = json.loads(output)
        snapshot.assert_match(parsed)

    def test_format_download_organization_scope_text(self, snapshot):
        """Test formatting download result with organization scope."""
        result = DgApiArtifactDownloadResult(key="org-artifact", path="/tmp/org-artifact.tar.gz")
        output = format_artifact_download(result, as_json=False)
        snapshot.assert_match(output)

    def test_format_download_organization_scope_json(self, snapshot):
        """Test formatting download result with organization scope as JSON."""
        result = DgApiArtifactDownloadResult(key="org-artifact", path="/tmp/org-artifact.tar.gz")
        output = format_artifact_download(result, as_json=True)
        parsed = json.loads(output)
        snapshot.assert_match(parsed)

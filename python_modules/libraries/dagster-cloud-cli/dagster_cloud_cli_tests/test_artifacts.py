from unittest.mock import patch

from dagster_cloud_cli.core import artifacts


def test_download_organization_artifact_passes_api_token(monkeypatch, tmp_path):
    monkeypatch.delenv("DAGSTER_CLOUD_API_TOKEN", raising=False)
    dest = tmp_path / "manifest.json"
    with (
        patch.object(artifacts, "download_artifact") as mock_download,
        patch.object(artifacts, "get_user_token", return_value="config-token"),
    ):
        artifacts.download_organization_artifact(
            key="some-key",
            path=dest,
            organization="my-org",
            api_token="passed-token",
        )

    assert mock_download.call_args.kwargs["api_token"] == "passed-token"

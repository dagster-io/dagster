import tempfile
from pathlib import Path

import pytest

from dagster_dg_cli_tests.cli_tests.plus_tests.utils import cleanup_gql_mocks


@pytest.fixture(autouse=True)
def _cleanup_gql_mocks():
    yield

    cleanup_gql_mocks()


@pytest.fixture()
def dg_plus_cli_config(monkeypatch):
    with (
        tempfile.TemporaryDirectory() as tmp_dg_dir,
        tempfile.TemporaryDirectory() as tmp_cloud_dir,
    ):
        config_path = Path(tmp_dg_dir) / "dg.toml"
        config_path.write_text(
            """
            [cli.plus]
            organization = "hooli"
            user_token = "abc123"
            default_deployment = "hooli-dev"
            """
        )
        monkeypatch.setenv("DG_CLI_CONFIG", config_path)
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(tmp_cloud_dir) / "config"))
        yield config_path

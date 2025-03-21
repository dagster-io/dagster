import json
import queue
import tempfile
import threading
import time
from pathlib import Path
from unittest import mock

import pytest
import requests
import tomlkit
import yaml
from click.testing import CliRunner
from dagster_dg.cli.plus import plus_group
from dagster_shared.plus.config import DagsterPlusCliConfig


@pytest.fixture()
def setup_cloud_cli_config(monkeypatch):
    with (
        tempfile.TemporaryDirectory() as tmp_cloud_dir,
        tempfile.TemporaryDirectory() as tmp_dg_dir,
    ):
        config_path = Path(tmp_cloud_dir) / "config"
        config_path.touch()
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", config_path)
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(tmp_dg_dir) / "dg.toml"))
        yield config_path


@pytest.fixture()
def setup_dg_cli_config(monkeypatch):
    with (
        tempfile.TemporaryDirectory() as tmp_dg_dir,
        tempfile.TemporaryDirectory() as tmp_cloud_dir,
    ):
        config_path = Path(tmp_dg_dir) / "dg.toml"
        config_path.touch()
        monkeypatch.setenv("DG_CLI_CONFIG", config_path)
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(tmp_cloud_dir) / "config"))
        yield config_path


@pytest.fixture()
def setup_dg_cli_config_additional_config(monkeypatch):
    with (
        tempfile.TemporaryDirectory() as tmp_dg_dir,
        tempfile.TemporaryDirectory() as tmp_cloud_dir,
    ):
        config_path = Path(tmp_dg_dir) / "dg.toml"
        config_path.write_text(
            """
            [cli]
            existing_key = "existing_value"
            """
        )
        monkeypatch.setenv("DG_CLI_CONFIG", config_path)
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(tmp_cloud_dir) / "config"))
        yield config_path


# Test setup command, using the web auth option
@pytest.mark.parametrize(
    "fixture_name",
    [
        "setup_cloud_cli_config",
        "setup_dg_cli_config",
        "setup_dg_cli_config_additional_config",
    ],
)
def test_setup_command_web(fixture_name, request: pytest.FixtureRequest):
    filepath = request.getfixturevalue(fixture_name)
    runner = CliRunner()
    with (
        mock.patch(
            "dagster_shared.utils.find_free_port",
            mock.Mock(return_value=4000),
        ),
        mock.patch(
            "dagster_shared.plus.login_server._generate_nonce",
            mock.Mock(return_value="ABCDEFGH"),
        ),
        mock.patch("dagster_dg.cli.plus.webbrowser.open", mock.Mock(return_value=True)),
    ):
        # Send configuration response to CLI endpoint, HTTP response passed back in queue
        q = queue.Queue()

        def respond_with_callback():
            time.sleep(0.25)
            response = requests.post(
                "http://localhost:4000/callback",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"nonce": "ABCDEFGH", "organization": "hooli", "token": "abc123"}),
            )
            q.put(response)

        th = threading.Thread(target=respond_with_callback)
        th.start()

        result = runner.invoke(plus_group, ["login"])
        th.join()

        assert result.exit_code == 0, result.output + " : " + str(result.exception)

        assert q.get().json().get("ok") is True, "JSON response from callback not as expected"

        # Verify new configuration success
        assert DagsterPlusCliConfig.get().organization == "hooli"
        assert DagsterPlusCliConfig.get().user_token == "abc123"

        if fixture_name == "setup_cloud_cli_config":
            assert yaml.safe_load(filepath.read_text()) == {
                "organization": "hooli",
                "user_token": "abc123",
            }
        elif fixture_name == "setup_dg_cli_config_additional_config":
            assert tomlkit.parse(filepath.read_text()) == {
                "cli": {
                    "existing_key": "existing_value",
                    "plus": {"organization": "hooli", "user_token": "abc123"},
                },
            }
        else:
            assert tomlkit.parse(filepath.read_text()) == {
                "cli": {"plus": {"organization": "hooli", "user_token": "abc123"}}
            }

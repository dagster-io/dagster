import json
import os
import queue
import tempfile
import threading
import time
from unittest import mock

import pytest
import requests
from click.testing import CliRunner
from dagster_dg.cli.plus import plus_group
from dagster_shared.plus.config import DagsterPlusCliConfig, get_active_config_path


@pytest.fixture()
def test_config_file(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config")
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", config_path)
        yield config_path


# Test setup command, using the web auth option
def test_setup_command_web(test_config_file):
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
        assert DagsterPlusCliConfig.from_file(get_active_config_path()).organization == "hooli"
        assert DagsterPlusCliConfig.from_file(get_active_config_path()).user_token == "abc123"

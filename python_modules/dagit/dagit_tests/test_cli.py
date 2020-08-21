import subprocess

from click.testing import CliRunner
from dagit.cli import ui
from gevent import pywsgi

from dagster.utils import file_relative_path


def test_invoke_ui():
    runner = CliRunner()
    result = runner.invoke(ui, ["--version"])
    assert "dagit, version" in result.output


def test_invoke_ui_with_port_taken(monkeypatch):
    def serve_forever(self):
        if self.server_port == 3000:
            raise OSError("Address already in use")

    monkeypatch.setattr(pywsgi.WSGIServer, "serve_forever", serve_forever)
    runner = CliRunner()
    result = runner.invoke(
        ui,
        ["-f", file_relative_path(__file__, "./pipeline.py"), "-a", "test_repository"],
        input="n\n",
    )
    assert result.exception

    result = runner.invoke(
        ui,
        ["-f", file_relative_path(__file__, "./pipeline.py"), "-a", "test_repository"],
        input="y\n",
    )
    assert ":3001" in result.output


def test_invoke_cli_wrapper_with_bad_option():
    process = subprocess.Popen(["dagit", "--fubar"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = process.communicate()
    assert process.returncode != 0
    assert b"Error: no such option: --fubar\n" in stderr

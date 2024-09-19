from os import path

import uvicorn
from click.testing import CliRunner
from dagster import job, op
from dagster._cli.debug import export_command
from dagster._core.test_utils import instance_for_test
from dagster_webserver.debug import webserver_debug_command


@op
def emit_one():
    return 1


@job
def pipe_test():
    emit_one()
    emit_one()


def test_roundtrip(monkeypatch):
    runner = CliRunner()
    with instance_for_test() as instance:
        run_result = pipe_test.execute_in_process(instance=instance)
        assert run_result.success
        file_path = path.join(instance.root_directory, ".temp.dump")
        export_result = runner.invoke(export_command, [run_result.run_id, file_path])
        assert "Exporting run_id" in export_result.output
        assert file_path in export_result.output

        # make webserver stop after launch
        monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: None)

        debug_result = runner.invoke(webserver_debug_command, [file_path])
        assert debug_result.exit_code == 0, debug_result.exception
        assert file_path in debug_result.output
        assert f"run_id: {run_result.run_id}" in debug_result.output

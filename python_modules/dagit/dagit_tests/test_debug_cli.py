from os import path

from click.testing import CliRunner
from dagit.debug import dagit_debug_command
from gevent import pywsgi

from dagster import execute_pipeline, lambda_solid, pipeline
from dagster.cli.debug import export_command
from dagster.core.test_utils import instance_for_test


@lambda_solid
def emit_one():
    return 1


@pipeline
def pipe_test():
    emit_one()
    emit_one()


def test_roundtrip(monkeypatch):
    runner = CliRunner()
    with instance_for_test() as instance:
        run_result = execute_pipeline(pipe_test, instance=instance)
        assert run_result.success
        file_path = path.join(instance.root_directory, ".temp.dump")
        export_result = runner.invoke(export_command, [run_result.run_id, file_path])
        assert "Exporting run_id" in export_result.output
        assert file_path in export_result.output

        # make dagit stop after launch
        monkeypatch.setattr(pywsgi.WSGIServer, "serve_forever", lambda _: None)

        debug_result = runner.invoke(dagit_debug_command, [file_path])
        assert file_path in debug_result.output
        assert "run_id: {}".format(run_result.run_id) in debug_result.output
        assert "Serving on" in debug_result.output

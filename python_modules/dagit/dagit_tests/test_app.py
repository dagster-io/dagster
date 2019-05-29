import pytest

try:
    import unittest.mock as mock
except ImportError:
    import mock

from dagster import ExecutionTargetHandle
from dagster.utils import script_relative_path
from dagit.app import create_app, notebook_view
from dagit.cli import host_dagit_ui

from dagster_graphql.implementation.pipeline_run_storage import (
    InMemoryPipelineRun,
    PipelineRunStorage,
)


def test_create_app():
    handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yml'))
    pipeline_run_storage = PipelineRunStorage(create_pipeline_run=InMemoryPipelineRun)
    assert create_app(handle, pipeline_run_storage, use_synchronous_execution_manager=True)
    assert create_app(handle, pipeline_run_storage, use_synchronous_execution_manager=False)


def test_notebook_view():
    notebook_path = script_relative_path('render_uuid_notebook.ipynb')
    html_response, code = notebook_view({'path': notebook_path})
    assert '6cac0c38-2c97-49ca-887c-4ac43f141213' in html_response
    assert code == 200


def test_successful_host_dagit_ui():
    with mock.patch('gevent.pywsgi.WSGIServer'):
        handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yml'))
        host_dagit_ui(log=False, log_dir=None, handle=handle, use_sync=True, host=None, port=2343)


def _define_mock_server(fn):
    class _Server:
        def __init__(self, *args, **kwargs):
            pass

        def serve_forever(self):
            fn()

    return _Server


def test_unknown_error():
    class AnException(Exception):
        pass

    def _raise_custom_error():
        raise AnException('foobar')

    with mock.patch('gevent.pywsgi.WSGIServer', new=_define_mock_server(_raise_custom_error)):
        handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yml'))
        with pytest.raises(AnException):
            host_dagit_ui(
                log=False, log_dir=None, handle=handle, use_sync=True, host=None, port=2343
            )


def test_port_collision():
    def _raise_os_error():
        raise OSError('Address already in use')

    with mock.patch('gevent.pywsgi.WSGIServer', new=_define_mock_server(_raise_os_error)):
        handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yml'))
        with pytest.raises(Exception) as exc_info:
            host_dagit_ui(
                log=False, log_dir=None, handle=handle, use_sync=True, host=None, port=2343
            )

        assert 'Another process ' in str(exc_info.value)

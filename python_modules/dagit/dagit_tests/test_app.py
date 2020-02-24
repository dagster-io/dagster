import pytest
from dagit.app import create_app
from dagit.cli import host_dagit_ui

from dagster import ExecutionTargetHandle, seven
from dagster.core.instance import DagsterInstance
from dagster.seven import mock
from dagster.utils import script_relative_path


def test_create_app():
    handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yaml'))
    assert create_app(handle, DagsterInstance.ephemeral())


def test_notebook_view():
    notebook_path = script_relative_path('render_uuid_notebook.ipynb')

    with create_app(
        ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yaml')),
        DagsterInstance.ephemeral(),
    ).test_client() as client:
        res = client.get('/dagit/notebook?path={}'.format(notebook_path))

    assert res.status_code == 200
    # This magic guid is hardcoded in the notebook
    assert b'6cac0c38-2c97-49ca-887c-4ac43f141213' in res.data


def test_index_view():
    with create_app(
        ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yaml')),
        DagsterInstance.ephemeral(),
    ).test_client() as client:
        res = client.get('/')

    assert res.status_code == 200, res.data
    assert b'You need to enable JavaScript to run this app' in res.data


def test_successful_host_dagit_ui():
    with mock.patch('gevent.pywsgi.WSGIServer'), seven.TemporaryDirectory() as temp_dir:
        handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yaml'))
        host_dagit_ui(storage_fallback=temp_dir, handle=handle, host=None, port=2343)


def _define_mock_server(fn):
    class _Server(object):
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

    with mock.patch(
        'gevent.pywsgi.WSGIServer', new=_define_mock_server(_raise_custom_error)
    ), seven.TemporaryDirectory() as temp_dir:
        handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yaml'))
        with pytest.raises(AnException):
            host_dagit_ui(storage_fallback=temp_dir, handle=handle, host=None, port=2343)


def test_port_collision():
    def _raise_os_error():
        raise OSError('Address already in use')

    with mock.patch(
        'gevent.pywsgi.WSGIServer', new=_define_mock_server(_raise_os_error)
    ), seven.TemporaryDirectory() as temp_dir:
        handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yaml'))
        with pytest.raises(Exception) as exc_info:
            host_dagit_ui(
                storage_fallback=temp_dir, handle=handle, host=None, port=2343, port_lookup=False
            )

        assert 'another instance of dagit ' in str(exc_info.value)

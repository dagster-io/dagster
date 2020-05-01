import pytest
from dagit.app import create_app_with_active_repository_data, create_app_with_reconstructable_repo
from dagit.cli import host_dagit_ui_with_reconstructable_repo

from dagster import seven
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance
from dagster.core.snap import active_repository_data_from_def
from dagster.seven import mock
from dagster.utils import file_relative_path


def test_create_app_with_reconstructable_repo():
    recon_repo = ReconstructableRepository.from_yaml(
        file_relative_path(__file__, './repository.yaml')
    )
    assert create_app_with_reconstructable_repo(recon_repo, DagsterInstance.ephemeral())


def test_create_app_with_active_repo_data():
    recon_repo = ReconstructableRepository.from_yaml(
        file_relative_path(__file__, './repository.yaml')
    )
    active_repository_data = active_repository_data_from_def(recon_repo.get_definition())
    assert create_app_with_active_repository_data(
        active_repository_data, DagsterInstance.ephemeral()
    )


def test_notebook_view():
    notebook_path = file_relative_path(__file__, 'render_uuid_notebook.ipynb')

    with create_app_with_reconstructable_repo(
        ReconstructableRepository.from_yaml(file_relative_path(__file__, './repository.yaml')),
        DagsterInstance.ephemeral(),
    ).test_client() as client:
        res = client.get('/dagit/notebook?path={}'.format(notebook_path))

    assert res.status_code == 200
    # This magic guid is hardcoded in the notebook
    assert b'6cac0c38-2c97-49ca-887c-4ac43f141213' in res.data


def test_index_view():
    with create_app_with_reconstructable_repo(
        ReconstructableRepository.from_yaml(file_relative_path(__file__, './repository.yaml')),
        DagsterInstance.ephemeral(),
    ).test_client() as client:
        res = client.get('/')

    assert res.status_code == 200, res.data
    assert b'You need to enable JavaScript to run this app' in res.data


def test_successful_host_dagit_ui():
    with mock.patch('gevent.pywsgi.WSGIServer'), seven.TemporaryDirectory() as temp_dir:
        recon_repo = ReconstructableRepository.from_yaml(
            file_relative_path(__file__, './repository.yaml')
        )
        host_dagit_ui_with_reconstructable_repo(
            storage_fallback=temp_dir, recon_repo=recon_repo, host=None, port=2343
        )


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
        recon_repo = ReconstructableRepository.from_yaml(
            file_relative_path(__file__, './repository.yaml')
        )
        with pytest.raises(AnException):
            host_dagit_ui_with_reconstructable_repo(
                storage_fallback=temp_dir, recon_repo=recon_repo, host=None, port=2343
            )


def test_port_collision():
    def _raise_os_error():
        raise OSError('Address already in use')

    with mock.patch(
        'gevent.pywsgi.WSGIServer', new=_define_mock_server(_raise_os_error)
    ), seven.TemporaryDirectory() as temp_dir:
        recon_repo = ReconstructableRepository.from_yaml(
            file_relative_path(__file__, './repository.yaml')
        )
        with pytest.raises(Exception) as exc_info:
            host_dagit_ui_with_reconstructable_repo(
                storage_fallback=temp_dir,
                recon_repo=recon_repo,
                host=None,
                port=2343,
                port_lookup=False,
            )

        assert 'another instance of dagit ' in str(exc_info.value)

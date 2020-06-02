import json
import os

import pytest
import yaml
from click.testing import CliRunner
from dagit.app import create_app_with_reconstructable_repo
from dagit.cli import host_dagit_ui_with_reconstructable_repo, host_dagit_ui_with_workspace, ui

from dagster import seven
from dagster.cli.workspace import load_workspace_from_yaml_path
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance
from dagster.core.telemetry import START_DAGIT_WEBSERVER, UPDATE_REPO_STATS, hash_name
from dagster.core.test_utils import environ
from dagster.seven import mock
from dagster.utils import file_relative_path, pushd, script_relative_path


def test_create_app_with_reconstructable_repo():
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
        file_relative_path(__file__, './repository.yaml')
    )
    assert create_app_with_reconstructable_repo(recon_repo, DagsterInstance.ephemeral())


def test_create_app_with_reconstructable_repo_and_scheduler():
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
        file_relative_path(__file__, './repository.yaml')
    )
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(
            temp_dir,
            overrides={
                'scheduler': {
                    'module': 'dagster.utils.test',
                    'class': 'FilesystemTestScheduler',
                    'config': {'base_dir': temp_dir},
                }
            },
        )
        assert create_app_with_reconstructable_repo(recon_repo, instance)


def test_notebook_view():
    notebook_path = file_relative_path(__file__, 'render_uuid_notebook.ipynb')

    with create_app_with_reconstructable_repo(
        ReconstructableRepository.from_legacy_repository_yaml(
            file_relative_path(__file__, './repository.yaml')
        ),
        DagsterInstance.ephemeral(),
    ).test_client() as client:
        res = client.get('/dagit/notebook?path={}'.format(notebook_path))

    assert res.status_code == 200
    # This magic guid is hardcoded in the notebook
    assert b'6cac0c38-2c97-49ca-887c-4ac43f141213' in res.data


def test_index_view():
    with create_app_with_reconstructable_repo(
        ReconstructableRepository.from_legacy_repository_yaml(
            file_relative_path(__file__, './repository.yaml')
        ),
        DagsterInstance.ephemeral(),
    ).test_client() as client:
        res = client.get('/')

    assert res.status_code == 200, res.data
    assert b'You need to enable JavaScript to run this app' in res.data


def test_successful_host_dagit_ui_from_workspace():
    with mock.patch('gevent.pywsgi.WSGIServer'), seven.TemporaryDirectory() as temp_dir:
        workspace = load_workspace_from_yaml_path(file_relative_path(__file__, './workspace.yaml'))

        host_dagit_ui_with_workspace(
            storage_fallback=temp_dir, workspace=workspace, host=None, port=2343
        )


def test_successful_host_dagit_ui_from_legacy_repository():
    with mock.patch('gevent.pywsgi.WSGIServer'), seven.TemporaryDirectory() as temp_dir:
        recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
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
        recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
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
        recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
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


def path_to_tutorial_file(path):
    return script_relative_path(
        os.path.join('../../../examples/dagster_examples/intro_tutorial/', path)
    )


@pytest.mark.skipif(
    os.name == 'nt', reason="TemporaryDirectory disabled for win because of event.log contention"
)
@mock.patch('gevent.pywsgi.WSGIServer.serve_forever')
def test_dagit_logs(
    server_mock, caplog,
):
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            with open(os.path.join(temp_dir, 'dagster.yaml'), 'w') as fd:
                yaml.dump({}, fd, default_flow_style=False)

            DagsterInstance.local_temp(temp_dir)
            runner = CliRunner(env={'DAGSTER_HOME': temp_dir})
            with pushd(path_to_tutorial_file('')):

                runner.invoke(
                    ui, ['-y', file_relative_path(__file__, 'telemetry_repository.yaml'),],
                )

                actions = set()
                for record in caplog.records:
                    message = json.loads(record.getMessage())
                    actions.add(message.get('action'))
                    if message.get('action') == UPDATE_REPO_STATS:
                        assert message.get('pipeline_name_hash') == ''
                        assert message.get('num_pipelines_in_repo') == str(4)
                        assert message.get('repo_hash') == hash_name('dagster_test_repository')
                    assert set(message.keys()) == set(
                        [
                            'action',
                            'client_time',
                            'elapsed_time',
                            'event_id',
                            'instance_id',
                            'pipeline_name_hash',
                            'num_pipelines_in_repo',
                            'repo_hash',
                            'python_version',
                            'metadata',
                            'version',
                        ]
                    )

                assert actions == set([START_DAGIT_WEBSERVER, UPDATE_REPO_STATS])
                assert len(caplog.records) == 2
                assert server_mock.call_args_list == [mock.call()]

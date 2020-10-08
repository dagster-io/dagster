import json
import os

import pytest
import yaml
from click.testing import CliRunner
from dagit.app import create_app_from_workspace
from dagit.cli import host_dagit_ui_with_workspace, ui

from dagster import seven
from dagster.cli.workspace.load import load_workspace_from_yaml_paths
from dagster.core.host_representation.handle import UserProcessApi
from dagster.core.instance import DagsterInstance
from dagster.core.telemetry import START_DAGIT_WEBSERVER, UPDATE_REPO_STATS, hash_name
from dagster.core.test_utils import environ
from dagster.seven import mock
from dagster.utils import file_relative_path


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_create_app_with_workspace(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "./workspace.yaml")], python_user_process_api,
    ) as workspace:
        assert create_app_from_workspace(workspace, DagsterInstance.ephemeral())


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_create_app_with_multiple_workspace_files(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [
            file_relative_path(__file__, "./workspace.yaml"),
            file_relative_path(__file__, "./override.yaml"),
        ],
        python_user_process_api,
    ) as workspace:
        assert create_app_from_workspace(workspace, DagsterInstance.ephemeral())


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_create_app_with_workspace_and_scheduler(python_user_process_api):
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "./workspace.yaml")], python_user_process_api
    ) as workspace:
        with seven.TemporaryDirectory() as temp_dir:
            instance = DagsterInstance.local_temp(
                temp_dir,
                overrides={
                    "scheduler": {
                        "module": "dagster.utils.test",
                        "class": "FilesystemTestScheduler",
                        "config": {"base_dir": temp_dir},
                    }
                },
            )
            assert create_app_from_workspace(workspace, instance)


def test_notebook_view():
    notebook_path = file_relative_path(__file__, "render_uuid_notebook.ipynb")

    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI
    ) as workspace:
        with create_app_from_workspace(
            workspace, DagsterInstance.ephemeral(),
        ).test_client() as client:
            res = client.get("/dagit/notebook?path={}".format(notebook_path))

        assert res.status_code == 200
        # This magic guid is hardcoded in the notebook
        assert b"6cac0c38-2c97-49ca-887c-4ac43f141213" in res.data


def test_index_view():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI
    ) as workspace:
        with create_app_from_workspace(
            workspace, DagsterInstance.ephemeral(),
        ).test_client() as client:
            res = client.get("/")

        assert res.status_code == 200, res.data
        assert b"You need to enable JavaScript to run this app" in res.data


def test_index_view_at_path_prefix():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI
    ) as workspace:
        with create_app_from_workspace(
            workspace, DagsterInstance.ephemeral(), "/dagster-path"
        ).test_client() as client:
            # / redirects to prefixed path
            res = client.get("/")
            assert res.status_code == 301

            # index contains the path meta tag
            res = client.get("/dagster-path")
            assert res.status_code == 200
            assert b"You need to enable JavaScript to run this app" in res.data
            assert b'<meta name="dagit-path-prefix" content="/dagster-path"' in res.data


def test_graphql_view():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI
    ) as workspace:
        with create_app_from_workspace(
            workspace, DagsterInstance.ephemeral(),
        ).test_client() as client:
            res = client.get("/graphql")
        assert b"Must provide query string" in res.data


def test_graphql_view_at_path_prefix():
    with load_workspace_from_yaml_paths(
        [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI
    ) as workspace:
        with create_app_from_workspace(
            workspace, DagsterInstance.ephemeral(), "/dagster-path"
        ).test_client() as client:
            res = client.get("/dagster-path/graphql")
            assert b"Must provide query string" in res.data


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_successful_host_dagit_ui_from_workspace(python_user_process_api):
    with mock.patch("gevent.pywsgi.WSGIServer"), seven.TemporaryDirectory() as temp_dir:

        instance = DagsterInstance.get(temp_dir)

        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "./workspace.yaml")], python_user_process_api,
        ) as workspace:
            host_dagit_ui_with_workspace(
                instance=instance, workspace=workspace, host=None, port=2343, path_prefix=""
            )


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_successful_host_dagit_ui_from_multiple_workspace_files(python_user_process_api):
    with mock.patch("gevent.pywsgi.WSGIServer"), seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.get(temp_dir)

        with load_workspace_from_yaml_paths(
            [
                file_relative_path(__file__, "./workspace.yaml"),
                file_relative_path(__file__, "./override.yaml"),
            ],
            python_user_process_api,
        ) as workspace:
            host_dagit_ui_with_workspace(
                instance=instance, workspace=workspace, host=None, port=2343, path_prefix=""
            )


def test_successful_host_dagit_ui_from_legacy_repository():
    with mock.patch("gevent.pywsgi.WSGIServer"), seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.get(temp_dir)
        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI,
        ) as workspace:
            host_dagit_ui_with_workspace(
                instance=instance, workspace=workspace, host=None, port=2343, path_prefix=""
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
        raise AnException("foobar")

    with mock.patch(
        "gevent.pywsgi.WSGIServer", new=_define_mock_server(_raise_custom_error)
    ), seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.get(temp_dir)
        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI,
        ) as workspace:
            with pytest.raises(AnException):
                host_dagit_ui_with_workspace(
                    instance=instance, workspace=workspace, host=None, port=2343, path_prefix=""
                )


def test_port_collision():
    def _raise_os_error():
        raise OSError("Address already in use")

    with mock.patch(
        "gevent.pywsgi.WSGIServer", new=_define_mock_server(_raise_os_error)
    ), seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.get(temp_dir)
        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI,
        ) as workspace:
            with pytest.raises(Exception) as exc_info:
                host_dagit_ui_with_workspace(
                    instance=instance,
                    workspace=workspace,
                    host=None,
                    port=2343,
                    port_lookup=False,
                    path_prefix="",
                )

            assert "another instance of dagit " in str(exc_info.value)


def test_invalid_path_prefix():
    with mock.patch("gevent.pywsgi.WSGIServer"), seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.get(temp_dir)

        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI,
        ) as workspace:
            with pytest.raises(Exception) as exc_info:
                host_dagit_ui_with_workspace(
                    instance=instance,
                    workspace=workspace,
                    host=None,
                    port=2343,
                    port_lookup=False,
                    path_prefix="no-leading-slash",
                )
            assert "path prefix should begin with a leading" in str(exc_info.value)

            with pytest.raises(Exception) as exc_info:
                host_dagit_ui_with_workspace(
                    instance=instance,
                    workspace=workspace,
                    host=None,
                    port=2343,
                    port_lookup=False,
                    path_prefix="/extra-trailing-slash/",
                )
            assert "path prefix should not include a trailing" in str(exc_info.value)


def test_valid_path_prefix():
    with mock.patch("gevent.pywsgi.WSGIServer"), seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.get(temp_dir)

        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "./workspace.yaml")], UserProcessApi.CLI,
        ) as workspace:
            host_dagit_ui_with_workspace(
                instance=instance,
                workspace=workspace,
                host=None,
                port=2343,
                port_lookup=False,
                path_prefix="/dagster-path",
            )


@pytest.mark.skipif(
    os.name == "nt", reason="TemporaryDirectory disabled for win because of event.log contention"
)
@mock.patch("gevent.pywsgi.WSGIServer.serve_forever")
def test_dagit_logs(
    server_mock, caplog,
):
    with seven.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            with open(os.path.join(temp_dir, "dagster.yaml"), "w") as fd:
                yaml.dump({}, fd, default_flow_style=False)

            DagsterInstance.local_temp(temp_dir)
            runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
            result = runner.invoke(
                ui, ["-w", file_relative_path(__file__, "telemetry_repository.yaml"),],
            )
            assert result.exit_code == 0, str(result.exception)

            actions = set()
            for record in caplog.records:
                message = json.loads(record.getMessage())
                actions.add(message.get("action"))
                if message.get("action") == UPDATE_REPO_STATS:
                    assert message.get("pipeline_name_hash") == ""
                    assert message.get("num_pipelines_in_repo") == str(4)
                    assert message.get("repo_hash") == hash_name("dagster_test_repository")
                assert set(message.keys()) == set(
                    [
                        "action",
                        "client_time",
                        "elapsed_time",
                        "event_id",
                        "instance_id",
                        "pipeline_name_hash",
                        "num_pipelines_in_repo",
                        "repo_hash",
                        "python_version",
                        "metadata",
                        "version",
                    ]
                )

            assert actions == set([START_DAGIT_WEBSERVER, UPDATE_REPO_STATS])
            assert len(caplog.records) == 2
            assert server_mock.call_args_list == [mock.call()]

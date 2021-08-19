import json
import tempfile
from unittest import mock

import pytest
from click.testing import CliRunner
from dagit.app import create_app_from_workspace_process_context
from dagit.cli import host_dagit_ui_with_workspace_process_context, ui
from dagster.core.instance import DagsterInstance
from dagster.core.telemetry import START_DAGIT_WEBSERVER, UPDATE_REPO_STATS, hash_name
from dagster.core.test_utils import instance_for_test
from dagster.core.workspace.load import load_workspace_process_context_from_yaml_paths
from dagster.utils import file_relative_path


def test_create_app_with_workspace():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [file_relative_path(__file__, "./workspace.yaml")],
    ) as workspace_process_context:
        assert create_app_from_workspace_process_context(workspace_process_context)


def test_create_app_with_multiple_workspace_files():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(),
        [
            file_relative_path(__file__, "./workspace.yaml"),
            file_relative_path(__file__, "./override.yaml"),
        ],
    ) as workspace_process_context:
        assert create_app_from_workspace_process_context(workspace_process_context)


def test_create_app_with_workspace_and_scheduler():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            temp_dir=temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.utils.test",
                    "class": "FilesystemTestScheduler",
                    "config": {"base_dir": temp_dir},
                }
            },
        ) as instance:
            with load_workspace_process_context_from_yaml_paths(
                instance, [file_relative_path(__file__, "./workspace.yaml")]
            ) as workspace_process_context:
                assert create_app_from_workspace_process_context(workspace_process_context)


def test_notebook_view():
    notebook_path = file_relative_path(__file__, "render_uuid_notebook.ipynb")

    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        with create_app_from_workspace_process_context(
            workspace_process_context,
        ).test_client() as client:
            res = client.get(
                f"/dagit/notebook?path={notebook_path}&repoName=test_repository&repoLocName=load_from_file"
            )

        assert res.status_code == 200
        # This magic guid is hardcoded in the notebook
        assert b"6cac0c38-2c97-49ca-887c-4ac43f141213" in res.data


def test_index_view():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        with create_app_from_workspace_process_context(
            workspace_process_context
        ).test_client() as client:
            res = client.get("/")

        assert res.status_code == 200, res.data
        assert b"You need to enable JavaScript to run this app" in res.data


def test_index_view_at_path_prefix():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        with create_app_from_workspace_process_context(
            workspace_process_context, "/dagster-path"
        ).test_client() as client:
            # / redirects to prefixed path
            res = client.get("/")
            assert res.status_code == 200

            # index contains the path meta tag
            res = client.get("/dagster-path/")
            assert res.status_code == 200
            assert b"You need to enable JavaScript to run this app" in res.data
            assert b'{"pathPrefix": "/dagster-path"}' in res.data


def test_graphql_view():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        with create_app_from_workspace_process_context(
            workspace_process_context,
        ).test_client() as client:
            res = client.get("/graphql")
        assert b"Must provide query string" in res.data


def test_graphql_view_at_path_prefix():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        with create_app_from_workspace_process_context(
            workspace_process_context, "/dagster-path"
        ).test_client() as client:
            res = client.get("/dagster-path/graphql")
            assert b"Must provide query string" in res.data


def test_successful_host_dagit_ui_from_workspace():
    with mock.patch("gevent.pywsgi.WSGIServer"), tempfile.TemporaryDirectory() as temp_dir:

        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagit_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="",
            )


def test_successful_host_dagit_ui_from_multiple_workspace_files():
    with mock.patch("gevent.pywsgi.WSGIServer"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance,
            [
                file_relative_path(__file__, "./workspace.yaml"),
                file_relative_path(__file__, "./override.yaml"),
            ],
        ) as workspace_process_context:
            host_dagit_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="",
            )


def test_successful_host_dagit_ui_from_legacy_repository():
    with mock.patch("gevent.pywsgi.WSGIServer"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagit_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="",
            )


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
        raise AnException("foobar")

    with mock.patch(
        "gevent.pywsgi.WSGIServer", new=_define_mock_server(_raise_custom_error)
    ), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            with pytest.raises(AnException):
                host_dagit_ui_with_workspace_process_context(
                    workspace_process_context=workspace_process_context,
                    host=None,
                    port=2343,
                    path_prefix="",
                )


def test_port_collision():
    def _raise_os_error():
        raise OSError("Address already in use")

    with mock.patch(
        "gevent.pywsgi.WSGIServer", new=_define_mock_server(_raise_os_error)
    ), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            with pytest.raises(Exception) as exc_info:
                host_dagit_ui_with_workspace_process_context(
                    workspace_process_context=workspace_process_context,
                    host=None,
                    port=2343,
                    port_lookup=False,
                    path_prefix="",
                )

            assert "another instance of dagit " in str(exc_info.value)


def test_invalid_path_prefix():
    with mock.patch("gevent.pywsgi.WSGIServer"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            with pytest.raises(Exception) as exc_info:
                host_dagit_ui_with_workspace_process_context(
                    workspace_process_context=workspace_process_context,
                    host=None,
                    port=2343,
                    port_lookup=False,
                    path_prefix="no-leading-slash",
                )
            assert "path prefix should begin with a leading" in str(exc_info.value)

            with pytest.raises(Exception) as exc_info:
                host_dagit_ui_with_workspace_process_context(
                    workspace_process_context=workspace_process_context,
                    host=None,
                    port=2343,
                    port_lookup=False,
                    path_prefix="/extra-trailing-slash/",
                )
            assert "path prefix should not include a trailing" in str(exc_info.value)


def test_valid_path_prefix():
    with mock.patch("gevent.pywsgi.WSGIServer"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagit_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                port_lookup=False,
                path_prefix="/dagster-path",
            )


@mock.patch("gevent.pywsgi.WSGIServer.serve_forever")
def test_dagit_logs(
    server_mock,
    caplog,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir):
            runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
            workspace_path = file_relative_path(__file__, "telemetry_repository.yaml")
            result = runner.invoke(
                ui,
                ["-w", workspace_path],
            )
            assert result.exit_code == 0, str(result.exception)

            expected_repo_stats = {
                hash_name("test_repository"): 1,
                hash_name("dagster_test_repository"): 4,
            }
            actions = set()
            for record in caplog.records:
                message = json.loads(record.getMessage())
                actions.add(message.get("action"))
                if message.get("action") == UPDATE_REPO_STATS:
                    assert message.get("pipeline_name_hash") == ""
                    repo_hash = message.get("repo_hash")

                    assert repo_hash in expected_repo_stats
                    expected_num_pipelines_in_repo = expected_repo_stats.get(repo_hash)
                    assert message.get("num_pipelines_in_repo") == str(
                        expected_num_pipelines_in_repo
                    )

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
            assert len(caplog.records) == 3
            assert server_mock.call_args_list == [mock.call()]

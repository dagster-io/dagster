import json
import tempfile
from unittest import mock

import pytest
from click.testing import CliRunner
from dagster._core.instance import DagsterInstance
from dagster._core.telemetry import START_DAGSTER_WEBSERVER, UPDATE_REPO_STATS, hash_name
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths
from dagster._utils import file_relative_path
from dagster._utils.log import get_structlog_json_formatter
from dagster_shared import seven
from dagster_webserver.app import create_app_from_workspace_process_context
from dagster_webserver.cli import (
    DEFAULT_WEBSERVER_PORT,
    dagster_webserver,
    host_dagster_ui_with_workspace_process_context,
)
from starlette.testclient import TestClient


@pytest.fixture
def instance():
    with instance_for_test() as the_instance:
        yield the_instance


def test_create_app_with_workspace(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance,
        [file_relative_path(__file__, "./workspace.yaml")],
    ) as workspace_process_context:
        assert create_app_from_workspace_process_context(workspace_process_context)


def test_create_app_with_multiple_workspace_files(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance,
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


@pytest.mark.parametrize("url_path", ["notebook", "dagit/notebook"])
def test_notebook_view(url_path):
    notebook_path = file_relative_path(__file__, "render_uuid_notebook.ipynb")

    with instance_for_test() as instance:
        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            client = TestClient(
                create_app_from_workspace_process_context(
                    workspace_process_context,
                )
            )
            res = client.get(f"/{url_path}?path={notebook_path}&repoLocName=load_from_file")

            assert res.status_code == 200
            # This magic guid is hardcoded in the notebook
            assert b"6cac0c38-2c97-49ca-887c-4ac43f141213" in res.content


def test_index_view(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance, [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        client = TestClient(create_app_from_workspace_process_context(workspace_process_context))
        res = client.get("/")

        assert res.status_code == 200, res.content
        assert b"<title>Dagster</title>" in res.content


def test_index_view_at_path_prefix(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance, [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        client = TestClient(
            create_app_from_workspace_process_context(workspace_process_context, "/dagster-path"),
        )
        # / redirects to prefixed path
        res = client.get("/")
        assert res.status_code == 200

        # index contains the path meta tag
        res = client.get("/dagster-path/")
        assert res.status_code == 200

        assert b'"pathPrefix": "/dagster-path",' in res.content


def test_graphql_view(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance, [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        client = TestClient(
            create_app_from_workspace_process_context(
                workspace_process_context,
            )
        )
        res = client.get("/graphql")
        assert b"No GraphQL query found in the request" in res.content


def test_graphql_view_at_path_prefix(instance):
    with load_workspace_process_context_from_yaml_paths(
        instance, [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        client = TestClient(
            create_app_from_workspace_process_context(workspace_process_context, "/dagster-path"),
        )

        res = client.get("/dagster-path/graphql")
        assert b"No GraphQL query found in the request" in res.content


def test_successful_host_dagster_ui_from_workspace():
    with mock.patch("uvicorn.run") as server_call, tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagster_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="",
                log_level="warning",
            )

        server_call.assert_called_with(mock.ANY, host="127.0.0.1", port=2343, log_level="warning")


@pytest.fixture
def mock_is_port_in_use():
    with mock.patch("dagster_webserver.cli.is_port_in_use") as mock_is_port_in_use:
        yield mock_is_port_in_use


@pytest.fixture
def mock_find_free_port():
    with mock.patch("dagster_webserver.cli.find_free_port") as mock_find_free_port:
        mock_find_free_port.return_value = 1234
        yield mock_find_free_port


def test_host_dagster_webserver_choose_port(mock_is_port_in_use, mock_find_free_port):
    with mock.patch("uvicorn.run") as server_call, tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        mock_is_port_in_use.return_value = False

        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagster_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=None,
                path_prefix="",
                log_level="warning",
            )

        server_call.assert_called_with(
            mock.ANY, host="127.0.0.1", port=DEFAULT_WEBSERVER_PORT, log_level="warning"
        )

        mock_is_port_in_use.return_value = True
        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagster_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=None,
                path_prefix="",
                log_level="warning",
            )

        server_call.assert_called_with(mock.ANY, host="127.0.0.1", port=1234, log_level="warning")


def test_successful_host_dagster_ui_from_multiple_workspace_files():
    with mock.patch("uvicorn.run"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance,
            [
                file_relative_path(__file__, "./workspace.yaml"),
                file_relative_path(__file__, "./override.yaml"),
            ],
        ) as workspace_process_context:
            host_dagster_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="",
                log_level="warning",
            )


def test_successful_host_dagster_ui_from_legacy_repository():
    with mock.patch("uvicorn.run"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagster_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="",
                log_level="warning",
            )


def test_invalid_path_prefix():
    with mock.patch("uvicorn.run"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            with pytest.raises(Exception) as exc_info:
                host_dagster_ui_with_workspace_process_context(
                    workspace_process_context=workspace_process_context,
                    host=None,
                    port=2343,
                    path_prefix="no-leading-slash",
                    log_level="warning",
                )
            assert "path prefix should begin with a leading" in str(exc_info.value)

            with pytest.raises(Exception) as exc_info:
                host_dagster_ui_with_workspace_process_context(
                    workspace_process_context=workspace_process_context,
                    host=None,
                    port=2343,
                    path_prefix="/extra-trailing-slash/",
                    log_level="warning",
                )
            assert "path prefix should not include a trailing" in str(exc_info.value)


def test_valid_path_prefix():
    with mock.patch("uvicorn.run"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagster_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="/dagster-path",
                log_level="warning",
            )


@mock.patch("uvicorn.run")
def test_dagster_webserver_logs(_, caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir, overrides={"telemetry": {"enabled": True}}):
            runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
            workspace_path = file_relative_path(__file__, "telemetry_repository.yaml")
            result = runner.invoke(
                dagster_webserver,
                ["-w", workspace_path],
            )
            assert result.exit_code == 0, str(result.exception)

            expected_repo_stats = {
                hash_name("test_repository"): 1,
                hash_name("dagster_test_repository"): 6,
            }
            actions = set()
            records = []
            for record in caplog.records:
                try:
                    message = json.loads(record.getMessage())
                except seven.JSONDecodeError:
                    continue

                records.append(record)

                actions.add(message.get("action"))
                if message.get("action") == UPDATE_REPO_STATS:
                    metadata = message.get("metadata")
                    assert metadata.get("pipeline_name_hash") == ""
                    repo_hash = metadata.get("repo_hash")

                    assert repo_hash in expected_repo_stats
                    expected_num_jobs_in_repo = expected_repo_stats.get(repo_hash)
                    assert metadata.get("num_pipelines_in_repo") == str(expected_num_jobs_in_repo)

                assert set(message.keys()) == set(
                    [
                        "action",
                        "client_time",
                        "elapsed_time",
                        "event_id",
                        "instance_id",
                        "python_version",
                        "run_storage_id",
                        "metadata",
                        "dagster_version",
                        "os_desc",
                        "os_platform",
                        "is_known_ci_env",
                    ]
                )

            assert actions == set([START_DAGSTER_WEBSERVER, UPDATE_REPO_STATS])
            assert len(records) == 3


@mock.patch("uvicorn.run")
def test_dagster_webserver_json_logs(
    _: mock.Mock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # https://github.com/pytest-dev/pytest/issues/2987#issuecomment-1460509126
    #
    # pytest captures log records using their handler. However, as a side-effect, this prevents
    # Dagster's log formatting from being applied in a unit test.
    #
    # To test the formatting, we monkeypatch the handler's formatter to use the same formatter as
    # the one used by Dagster when enabling JSON log format.
    monkeypatch.setattr(caplog.handler, "formatter", get_structlog_json_formatter())

    runner = CliRunner()
    result = runner.invoke(dagster_webserver, ["--log-format", "json", "--empty-workspace"])

    assert result.exit_code == 0, str(result.exception)

    lines = [line for line in caplog.text.split("\n") if line]

    assert lines
    assert [json.loads(line) for line in lines]


@mock.patch("uvicorn.run")
def test_dagster_webserver_rich_logs(_: mock.Mock) -> None:
    runner = CliRunner()
    result = runner.invoke(dagster_webserver, ["--log-format", "rich", "--empty-workspace"])

    # Test that the webserver can be started with rich formatting.
    assert result.exit_code == 0, str(result.exception)

import json
import tempfile
from unittest import mock

import pytest
from click.testing import CliRunner
from dagit.app import create_app_from_workspace_process_context
from dagit.cli import dagit, host_dagit_ui_with_workspace_process_context
from starlette.testclient import TestClient

from dagster import _seven
from dagster._utils import file_relative_path
from dagster._core.instance import DagsterInstance
from dagster._core.telemetry import START_DAGIT_WEBSERVER, UPDATE_REPO_STATS, hash_name
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths


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
        client = TestClient(
            create_app_from_workspace_process_context(
                workspace_process_context,
            )
        )
        res = client.get(f"/dagit/notebook?path={notebook_path}&repoLocName=load_from_file")

        assert res.status_code == 200
        # This magic guid is hardcoded in the notebook
        assert b"6cac0c38-2c97-49ca-887c-4ac43f141213" in res.content


def test_index_view():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        client = TestClient(create_app_from_workspace_process_context(workspace_process_context))
        res = client.get("/")

        assert res.status_code == 200, res.content
        assert b"You need to enable JavaScript to run this app" in res.content


def test_index_view_at_path_prefix():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
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

        assert b"You need to enable JavaScript to run this app" in res.content
        assert b'{"pathPrefix": "/dagster-path"' in res.content


def test_graphql_view():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        client = TestClient(
            create_app_from_workspace_process_context(
                workspace_process_context,
            )
        )
        res = client.get("/graphql")
        assert b"No GraphQL query found in the request" in res.content


def test_graphql_view_at_path_prefix():
    with load_workspace_process_context_from_yaml_paths(
        DagsterInstance.ephemeral(), [file_relative_path(__file__, "./workspace.yaml")]
    ) as workspace_process_context:
        client = TestClient(
            create_app_from_workspace_process_context(workspace_process_context, "/dagster-path"),
        )

        res = client.get("/dagster-path/graphql")
        assert b"No GraphQL query found in the request" in res.content


def test_successful_host_dagit_ui_from_workspace():
    with mock.patch("uvicorn.run"), tempfile.TemporaryDirectory() as temp_dir:

        instance = DagsterInstance.local_temp(temp_dir)

        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagit_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="",
                log_level="warning",
            )


def test_successful_host_dagit_ui_from_multiple_workspace_files():
    with mock.patch("uvicorn.run"), tempfile.TemporaryDirectory() as temp_dir:
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
                log_level="warning",
            )


def test_successful_host_dagit_ui_from_legacy_repository():
    with mock.patch("uvicorn.run"), tempfile.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./workspace.yaml")]
        ) as workspace_process_context:
            host_dagit_ui_with_workspace_process_context(
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
                host_dagit_ui_with_workspace_process_context(
                    workspace_process_context=workspace_process_context,
                    host=None,
                    port=2343,
                    path_prefix="no-leading-slash",
                    log_level="warning",
                )
            assert "path prefix should begin with a leading" in str(exc_info.value)

            with pytest.raises(Exception) as exc_info:
                host_dagit_ui_with_workspace_process_context(
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
            host_dagit_ui_with_workspace_process_context(
                workspace_process_context=workspace_process_context,
                host=None,
                port=2343,
                path_prefix="/dagster-path",
                log_level="warning",
            )


@mock.patch("uvicorn.run")
def test_dagit_logs(_, caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir, overrides={"telemetry": {"enabled": True}}):
            runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
            workspace_path = file_relative_path(__file__, "telemetry_repository.yaml")
            result = runner.invoke(
                dagit,
                ["-w", workspace_path],
            )
            assert result.exit_code == 0, str(result.exception)

            expected_repo_stats = {
                hash_name("test_repository"): 1,
                hash_name("dagster_test_repository"): 4,
            }
            actions = set()
            records = []
            for record in caplog.records:
                try:
                    message = json.loads(record.getMessage())
                except _seven.JSONDecodeError:
                    continue

                records.append(record)

                actions.add(message.get("action"))
                if message.get("action") == UPDATE_REPO_STATS:
                    metadata = message.get("metadata")
                    assert metadata.get("pipeline_name_hash") == ""
                    repo_hash = metadata.get("repo_hash")

                    assert repo_hash in expected_repo_stats
                    expected_num_pipelines_in_repo = expected_repo_stats.get(repo_hash)
                    assert metadata.get("num_pipelines_in_repo") == str(
                        expected_num_pipelines_in_repo
                    )

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
                    ]
                )

            assert actions == set([START_DAGIT_WEBSERVER, UPDATE_REPO_STATS])
            assert len(records) == 3

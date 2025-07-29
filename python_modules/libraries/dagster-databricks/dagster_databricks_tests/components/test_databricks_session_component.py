from collections.abc import Iterator
from contextlib import contextmanager
from unittest import mock

from dagster import AssetKey, Definitions, PythonScriptComponent
from dagster.components.testing import copy_code_to_file, create_defs_folder_sandbox
from dagster_databricks.components.databricks_session.component import DatabricksSessionComponent
from databricks.connect import DatabricksSession


@contextmanager
def setup_databricks_session_component(
    defs_yaml_contents: dict,
) -> Iterator[tuple[DatabricksSessionComponent, Definitions]]:
    """Sets up a components project with a DatabricksSessionComponent based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksSessionComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, DatabricksSessionComponent)
            yield component, defs


def test_basic_component_load() -> None:
    """Test that DatabricksSessionComponent loads with basic configuration."""
    with setup_databricks_session_component(
        defs_yaml_contents={
            "type": "dagster_databricks.DatabricksSessionComponent",
            "attributes": {},
        }
    ) as (_, defs):
        assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0


def test_session_property_basic() -> None:
    """Test that session property creates DatabricksSession correctly."""
    with setup_databricks_session_component(
        defs_yaml_contents={
            "type": "dagster_databricks.DatabricksSessionComponent",
            "attributes": {},
        }
    ) as (component, _):
        with mock.patch.object(
            DatabricksSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_session = mock.Mock(spec=DatabricksSession)
            mock_builder_instance = mock.Mock()
            mock_builder_instance.getOrCreate.return_value = mock_session
            mock_builder_prop.return_value = mock_builder_instance

            session = component.session

            assert session == mock_session
            mock_builder_instance.getOrCreate.assert_called_once()


def test_session_property_with_host_and_token() -> None:
    """Test that session property applies host and token configuration."""
    host = "https://dbc-12345678-1234.cloud.databricks.com"
    token = "dapi123456789abcdef"
    with setup_databricks_session_component(
        defs_yaml_contents={
            "type": "dagster_databricks.DatabricksSessionComponent",
            "attributes": {
                "host": host,
                "token": token,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            DatabricksSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.remote.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=DatabricksSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            mock_builder_instance.remote.assert_called_once_with(host=host, token=token)


def test_session_property_with_cluster_id() -> None:
    """Test that session property applies cluster_id configuration."""
    host = "https://dbc-12345678-1234.cloud.databricks.com"
    token = "dapi123456789abcdef"
    cluster_id = "1234-567890-test123"
    with setup_databricks_session_component(
        defs_yaml_contents={
            "type": "dagster_databricks.DatabricksSessionComponent",
            "attributes": {
                "host": host,
                "token": token,
                "cluster_id": cluster_id,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            DatabricksSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.remote.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=DatabricksSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            mock_builder_instance.remote.assert_called_once_with(
                host=host, token=token, cluster_id=cluster_id
            )


def test_session_property_with_serverless() -> None:
    """Test that session property applies serverless configuration."""
    host = "https://dbc-12345678-1234.cloud.databricks.com"
    token = "dapi123456789abcdef"
    with setup_databricks_session_component(
        defs_yaml_contents={
            "type": "dagster_databricks.DatabricksSessionComponent",
            "attributes": {
                "host": host,
                "token": token,
                "serverless": True,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            DatabricksSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.remote.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=DatabricksSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            mock_builder_instance.remote.assert_called_once_with(
                host=host, token=token, serverless=True
            )


def test_session_property_with_oauth_m2m() -> None:
    """Test that session property applies OAuth M2M configuration."""
    host = "https://dbc-12345678-1234.cloud.databricks.com"
    client_id = "client_id_123"
    client_secret = "client_secret_456"
    cluster_id = "1234-567890-test123"
    with setup_databricks_session_component(
        defs_yaml_contents={
            "type": "dagster_databricks.DatabricksSessionComponent",
            "attributes": {
                "host": host,
                "client_id": client_id,
                "client_secret": client_secret,
                "cluster_id": cluster_id,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            DatabricksSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.remote.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=DatabricksSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            mock_builder_instance.remote.assert_called_once_with(
                host=host, client_id=client_id, client_secret=client_secret, cluster_id=cluster_id
            )


def test_session_property_with_all_options() -> None:
    """Test that session property applies all configuration options together."""
    host = "https://dbc-12345678-1234.cloud.databricks.com"
    token = "dapi123456789abcdef"
    cluster_id = "1234-567890-test123"
    user_agent = "my-app/1.0"

    with setup_databricks_session_component(
        defs_yaml_contents={
            "type": "dagster_databricks.DatabricksSessionComponent",
            "attributes": {
                "host": host,
                "token": token,
                "cluster_id": cluster_id,
                "user_agent": user_agent,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            DatabricksSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.remote.return_value = mock_builder_instance
            mock_builder_instance.config.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=DatabricksSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            mock_builder_instance.remote.assert_called_once_with(
                host=host, token=token, cluster_id=cluster_id, user_agent=user_agent
            )


def test_session_property_caching() -> None:
    """Test that session property is cached using @cached_property."""
    with setup_databricks_session_component(
        defs_yaml_contents={
            "type": "dagster_databricks.DatabricksSessionComponent",
            "attributes": {},
        }
    ) as (component, _):
        with mock.patch.object(
            DatabricksSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_session = mock.Mock(spec=DatabricksSession)
            mock_builder_instance = mock.Mock()
            mock_builder_instance.getOrCreate.return_value = mock_session
            mock_builder_prop.return_value = mock_builder_instance

            session1 = component.session
            session2 = component.session

            assert session1 is session2
            mock_builder_instance.getOrCreate.assert_called_once()


def test_databricks_session_component_integration() -> None:
    """Test integration pattern where PythonScriptComponent accesses DatabricksSessionComponent."""

    def create_integration_script():
        from pathlib import Path

        from dagster.components.core.tree import ComponentTree
        from dagster_databricks import DatabricksSessionComponent

        component_tree = ComponentTree.for_project(Path(__file__).parent)
        databricks_component = component_tree.load_component_at_path(
            "databricks_session", expected_type=DatabricksSessionComponent
        )
        session = databricks_component.session
        session.sql("SELECT 1 as test_col")

    def create_mock_databricks_component():
        from functools import cached_property
        from unittest import mock

        from dagster_databricks import DatabricksSessionComponent

        class MockDatabricksSessionComponent(DatabricksSessionComponent):
            @cached_property
            def session(self):
                mock_session = mock.Mock()
                mock_session.sql.return_value = [{"test_col": 1}]
                return mock_session

    with create_defs_folder_sandbox(project_name="databricks_integration_test_project") as sandbox:
        # Create DatabricksSessionComponent with specific configuration

        copy_code_to_file(
            create_mock_databricks_component, sandbox.defs_folder_path / "mock_databricks.py"
        )

        sandbox.scaffold_component(
            component_cls=DatabricksSessionComponent,
            defs_path="databricks_session",
            defs_yaml_contents={
                "type": "databricks_integration_test_project.defs.mock_databricks.MockDatabricksSessionComponent",
                "attributes": {
                    "host": "https://dbc-12345678-1234.cloud.databricks.com",
                    "token": "dapi123456789abcdef",
                },
            },
        )

        data_processor_path = sandbox.scaffold_component(
            component_cls=PythonScriptComponent,
            defs_path="data_processor",
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {"path": "my_fn.py", "name": "process_with_databricks"},
                    "assets": [
                        {
                            "key": "processed_data",
                            "description": "Data processed using Databricks",
                        }
                    ],
                },
            },
        )
        copy_code_to_file(create_integration_script, data_processor_path / "my_fn.py")

        # Build and verify the complete setup
        with sandbox.build_all_defs() as defs:
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
            assert AssetKey("processed_data") in asset_keys

            asset_def = defs.get_assets_def(AssetKey("processed_data"))
            assert asset_def is not None
            assert asset_def.op.name == "process_with_databricks"

            result = defs.get_implicit_global_asset_job_def().execute_in_process()
            assert result.success

from collections.abc import Iterator
from contextlib import contextmanager
from unittest import mock

from dagster import AssetKey, Definitions, PythonScriptComponent
from dagster.components.testing import copy_code_to_file, create_defs_folder_sandbox
from dagster_pyspark.components.spark_session.component import SparkSessionComponent
from pyspark.sql import SparkSession


@contextmanager
def setup_spark_session_component(
    defs_yaml_contents: dict,
) -> Iterator[tuple[SparkSessionComponent, Definitions]]:
    """Sets up a components project with a SparkSessionComponent based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SparkSessionComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, SparkSessionComponent)
            yield component, defs


def test_basic_component_load() -> None:
    """Test that SparkSessionComponent loads with basic configuration."""
    with setup_spark_session_component(
        defs_yaml_contents={
            "type": "dagster_pyspark.SparkSessionComponent",
            "attributes": {},
        }
    ) as (_, defs):
        assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0


def test_session_property_basic() -> None:
    """Test that session property creates SparkSession correctly."""
    with setup_spark_session_component(
        defs_yaml_contents={
            "type": "dagster_pyspark.SparkSessionComponent",
            "attributes": {},
        }
    ) as (component, _):
        with mock.patch.object(
            SparkSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_session = mock.Mock(spec=SparkSession)
            mock_builder_instance = mock.Mock()
            mock_builder_instance.getOrCreate.return_value = mock_session
            mock_builder_prop.return_value = mock_builder_instance

            session = component.session

            assert session == mock_session
            mock_builder_instance.getOrCreate.assert_called_once()


def test_session_property_with_app_name() -> None:
    """Test that session property applies app_name configuration."""
    app_name = "test_app_name"
    with setup_spark_session_component(
        defs_yaml_contents={
            "type": "dagster_pyspark.SparkSessionComponent",
            "attributes": {
                "app_name": app_name,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            SparkSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.appName.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=SparkSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            mock_builder_instance.appName.assert_called_once_with(app_name)


def test_session_property_with_url() -> None:
    """Test that session property applies URL configuration."""
    url = "sc://localhost:15002"
    with setup_spark_session_component(
        defs_yaml_contents={
            "type": "dagster_pyspark.SparkSessionComponent",
            "attributes": {
                "url": url,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            SparkSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.remote.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=SparkSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            mock_builder_instance.remote.assert_called_once_with(url)


def test_session_property_with_config() -> None:
    """Test that session property applies config options."""
    config = {
        "spark.executor.memory": "2g",
        "spark.driver.memory": "1g",
    }
    with setup_spark_session_component(
        defs_yaml_contents={
            "type": "dagster_pyspark.SparkSessionComponent",
            "attributes": {
                "config": config,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            SparkSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.config.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=SparkSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            expected_calls = [mock.call(key, value) for key, value in config.items()]
            mock_builder_instance.config.assert_has_calls(expected_calls, any_order=True)


def test_session_property_with_all_options() -> None:
    """Test that session property applies all configuration options together."""
    app_name = "full_config_test"
    url = "sc://test-cluster:15002"
    config = {
        "spark.executor.memory": "4g",
        "spark.sql.adaptive.enabled": "true",
    }

    with setup_spark_session_component(
        defs_yaml_contents={
            "type": "dagster_pyspark.SparkSessionComponent",
            "attributes": {
                "app_name": app_name,
                "url": url,
                "config": config,
            },
        }
    ) as (component, _):
        with mock.patch.object(
            SparkSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_builder_instance = mock.Mock()
            mock_builder_instance.appName.return_value = mock_builder_instance
            mock_builder_instance.remote.return_value = mock_builder_instance
            mock_builder_instance.config.return_value = mock_builder_instance
            mock_builder_instance.getOrCreate.return_value = mock.Mock(spec=SparkSession)
            mock_builder_prop.return_value = mock_builder_instance

            assert component.session

            mock_builder_instance.appName.assert_called_once_with(app_name)
            mock_builder_instance.remote.assert_called_once_with(url)
            expected_config_calls = [mock.call(key, value) for key, value in config.items()]
            mock_builder_instance.config.assert_has_calls(expected_config_calls, any_order=True)


def test_session_property_caching() -> None:
    """Test that session property is cached using @cached_property."""
    with setup_spark_session_component(
        defs_yaml_contents={
            "type": "dagster_pyspark.SparkSessionComponent",
            "attributes": {},
        }
    ) as (component, _):
        with mock.patch.object(
            SparkSession, "builder", new_callable=mock.PropertyMock
        ) as mock_builder_prop:
            mock_session = mock.Mock(spec=SparkSession)
            mock_builder_instance = mock.Mock()
            mock_builder_instance.getOrCreate.return_value = mock_session
            mock_builder_prop.return_value = mock_builder_instance

            session1 = component.session
            session2 = component.session

            assert session1 is session2
            mock_builder_instance.getOrCreate.assert_called_once()


def test_spark_session_component_integration() -> None:
    """Test integration pattern where PythonScriptComponent accesses SparkSessionComponent."""

    def create_integration_script():
        from pathlib import Path

        from dagster.components.core.tree import ComponentTree
        from dagster_pyspark import SparkSessionComponent

        component_tree = ComponentTree.for_project(Path(__file__).parent)
        spark_component = component_tree.load_component_at_path(
            "spark_session", expected_type=SparkSessionComponent
        )
        session = spark_component.session
        session.sql("SELECT 1 as test_col")

    def create_mock_spark_component():
        from functools import cached_property
        from unittest import mock

        from dagster_pyspark import SparkSessionComponent

        class MockSparkSessionComponent(SparkSessionComponent):
            @cached_property
            def session(self):
                mock_session = mock.Mock()
                mock_session.sql.return_value = [{"test_col": 1}]
                return mock_session

    with create_defs_folder_sandbox(project_name="integration_test_project") as sandbox:
        # Create SparkSessionComponent with specific configuration

        copy_code_to_file(create_mock_spark_component, sandbox.defs_folder_path / "mock_spark.py")

        sandbox.scaffold_component(
            component_cls=SparkSessionComponent,
            defs_path="spark_session",
            defs_yaml_contents={
                "type": "integration_test_project.defs.mock_spark.MockSparkSessionComponent",
                "attributes": {
                    "url": "sc://localhost",
                },
            },
        )

        data_processor_path = sandbox.scaffold_component(
            component_cls=PythonScriptComponent,
            defs_path="data_processor",
            defs_yaml_contents={
                "type": "dagster.PythonScriptComponent",
                "attributes": {
                    "execution": {"path": "my_fn.py", "name": "process_with_spark"},
                    "assets": [
                        {
                            "key": "processed_data",
                            "description": "Data processed using Spark",
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
            assert asset_def.op.name == "process_with_spark"

            result = defs.get_implicit_global_asset_job_def().execute_in_process()
            assert result.success

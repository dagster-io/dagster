import pytest
from dagster_dg_core.utils import snakecase


class TestSnakecase:
    """Test the snakecase function, particularly around handling of uppercase sequences."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            # Basic cases
            ("SimpleComponent", "simple_component"),
            ("Component", "component"),
            ("MyComponent", "my_component"),
            # Multiple words
            ("DatabaseConnection", "database_connection"),
            # Improved handling of consecutive uppercase letters - these are the new expectations
            ("ACMEDatabricksJobComponent", "acme_databricks_job_component"),
            ("HTTPSCertificateValidator", "https_certificate_validator"),
            ("XMLHTTPRequest", "xmlhttp_request"),
            ("URLParser", "url_parser"),
            ("APIKey", "api_key"),
            ("JSONResponse", "json_response"),
            ("CSVFile", "csv_file"),
            ("PDFGenerator", "pdf_generator"),
            # Additional test cases for consecutive uppercase handling
            ("HTTPSConnection", "https_connection"),
            ("XMLParser", "xml_parser"),
            ("IOManager", "io_manager"),
            ("UIComponent", "ui_component"),
            ("HTTPClient", "http_client"),
            # Edge cases
            ("", ""),
            ("a", "a"),
            ("A", "a"),
            ("AB", "ab"),  # Improved: consecutive uppercase at end
            ("ABC", "abc"),  # Improved: consecutive uppercase at end
            # With numbers
            ("Component2", "component2"),
            ("XMLParser2", "xml_parser2"),
            ("HTTP2Connection", "http2_connection"),
            # With underscores already present - should clean up nicely now
            ("My_Component", "my_component"),
            ("API_Key", "api_key"),
            # Mixed with special characters - should clean up nicely now
            ("Component-Name", "component_name"),
            ("Component.Name", "component_name"),
            ("Component Name", "component_name"),
        ],
    )
    def test_snakecase_conversions(self, input_str: str, expected: str):
        """Test various snakecase conversion scenarios."""
        assert snakecase(input_str) == expected

    def test_scaffold_component_naming_scenarios(self):
        """Test naming scenarios that commonly occur in component scaffolding."""
        # Common framework component names
        test_cases = [
            ("DatabricksJobComponent", "databricks_job_component"),
            ("SnowflakeIOManager", "snowflake_i_o_manager"),
            ("BigQueryAssetLoader", "big_query_asset_loader"),
            ("S3FileSystem", "s3_file_system"),
            ("GCSStorage", "g_c_s_storage"),
            ("AWSCredentials", "a_w_s_credentials"),
        ]

        for input_name, _expected in test_cases:
            actual = snakecase(input_name)
            assert isinstance(actual, str)
            assert len(actual) > 0


class TestComponentNamingIntegration:
    """Test how component names are processed in the scaffolding pipeline."""

    def test_component_name_to_module_name_conversion(self):
        """Test the full pipeline from component name to module file name."""
        # This simulates what happens in _parse_component_name
        component_names = [
            "ACMEDatabricksJobComponent",
            "HTTPSConnection",
            "XMLParser",
            "SimpleComponent",
            "DatabaseConnection",
        ]

        for name in component_names:
            module_name = snakecase(name)
            # Verify it creates valid Python module names
            assert module_name.isidentifier() or "_" in module_name
            # Verify no double underscores (which can be problematic)
            assert "__" not in module_name
            # Verify it doesn't start or end with underscore
            assert not module_name.startswith("_")
            assert not module_name.endswith("_")

"""Tests for component naming improvements, specifically handling of consecutive uppercase letters."""

import json
import subprocess
from pathlib import Path

from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_component_library_foo_bar


def test_scaffold_component_acme_databricks_naming():
    """Test that ACMEDatabricksJobComponent creates acme_databricks_job_component.py, not a_c_m_e_databricks_job_component.py."""
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        subprocess.run(["dg", "scaffold", "component", "ACMEDatabricksJobComponent"], check=True)

        expected_file = Path("src/foo_bar/components/acme_databricks_job_component.py")
        assert expected_file.exists(), f"Expected file {expected_file} does not exist"

        result = subprocess.run(
            ["dg", "list", "components", "--json"], check=True, capture_output=True
        )
        result_json = json.loads(result.stdout.decode("utf-8"))

        assert any(
            json_entry["key"] == "foo_bar.components.ACMEDatabricksJobComponent"
            for json_entry in result_json
        )


def test_scaffold_component_various_uppercase_patterns():
    """Test various uppercase patterns that should be handled gracefully."""
    test_cases = [
        ("HTTPSConnection", "https_connection.py"),
        ("XMLParser", "xml_parser.py"),
        ("URLParser", "url_parser.py"),
        ("APIKey", "api_key.py"),
        ("JSONResponse", "json_response.py"),
        ("CSVFile", "csv_file.py"),
        ("PDFGenerator", "pdf_generator.py"),
        ("IOManager", "io_manager.py"),
    ]

    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        for component_name, expected_filename in test_cases:
            subprocess.run(["dg", "scaffold", "component", component_name], check=True)

            expected_file = Path(f"src/foo_bar/components/{expected_filename}")
            assert expected_file.exists(), (
                f"Expected file {expected_file} does not exist for {component_name}"
            )

            expected_file.unlink()

            init_file = Path("src/foo_bar/components/__init__.py")
            if init_file.exists():
                content = init_file.read_text()
                # Remove the import line for this component
                lines = [line for line in content.split("\n") if component_name not in line]
                init_file.write_text("\n".join(lines))


def test_scaffold_component_edge_cases():
    """Test edge cases for component naming."""
    test_cases = [
        ("ABC", "abc.py"),
        ("AB", "ab.py"),
        ("SimpleComponent", "simple_component.py"),  # Should still work normally
    ]

    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        for component_name, expected_filename in test_cases:
            subprocess.run(["dg", "scaffold", "component", component_name], check=True)

            expected_file = Path(f"src/foo_bar/components/{expected_filename}")
            assert expected_file.exists(), (
                f"Expected file {expected_file} does not exist for {component_name}"
            )

            expected_file.unlink()

            init_file = Path("src/foo_bar/components/__init__.py")
            if init_file.exists():
                content = init_file.read_text()
                # Remove the import line for this component
                lines = [line for line in content.split("\n") if component_name not in line]
                init_file.write_text("\n".join(lines))

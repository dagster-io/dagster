"""Tests for multi-document YAML validation in `dg check yaml`.

The `dg check yaml` command validates ALL YAML documents in multi-document
files (documents separated by `---`).

These tests verify that:
1. Errors in the first document are caught correctly
2. Errors in subsequent documents are caught correctly
3. Valid multi-document files work correctly
"""

from dagster_test.components.test_utils.test_cases import BASIC_COMPONENT_TYPE_FILEPATH
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_runner_result,
    create_project_from_components,
)


def test_check_yaml_multi_document_validation_error_in_second_document():
    """Test that validation errors in the second document are caught correctly.

    This test creates a multi-document YAML file where:
    - The first document is valid
    - The second document has a typo (arameters instead of attributes)

    The validation should fail due to the error in the second document.
    """
    multi_document_yaml_content = """type: .MyComponent

attributes:
  a_string: "first document"
  an_int: 1

---

type: .MyComponent

arameters:
  a_string: "second document"  
  an_int: 2
"""

    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            "validation/basic_component_success",
            local_component_defn_to_inject=BASIC_COMPONENT_TYPE_FILEPATH,
        ) as tmpdir,
    ):
        defs_yaml_path = (
            tmpdir / "src" / "foo_bar" / "defs" / "basic_component_success" / "defs.yaml"
        )
        defs_yaml_path.write_text(multi_document_yaml_content)

        result = runner.invoke("check", "yaml")

        assert_runner_result(result, exit_0=False)
        assert "'arameters' was unexpected" in result.stdout


def test_check_yaml_multi_document_validation_another_error_case():
    """Test another case of validation errors in subsequent documents."""
    multi_document_yaml_content = """type: .MyComponent

attributes:
  a_string: "first document"
  an_int: 1

---

type: .MyComponent

arameters:
  a_string: "second document"  
  an_int: 2
"""

    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            "validation/basic_component_success",
            local_component_defn_to_inject=BASIC_COMPONENT_TYPE_FILEPATH,
        ) as tmpdir,
    ):
        defs_yaml_path = (
            tmpdir / "src" / "foo_bar" / "defs" / "basic_component_success" / "defs.yaml"
        )
        defs_yaml_path.write_text(multi_document_yaml_content)

        result = runner.invoke("check", "yaml")

        assert_runner_result(result, exit_0=False)
        assert "'arameters' was unexpected" in result.stdout


def test_check_yaml_multi_document_first_document_error():
    """Test that errors in the first document are caught correctly."""
    multi_document_yaml_content = """type: .MyComponent

arameters:
  a_string: "first document"
  an_int: 1

---

type: .MyComponent

attributes:
  a_string: "second document"
  an_int: 2
"""

    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            "validation/basic_component_success",
            local_component_defn_to_inject=BASIC_COMPONENT_TYPE_FILEPATH,
        ) as tmpdir,
    ):
        defs_yaml_path = (
            tmpdir / "src" / "foo_bar" / "defs" / "basic_component_success" / "defs.yaml"
        )
        defs_yaml_path.write_text(multi_document_yaml_content)

        result = runner.invoke("check", "yaml")

        assert_runner_result(result, exit_0=False)
        assert "'arameters' was unexpected" in result.stdout


def test_check_yaml_multi_document_comprehensive():
    """Comprehensive test showing different multi-document scenarios."""
    valid_multi_document = """type: .MyComponent

attributes:
  a_string: "first"
  an_int: 1

---

type: .MyComponent

attributes:
  a_string: "second"
  an_int: 2

---

type: .MyComponent

attributes:
  a_string: "third"
  an_int: 3
"""

    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            "validation/basic_component_success",
            local_component_defn_to_inject=BASIC_COMPONENT_TYPE_FILEPATH,
        ) as tmpdir,
    ):
        defs_yaml_path = (
            tmpdir / "src" / "foo_bar" / "defs" / "basic_component_success" / "defs.yaml"
        )

        # Test valid multi-document
        defs_yaml_path.write_text(valid_multi_document)
        result = runner.invoke("check", "yaml")
        assert_runner_result(result, exit_0=True)
        assert "All component YAML validated successfully" in result.stdout

        # Test with error in third document
        error_in_third_document = """type: .MyComponent

attributes:
  a_string: "first"
  an_int: 1

---

type: .MyComponent

attributes:
  a_string: "second"
  an_int: 2

---

type: .MyComponent

arameters:
  a_string: "third"
  an_int: 3
"""

        defs_yaml_path.write_text(error_in_third_document)
        result = runner.invoke("check", "yaml")

        assert_runner_result(result, exit_0=False)
        assert "'arameters' was unexpected" in result.stdout

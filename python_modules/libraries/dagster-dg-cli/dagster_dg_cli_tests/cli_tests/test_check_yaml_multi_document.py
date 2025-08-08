"""Tests for multi-document YAML validation bug in `dg check yaml`.

BUG DESCRIPTION:
The `dg check yaml` command only validates the first YAML document in multi-document
files (documents separated by `---`). This is because the YAML parsing logic in
dagster_dg_core.check.parse_yaml_with_source_position() only returns the first document.

REPRODUCTION:
These tests demonstrate that:
1. Errors in the first document are caught correctly ✓
2. Errors in subsequent documents are NOT caught (BUG) ❌
3. Valid multi-document files work correctly ✓

EXPECTED FIX:
The YAML parsing should iterate through ALL documents in the file and validate each one.
"""

from dagster_dg_core_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    create_project_from_components,
)
from dagster_test.components.test_utils.test_cases import BASIC_COMPONENT_TYPE_FILEPATH


def test_check_yaml_multi_document_validation_bug():
    """Test that demonstrates the bug where only the first YAML document is validated in multi-document files.

    This test creates a multi-document YAML file where:
    - The first document is valid
    - The second document has a typo (arameters instead of attributes)

    BUG: This test currently PASSES when it should FAIL, demonstrating that only
    the first YAML document is being validated.

    TODO: When the bug is fixed, change the assertion to expect failure.
    """
    multi_document_yaml_content = """type: .MyComponent

attributes:
  a_string: "first document"
  an_int: 1

---

type: .MyComponent

# BUG: This typo in the second document should cause validation to fail
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
        # Replace the valid defs.yaml with our multi-document version containing the typo
        defs_yaml_path = (
            tmpdir / "src" / "foo_bar" / "defs" / "basic_component_success" / "defs.yaml"
        )
        defs_yaml_path.write_text(multi_document_yaml_content)

        result = runner.invoke("check", "yaml")

        # CURRENT BUG BEHAVIOR: This passes when it should fail
        # The validation succeeds because only the first document is checked
        assert_runner_result(result, exit_0=True)
        assert "All component YAML validated successfully" in result.stdout

        # Additional verification that the command output indicates success
        assert "error" not in result.stdout.lower()
        assert "unexpected" not in result.stdout.lower()


def test_check_yaml_multi_document_validation_bug_expected_behavior():
    """This test shows what SHOULD happen when the bug is fixed.

    This test will FAIL until the bug is fixed, demonstrating the expected behavior.
    When the bug is fixed, this test should pass.
    """
    multi_document_yaml_content = """type: .MyComponent

attributes:
  a_string: "first document"
  an_int: 1

---

type: .MyComponent

# This typo should cause validation to fail
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

        # EXPECTED BEHAVIOR: This should fail due to typo in second document
        assert_runner_result(result, exit_0=False)
        assert "'arameters' was unexpected" in result.stdout


def test_check_yaml_multi_document_first_document_error():
    """Test that errors in the first document are still caught (this works correctly)."""
    multi_document_yaml_content = """type: .MyComponent

# Typo in first document should be caught
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

        # This should fail correctly because the error is in the first document
        assert_runner_result(result, exit_0=False)
        assert "'arameters' was unexpected" in result.stdout


def test_check_yaml_multi_document_comprehensive():
    """Comprehensive test showing different multi-document scenarios."""
    # Test 1: Valid multi-document YAML should pass
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

        # Test with error in third document (should currently pass due to bug)
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

# BUG: This error in the third document is not caught
arameters:
  a_string: "third"
  an_int: 3
"""

        defs_yaml_path.write_text(error_in_third_document)
        result = runner.invoke("check", "yaml")

        # BUG: This passes when it should fail (error in third document not detected)
        assert_runner_result(result, exit_0=True)
        assert "All component YAML validated successfully" in result.stdout
        assert "arameters" not in result.stdout  # Error not reported

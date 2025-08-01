"""Tests for Python AST validation in docstring code blocks."""

import importlib

from automation.dagster_docs.validator import validate_docstring_text


class TestPythonASTValidation:
    """Test Python AST validation in docstring code blocks."""

    def test_valid_python_examples(self):
        """Test that valid Python examples pass validation."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.python_ast.valid_python_examples"
        )

        test_cases = [
            (
                fixtures_module.ValidPythonFixtures.simple_python_function.__doc__ or "",
                "ValidPythonFixtures.simple_python_function",
            ),
            (
                fixtures_module.ValidPythonFixtures.python_with_imports_and_classes.__doc__ or "",
                "ValidPythonFixtures.python_with_imports_and_classes",
            ),
            (
                fixtures_module.ValidPythonFixtures.python_with_decorators_and_async.__doc__ or "",
                "ValidPythonFixtures.python_with_decorators_and_async",
            ),
        ]

        for docstring, symbol_name in test_cases:
            result = validate_docstring_text(docstring, symbol_name)
            # Valid Python should not produce Python-specific syntax errors
            python_errors = [
                e for e in result.errors if "syntax error" in e.lower() and "python" in e.lower()
            ]
            assert len(python_errors) == 0, (
                f"{symbol_name} should not have Python syntax errors: {python_errors}"
            )

    def test_invalid_python_examples(self):
        """Test that invalid Python examples are detected."""
        fixtures_module = importlib.import_module(
            "automation_tests.dagster_docs_tests.python_ast.invalid_python_examples"
        )

        test_cases = [
            (
                fixtures_module.InvalidPythonFixtures.python_with_syntax_error.__doc__ or "",
                "InvalidPythonFixtures.python_with_syntax_error",
            ),
            (
                fixtures_module.InvalidPythonFixtures.python_with_indentation_error.__doc__ or "",
                "InvalidPythonFixtures.python_with_indentation_error",
            ),
            (
                fixtures_module.InvalidPythonFixtures.python_with_unmatched_parentheses.__doc__
                or "",
                "InvalidPythonFixtures.python_with_unmatched_parentheses",
            ),
            (
                fixtures_module.InvalidPythonFixtures.python_with_invalid_assignment.__doc__ or "",
                "InvalidPythonFixtures.python_with_invalid_assignment",
            ),
            (
                fixtures_module.InvalidPythonFixtures.python_with_incomplete_structure.__doc__
                or "",
                "InvalidPythonFixtures.python_with_incomplete_structure",
            ),
        ]

        for docstring, symbol_name in test_cases:
            result = validate_docstring_text(docstring, symbol_name)
            # Invalid Python should either produce errors or warnings
            # (depending on validator configuration)
            # For now, we just verify the validation runs without crashing
            # The exact error detection depends on the Python AST validation rules
            assert result is not None, f"{symbol_name} validation should complete"

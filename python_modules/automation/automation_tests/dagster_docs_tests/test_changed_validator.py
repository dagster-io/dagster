"""Tests for the changed_validator module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from automation.dagster_docs.changed_validator import (
    SymbolInfo,
    ValidationConfig,
    ValidationResult,
    extract_symbols_from_file,
    validate_changed_files,
    validate_symbols,
)
from automation.dagster_docs.path_converters import generic_path_converter
from automation.dagster_docs.validator import ValidationResult as ValidatorResult


class TestValidationConfig:
    def test_default_file_filter(self):
        config = ValidationConfig(
            root_path=Path("/test"),
            path_converter=generic_path_converter,
        )

        assert config.file_filter(Path("test.py")) is True
        assert config.file_filter(Path("test.txt")) is False
        assert config.file_filter(Path("test")) is False

    def test_custom_file_filter(self):
        custom_filter = lambda p: p.name.startswith("test_")
        config = ValidationConfig(
            root_path=Path("/test"),
            path_converter=generic_path_converter,
            file_filter=custom_filter,
        )

        assert config.file_filter(Path("test_module.py")) is True
        assert config.file_filter(Path("module.py")) is False


class TestSymbolInfo:
    def test_creation(self):
        symbol = SymbolInfo(
            symbol_path="test.module.Class",
            file_path=Path("/test/module.py"),
            line_number=10,
        )

        assert symbol.symbol_path == "test.module.Class"
        assert symbol.file_path == Path("/test/module.py")
        assert symbol.line_number == 10

    def test_optional_line_number(self):
        symbol = SymbolInfo(
            symbol_path="test.module.func",
            file_path=Path("/test/module.py"),
        )

        assert symbol.line_number is None


class TestValidationResult:
    def test_has_errors(self):
        result_with_errors = ValidationResult(
            symbol_info=SymbolInfo(symbol_path="test.Class", file_path=Path("/test.py")),
            errors=["Error 1", "Error 2"],
            warnings=[],
        )

        result_without_errors = ValidationResult(
            symbol_info=SymbolInfo(symbol_path="test.Class", file_path=Path("/test.py")),
            errors=[],
            warnings=["Warning 1"],
        )

        assert result_with_errors.has_errors() is True
        assert result_without_errors.has_errors() is False

    def test_has_warnings(self):
        result_with_warnings = ValidationResult(
            symbol_info=SymbolInfo(symbol_path="test.Class", file_path=Path("/test.py")),
            errors=[],
            warnings=["Warning 1"],
        )

        result_without_warnings = ValidationResult(
            symbol_info=SymbolInfo(symbol_path="test.Class", file_path=Path("/test.py")),
            errors=["Error 1"],
            warnings=[],
        )

        assert result_with_warnings.has_warnings() is True
        assert result_without_warnings.has_warnings() is False


class TestExtractSymbolsFromFile:
    def test_extract_class_with_docstring(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_module.py"
            test_file.write_text('''
class TestClass:
    """Test class docstring."""
    pass

def test_function():
    """Test function docstring."""
    pass

class NoDocClass:
    pass

def _private_function():
    """Private function - should be ignored."""
    pass
''')

            symbols = extract_symbols_from_file(test_file, "test_module")
            symbol_paths = {s.symbol_path for s in symbols}

            assert "test_module.TestClass" in symbol_paths
            assert "test_module.test_function" in symbol_paths
            assert "test_module.NoDocClass" not in symbol_paths
            assert "test_module._private_function" not in symbol_paths

    def test_extract_method_docstrings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_module.py"
            test_file.write_text('''
class TestClass:
    """Test class docstring."""
    
    def public_method(self):
        """Public method docstring."""
        pass
        
    def _private_method(self):
        """Private method - should be ignored."""
        pass
        
    def no_doc_method(self):
        pass
''')

            symbols = extract_symbols_from_file(test_file, "test_module")
            symbol_paths = {s.symbol_path for s in symbols}

            assert "test_module.TestClass" in symbol_paths
            assert "test_module.TestClass.public_method" in symbol_paths
            assert "test_module.TestClass._private_method" not in symbol_paths
            assert "test_module.TestClass.no_doc_method" not in symbol_paths

    def test_import_error_handling(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "broken_module.py"
            test_file.write_text('import nonexistent_module\nraise RuntimeError("broken")')

            symbols = extract_symbols_from_file(test_file, "broken_module")
            assert len(symbols) == 0


class TestValidateChangedFiles:
    def test_validate_simple_module(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a simple test module
            test_file = temp_path / "test_module.py"
            test_file.write_text('''
def good_function():
    """A well-documented function."""
    pass
''')

            config = ValidationConfig(
                root_path=temp_path,
                path_converter=generic_path_converter,
            )

            # Mock the validation function to always return success
            mock_result = ValidatorResult.create("test_module.good_function")
            with patch(
                "automation.dagster_docs.changed_validator.validate_symbol_docstring",
                return_value=mock_result,
            ):
                results = validate_changed_files([test_file], config)

            assert len(results) == 1
            assert results[0].symbol_info.symbol_path == "test_module.good_function"
            assert not results[0].has_errors()
            assert not results[0].has_warnings()

    def test_file_filtering(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create Python and non-Python files
            py_file = temp_path / "test.py"
            py_file.write_text('def func(): """Doc"""; pass')

            txt_file = temp_path / "test.txt"
            txt_file.write_text("Not Python code")

            config = ValidationConfig(
                root_path=temp_path,
                path_converter=generic_path_converter,
            )

            # Mock the validation function to always return success
            mock_result = ValidatorResult.create("test.func")
            with patch(
                "automation.dagster_docs.changed_validator.validate_symbol_docstring",
                return_value=mock_result,
            ):
                results = validate_changed_files([py_file, txt_file], config)

            # Only the Python file should be processed
            assert len(results) == 1
            assert results[0].symbol_info.file_path == py_file

    def test_path_converter_filtering(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            test_file = temp_path / "test.py"
            test_file.write_text('def func(): """Doc"""; pass')

            # Path converter that rejects all files
            def reject_all_converter(file_path, root_path):
                return None

            config = ValidationConfig(
                root_path=temp_path,
                path_converter=reject_all_converter,
            )

            # Mock the validation function (though it shouldn't be called)
            mock_result = ValidatorResult.create("test.func")
            with patch(
                "automation.dagster_docs.changed_validator.validate_symbol_docstring",
                return_value=mock_result,
            ):
                results = validate_changed_files([test_file], config)

            # No files should be processed due to path converter rejection
            assert len(results) == 0


class TestValidateSymbols:
    def test_validation_with_errors(self):
        symbol_info = SymbolInfo(symbol_path="test.func", file_path=Path("/test.py"))

        # Mock the validation function to return errors and warnings
        mock_result = ValidatorResult.create("test.func")
        mock_result = mock_result.with_error("Test error").with_warning("Test warning")

        with patch(
            "automation.dagster_docs.changed_validator.validate_symbol_docstring",
            return_value=mock_result,
        ):
            results = validate_symbols({symbol_info})

        assert len(results) == 1
        result = results[0]
        assert result.symbol_info == symbol_info
        assert result.errors == ["Test error"]
        assert result.warnings == ["Test warning"]
        assert result.has_errors() is True
        assert result.has_warnings() is True

    def test_validation_exception_handling(self):
        symbol_info = SymbolInfo(symbol_path="test.func", file_path=Path("/test.py"))

        # Mock the validation function to raise an exception
        with patch(
            "automation.dagster_docs.changed_validator.validate_symbol_docstring",
            side_effect=ValueError("Validation failed"),
        ):
            results = validate_symbols({symbol_info})

        assert len(results) == 1
        result = results[0]
        assert result.has_errors() is True
        assert "Validation error: Validation failed" in result.errors[0]

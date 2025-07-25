"""Tests for the changed_validator module."""

import tempfile
from pathlib import Path

from automation.dagster_docs.changed_validator import (
    SymbolInfo,
    ValidationConfig,
    ValidationResult,
    extract_symbols_from_file,
    validate_changed_files,
    validate_symbols,
)
from automation.dagster_docs.path_converters import generic_path_converter
from automation.dagster_docs.validator import (
    DocstringValidator,
    ValidationResult as ValidatorResult,
)


class MockValidator(DocstringValidator):
    """Mock validator for testing."""

    def __init__(self, errors=None, warnings=None):
        self.errors = errors or []
        self.warnings = warnings or []

    def validate_symbol_docstring(self, dotted_path):
        result = ValidatorResult.create(dotted_path)
        for error in self.errors:
            result = result.with_error(error)
        for warning in self.warnings:
            result = result.with_warning(warning)
        return result


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

            # Mock validator that always passes
            mock_validator = MockValidator()
            results = validate_changed_files([test_file], config, mock_validator)

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

            mock_validator = MockValidator()
            results = validate_changed_files([py_file, txt_file], config, mock_validator)

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

            mock_validator = MockValidator()
            results = validate_changed_files([test_file], config, mock_validator)

            # No files should be processed due to path converter rejection
            assert len(results) == 0


class TestValidateSymbols:
    def test_validation_with_errors(self):
        symbol_info = SymbolInfo(symbol_path="test.func", file_path=Path("/test.py"))

        mock_validator = MockValidator(errors=["Test error"], warnings=["Test warning"])
        results = validate_symbols({symbol_info}, mock_validator)

        assert len(results) == 1
        result = results[0]
        assert result.symbol_info == symbol_info
        assert result.errors == ["Test error"]
        assert result.warnings == ["Test warning"]
        assert result.has_errors() is True
        assert result.has_warnings() is True

    def test_validation_exception_handling(self):
        symbol_info = SymbolInfo(symbol_path="test.func", file_path=Path("/test.py"))

        class FailingMockValidator(DocstringValidator):
            def validate_symbol_docstring(self, dotted_path):
                raise ValueError("Validation failed")

        results = validate_symbols({symbol_info}, FailingMockValidator())

        assert len(results) == 1
        result = results[0]
        assert result.has_errors() is True
        assert "Validation error: Validation failed" in result.errors[0]

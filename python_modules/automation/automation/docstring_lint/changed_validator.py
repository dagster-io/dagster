"""Functional docstring validation for changed files."""

import importlib.util
import inspect
from pathlib import Path
from typing import Callable, Union

from dagster._record import IHaveNew, record, record_custom

from automation.docstring_lint.validator import DocstringValidator


@record_custom
class ValidationConfig(IHaveNew):
    """Configuration for docstring validation."""

    root_path: Path
    path_converter: Callable[[Path, Path], Union[str, None]]
    file_filter: Callable[[Path], bool]

    def __new__(
        cls,
        root_path: Path,
        path_converter: Callable[[Path, Path], Union[str, None]],
        file_filter: Union[Callable[[Path], bool], None] = None,
    ):
        if file_filter is None:
            file_filter = lambda p: p.suffix == ".py"
        return super().__new__(
            cls,
            root_path=root_path,
            path_converter=path_converter,
            file_filter=file_filter,
        )


@record
class SymbolInfo:
    """Information about a top-level exported symbol with a docstring."""

    symbol_path: str
    file_path: Path
    line_number: Union[int, None] = None


@record
class ValidationResult:
    """Result of validating a single exported symbol's docstring."""

    symbol_info: SymbolInfo
    errors: list[str]
    warnings: list[str]

    def has_errors(self) -> bool:
        """Check if this result has any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if this result has any warnings."""
        return len(self.warnings) > 0


def extract_symbols_from_file(file_path: Path, module_path: str) -> set[SymbolInfo]:
    """Extract top-level exported symbols with docstrings from a file using dynamic import."""
    try:
        # Create a unique module name to avoid conflicts
        module_name = f"temp_module_{hash(str(file_path))}"

        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return set()

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        symbols = set()

        # Extract top-level exported symbols using introspection
        for name, obj in inspect.getmembers(module):
            if name.startswith("_"):
                continue

            # Check if the object was defined in this module
            if hasattr(obj, "__module__") and obj.__module__ != module_name:
                continue

            symbol_path = f"{module_path}.{name}"

            if inspect.isclass(obj):
                if obj.__doc__:
                    symbols.add(
                        SymbolInfo(
                            symbol_path=symbol_path,
                            file_path=file_path,
                            line_number=getattr(obj, "__lineno__", None),
                        )
                    )

                # Check methods
                for method_name, method_obj in inspect.getmembers(obj, inspect.ismethod):
                    if not method_name.startswith("_") and method_obj.__doc__:
                        symbols.add(
                            SymbolInfo(
                                symbol_path=f"{symbol_path}.{method_name}",
                                file_path=file_path,
                                line_number=getattr(method_obj, "__lineno__", None),
                            )
                        )

                # Check functions (unbound methods)
                for func_name, func_obj in inspect.getmembers(obj, inspect.isfunction):
                    if not func_name.startswith("_") and func_obj.__doc__:
                        symbols.add(
                            SymbolInfo(
                                symbol_path=f"{symbol_path}.{func_name}",
                                file_path=file_path,
                                line_number=getattr(func_obj, "__lineno__", None),
                            )
                        )

            elif inspect.isfunction(obj):
                if obj.__doc__:
                    symbols.add(
                        SymbolInfo(
                            symbol_path=symbol_path,
                            file_path=file_path,
                            line_number=getattr(obj, "__lineno__", None),
                        )
                    )

        return symbols

    except Exception:
        # Silently ignore import errors - some files may not be importable
        return set()


def validate_symbols(
    symbols: set[SymbolInfo], validator: DocstringValidator
) -> list[ValidationResult]:
    """Validate docstrings for a set of top-level exported symbols."""
    results = []

    for symbol_info in symbols:
        try:
            validation_result = validator.validate_symbol_docstring(symbol_info.symbol_path)

            result = ValidationResult(
                symbol_info=symbol_info,
                errors=validation_result.errors,
                warnings=validation_result.warnings,
            )
            results.append(result)

        except Exception as e:
            # Convert exceptions to validation errors
            result = ValidationResult(
                symbol_info=symbol_info, errors=[f"Validation error: {e}"], warnings=[]
            )
            results.append(result)

    return results


def validate_changed_files(
    changed_files: list[Path],
    config: ValidationConfig,
    validator: Union[DocstringValidator, None] = None,
) -> list[ValidationResult]:
    """Validate docstrings in a list of changed files."""
    if validator is None:
        validator = DocstringValidator()

    all_symbols = set()

    # Extract top-level exported symbols from all changed files
    for file_path in changed_files:
        if not config.file_filter(file_path):
            continue

        module_path = config.path_converter(file_path, config.root_path)
        if module_path is None:
            continue

        symbols = extract_symbols_from_file(file_path, module_path)
        all_symbols.update(symbols)

    # Validate all exported symbols
    return validate_symbols(all_symbols, validator)


def print_validation_results(
    results: list[ValidationResult], verbose: bool = False
) -> tuple[int, int]:
    """Print validation results and return (error_count, warning_count)."""
    total_errors = 0
    total_warnings = 0

    for result in results:
        if result.has_errors() or result.has_warnings():
            print(f"--- {result.symbol_info.symbol_path} ---")  # noqa: T201

            for error in result.errors:
                print(f"  ERROR: {error}")  # noqa: T201
                total_errors += 1

            for warning in result.warnings:
                print(f"  WARNING: {warning}")  # noqa: T201
                total_warnings += 1

            print()  # noqa: T201

    return total_errors, total_warnings

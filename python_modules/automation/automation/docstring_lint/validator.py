"""Core docstring validation logic using Sphinx parsing pipeline."""

import importlib
import inspect
import io
import sys
import warnings
from pathlib import Path
from typing import Any, Optional

import docutils.core
import docutils.utils
from dagster_shared.record import record
from sphinx.ext.napoleon import GoogleDocstring
from sphinx.util.docutils import docutils_namespace

# Filter out Sphinx role errors and warnings that are valid in the full Sphinx build context
# but appear as errors in standalone docutils validation. These roles like :py:class:,
# :func:, etc. are properly resolved during the actual documentation build with all
# Sphinx extensions loaded, but docutils alone doesn't recognize them.
# Set to False to see all role-related errors/warnings for debugging.
DO_FILTER_OUT_SPHINX_ROLE_WARNINGS = True

# Setup paths to match Dagster's Sphinx configuration
DAGSTER_ROOT = Path(__file__).parent.parent.parent.parent.parent
SPHINX_EXT_PATH = DAGSTER_ROOT / "docs" / "sphinx" / "_ext"
if SPHINX_EXT_PATH.exists() and str(SPHINX_EXT_PATH) not in sys.path:
    sys.path.insert(0, str(SPHINX_EXT_PATH))


@record
class ValidationResult:
    """Results from validating a docstring."""

    symbol_path: str
    errors: list[str]
    warnings: list[str]
    parsing_successful: bool

    @staticmethod
    def create(symbol_path: str) -> "ValidationResult":
        """Create a new ValidationResult."""
        return ValidationResult(
            symbol_path=symbol_path,
            errors=[],
            warnings=[],
            parsing_successful=True,
        )

    def with_error(self, message: str, line_number: Optional[int] = None) -> "ValidationResult":
        """Return a new ValidationResult with an additional error message."""
        location = f" (line {line_number})" if line_number else ""
        return ValidationResult(
            symbol_path=self.symbol_path,
            errors=self.errors + [f"{message}{location}"],
            warnings=self.warnings,
            parsing_successful=self.parsing_successful,
        )

    def with_warning(self, message: str, line_number: Optional[int] = None) -> "ValidationResult":
        """Return a new ValidationResult with an additional warning message."""
        location = f" (line {line_number})" if line_number else ""
        return ValidationResult(
            symbol_path=self.symbol_path,
            errors=self.errors,
            warnings=self.warnings + [f"{message}{location}"],
            parsing_successful=self.parsing_successful,
        )

    def with_parsing_failed(self) -> "ValidationResult":
        """Return a new ValidationResult with parsing marked as failed."""
        return ValidationResult(
            symbol_path=self.symbol_path,
            errors=self.errors,
            warnings=self.warnings,
            parsing_successful=False,
        )

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def is_valid(self) -> bool:
        """Check if the docstring is valid (no errors)."""
        return not self.has_errors() and self.parsing_successful


@record
class SymbolInfo:
    """Information about a Python symbol."""

    symbol: Any
    dotted_path: str
    name: str
    module: Optional[str]
    docstring: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]

    @staticmethod
    def create(symbol: Any, dotted_path: str) -> "SymbolInfo":
        """Create SymbolInfo from a symbol and dotted path."""
        name = getattr(symbol, "__name__", str(symbol))
        module = getattr(symbol, "__module__", None)
        docstring = inspect.getdoc(symbol)
        file_path = None
        line_number = None

        # Try to get source location
        try:
            file_path = inspect.getfile(symbol)
            line_number = inspect.getsourcelines(symbol)[1]
        except (OSError, TypeError):
            pass

        return SymbolInfo(
            symbol=symbol,
            dotted_path=dotted_path,
            name=name,
            module=module,
            docstring=docstring,
            file_path=file_path,
            line_number=line_number,
        )

    def __repr__(self) -> str:
        location = f" at {self.file_path}:{self.line_number}" if self.file_path else ""
        return f"SymbolInfo({self.dotted_path}{location})"


class DocstringValidator:
    """Core validator for processing single docstrings efficiently."""

    def validate_docstring_text(
        self, docstring: str, symbol_path: str = "unknown"
    ) -> ValidationResult:
        """Validate a raw docstring text efficiently.

        Args:
            docstring: The docstring text to validate
            symbol_path: Path identifier for error reporting

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult.create(symbol_path)

        if not docstring or not docstring.strip():
            return result.with_warning("No docstring found")

        # 1. Napoleon processing (convert Google-style to RST first)
        processed_rst = docstring
        try:
            with docutils_namespace():
                napoleon_docstring = GoogleDocstring(docstring)
                processed_rst = str(napoleon_docstring)
        except Exception as e:
            return result.with_error(f"Napoleon processing failed: {e}").with_parsing_failed()

        # 2. RST syntax validation on the processed content
        try:
            warning_stream = io.StringIO()
            settings = {
                "warning_stream": warning_stream,
                "halt_level": 5,
                "report_level": 1,
            }

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                docutils.core.publish_doctree(processed_rst, settings_overrides=settings)

            # Check for RST issues, filtering Sphinx role errors/warnings if enabled
            warnings_text = warning_stream.getvalue()
            if warnings_text:
                # Check if this is a code-block directive error with missing blank line
                enhanced_full_text = self._enhance_full_error_message(warnings_text)
                if enhanced_full_text != warnings_text:
                    # We enhanced the message, use it as a single error
                    result = result.with_error(f"RST syntax: {enhanced_full_text}")
                else:
                    # Process line by line as before
                    for line in warnings_text.strip().split("\n"):
                        if line.strip():
                            # Skip Sphinx role issues if filtering is enabled
                            if DO_FILTER_OUT_SPHINX_ROLE_WARNINGS and self._is_sphinx_role_issue(
                                line
                            ):
                                continue

                            line_num = self._extract_line_number(line)
                            enhanced_message = self._enhance_error_message(line)

                            # Upgrade certain warnings to errors
                            should_be_error = (
                                "ERROR" in line or self._should_upgrade_warning_to_error(line)
                            )

                            if should_be_error:
                                result = result.with_error(
                                    f"RST syntax: {enhanced_message}", line_num
                                )
                            else:
                                result = result.with_warning(
                                    f"RST syntax: {enhanced_message}", line_num
                                )

        except Exception as e:
            result = result.with_error(f"RST validation failed: {e}")

        # 3. Basic docstring structure checks
        result = self._check_docstring_structure(docstring, result)

        return result

    def validate_symbol_docstring(self, dotted_path: str) -> ValidationResult:
        """Validate the docstring of a Python symbol by importing it.

        Args:
            dotted_path: The dotted path to the symbol (e.g., 'dagster.asset')

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult.create(dotted_path)

        try:
            symbol = self._import_symbol(dotted_path)
            docstring = inspect.getdoc(symbol)

            if not docstring:
                return result.with_warning("Symbol has no docstring")

            return self.validate_docstring_text(docstring, dotted_path)

        except (ImportError, AttributeError) as e:
            return result.with_error(f"Failed to import symbol: {e}").with_parsing_failed()

    def _import_symbol(self, dotted_path: str) -> Any:
        """Import a symbol from a dotted path."""
        parts = dotted_path.split(".")

        for i in range(len(parts), 0, -1):
            module_path = ".".join(parts[:i])
            try:
                module = importlib.import_module(module_path)

                if i == len(parts):
                    return module

                symbol = module
                for attr_name in parts[i:]:
                    symbol = getattr(symbol, attr_name)

                return symbol

            except ImportError:
                continue

        raise ImportError(f"Could not import symbol '{dotted_path}'")

    def _extract_line_number(self, warning_line: str) -> Optional[int]:
        """Extract line number from a docutils warning message."""
        if "(line" in warning_line:
            try:
                return int(warning_line.split("(line")[1].split(")")[0])
            except (IndexError, ValueError):
                pass
        return None

    def _is_sphinx_role_issue(self, warning_line: str) -> bool:
        """Check if a warning/error is related to unknown Sphinx roles or directives."""
        sphinx_roles = [
            "py:class",
            "py:func",
            "py:meth",
            "py:attr",
            "py:mod",
            "py:data",
            "func",
            "class",
            "meth",
            "attr",
            "mod",
            "data",
            "ref",
            "doc",
            "download",
        ]

        sphinx_directives = [
            "literalinclude",
            "automodule",
            "autoclass",
            "autofunction",
            "toctree",
            "code-block",
            "highlight",
            "note",
            "warning",
            "versionadded",
            "versionchanged",
            "deprecated",
        ]

        # Check for "Unknown interpreted text role" messages
        if "Unknown interpreted text role" in warning_line:
            return any(role in warning_line for role in sphinx_roles)

        # Check for "No role entry" messages
        if "No role entry for" in warning_line:
            return any(f'"{role}"' in warning_line for role in sphinx_roles)

        # Check for "Trying X as canonical role name" messages
        if "Trying" in warning_line and "as canonical role name" in warning_line:
            return any(f'"{role}"' in warning_line for role in sphinx_roles)

        # Check for "Unknown directive type" messages
        if "Unknown directive type" in warning_line:
            return any(f'"{directive}"' in warning_line for directive in sphinx_directives)

        # Check for "No directive entry" messages
        if "No directive entry for" in warning_line:
            return any(f'"{directive}"' in warning_line for directive in sphinx_directives)

        # Check for "Trying X as canonical directive name" messages
        if "Trying" in warning_line and "as canonical directive name" in warning_line:
            return any(f'"{directive}"' in warning_line for directive in sphinx_directives)

        # Check for directive content warnings (lines that start with ".. directive::")
        if warning_line.strip().startswith(".. "):
            directive_name = warning_line.strip().split("::")[0][3:].strip()
            if directive_name in sphinx_directives:
                return True

        # Check for directive option warnings (lines that start with spaces and ":")
        if warning_line.strip().startswith(":") and any(
            opt in warning_line for opt in ["caption", "language", "linenos"]
        ):
            return True

        return False

    def _enhance_full_error_message(self, warnings_text: str) -> str:
        """Enhance full RST error message for common multi-line patterns."""
        # Check for code-block directive error with missing blank line
        if (
            'Error in "code-block" directive' in warnings_text
            and "maximum 1 argument(s) allowed" in warnings_text
        ):
            return (
                'Error in "code-block" directive: missing blank line after directive. '
                "RST directives like '.. code-block:: python' require an empty line "
                "before the code content begins."
            )

        # Return original text if no enhancement applies
        return warnings_text

    def _enhance_error_message(self, warning_line: str) -> str:
        """Enhance RST error messages to provide more helpful feedback for common issues."""
        # Check for code-block directive issues with too many arguments
        if (
            'Error in "code-block" directive' in warning_line
            and "maximum 1 argument(s) allowed" in warning_line
        ):
            return (
                'Error in "code-block" directive: too many arguments. '
                "This usually means you're missing a blank line after the directive. "
                "Ensure there's an empty line between '.. code-block:: python' and your code."
            )

        # Check for other common directive issues
        if (
            'Error in "' in warning_line
            and "directive" in warning_line
            and "maximum" in warning_line
            and "argument(s) allowed" in warning_line
        ):
            directive_match = warning_line.split('Error in "')[1].split('"')[0]
            return (
                f'Error in "{directive_match}" directive: too many arguments. '
                f"Check that you have a blank line after the directive declaration."
            )

        # Return original message if no enhancement applies
        return warning_line

    def _should_upgrade_warning_to_error(self, warning_line: str) -> bool:
        """Determine if a warning should be upgraded to an error."""
        # Unrecognized language in code-block directive is almost certainly an error
        if "No Pygments lexer found for" in warning_line:
            return True

        # Add other warning patterns that should be errors here
        return False

    def _check_docstring_structure(
        self, docstring: str, result: ValidationResult
    ) -> ValidationResult:
        """Check basic docstring structure issues."""
        lines = docstring.split("\n")

        # Check for common section headers
        sections = [
            "Args:",
            "Arguments:",
            "Parameters:",
            "Returns:",
            "Return:",
            "Yields:",
            "Yield:",
            "Raises:",
            "Examples:",
            "Example:",
        ]

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for malformed section headers
            for section in sections:
                if section.lower() in stripped.lower() and section not in stripped:
                    result = result.with_warning(
                        f"Possible malformed section header: '{stripped}' (should be '{section}')",
                        i,
                    )

        return result


class SymbolImporter:
    """Handles dynamic importing of Python symbols from dotted paths."""

    @staticmethod
    def import_symbol(dotted_path: str) -> SymbolInfo:
        """Import a symbol from a dotted path like 'dagster.asset' or 'dagster.OpDefinition'.

        Args:
            dotted_path: The full dotted path to the symbol

        Returns:
            SymbolInfo object containing the imported symbol and metadata

        Raises:
            ImportError: If the symbol cannot be imported
            AttributeError: If the symbol doesn't exist in the module
        """
        parts = dotted_path.split(".")

        # Try progressively longer module paths until we find one that imports
        for i in range(len(parts), 0, -1):
            module_path = ".".join(parts[:i])
            try:
                module = importlib.import_module(module_path)

                # If we imported the entire path as a module, return the module itself
                if i == len(parts):
                    return SymbolInfo.create(module, dotted_path)

                # Otherwise, walk the remaining attribute path
                symbol = module
                for attr_name in parts[i:]:
                    symbol = getattr(symbol, attr_name)

                return SymbolInfo.create(symbol, dotted_path)

            except ImportError:
                continue

        raise ImportError(f"Could not import symbol '{dotted_path}'")

    @staticmethod
    def get_all_public_symbols(module_path: str) -> list[SymbolInfo]:
        """Get all public symbols from a module (those not starting with '_').

        Args:
            module_path: The dotted path to the module

        Returns:
            List of SymbolInfo objects for all public symbols
        """
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(f"Could not import module '{module_path}': {e}")

        symbols = []
        for name in dir(module):
            if not name.startswith("_"):
                try:
                    symbol = getattr(module, name)
                    full_path = f"{module_path}.{name}"
                    symbols.append(SymbolInfo.create(symbol, full_path))
                except Exception:
                    # Skip symbols that can't be accessed
                    continue

        return symbols

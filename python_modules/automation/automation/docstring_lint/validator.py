"""Core docstring validation logic using Sphinx parsing pipeline."""

# Import the is_public function to check for @public decorator
import importlib
import inspect
import io
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Optional

import docutils.core
import docutils.utils
from dagster._annotations import is_public
from dagster_shared.record import record
from sphinx.ext.napoleon import GoogleDocstring
from sphinx.util.docutils import docutils_namespace

from automation.docstring_lint.public_symbol_utils import get_public_methods_from_class

# Filter out Sphinx role errors and warnings that are valid in the full Sphinx build context
# but appear as errors in standalone docutils validation. These roles like :py:class:,
# :func:, etc. are properly resolved during the actual documentation build with all
# Sphinx extensions loaded, but docutils alone doesn't recognize them.
# Set to False to see all role-related errors/warnings for debugging.
DO_FILTER_OUT_SPHINX_ROLE_WARNINGS = True

# Regex pattern for potential section headers: uppercase letter followed by letters/spaces, ending with colon
# Examples: "Args:", "Example usage:", "See Also:" but not "http://", "def function():", etc.
SECTION_HEADER_PATTERN = re.compile(r"^[A-Z][A-Za-z\s]{2,30}:$")

# All section headers currently used in the Dagster codebase
# Based on analysis of all public symbols
ALLOWED_SECTION_HEADERS = {
    # Standard Google-style sections
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
    "Note:",
    "Notes:",
    "Warning:",
    "Warnings:",
    "See Also:",
    "Attributes:",
    # Dagster-specific sections that are commonly used
    "Example usage:",
    "Example definition:",
    "Definitions:",
    # Common example section variations
    "For example:",
    "For example::",  # RST code block style
    "Example enumeration:",
}


def extract_section_headers_from_docstring(docstring: str) -> list[str]:
    """Extract all potential section headers from a docstring.

    Uses the same regex pattern as the main validation logic to identify
    lines that could be section headers.

    Args:
        docstring: The docstring text to analyze

    Returns:
        List of potential section header strings found in the docstring
    """
    if not docstring:
        return []

    headers = []
    lines = docstring.split("\n")

    for line in lines:
        stripped = line.strip()
        if SECTION_HEADER_PATTERN.match(stripped):
            headers.append(stripped)

    return headers


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

        # Try to get source location - prefer the module where the symbol is defined
        try:
            if module:
                # Try to import the module and get the file from there
                import importlib

                mod = importlib.import_module(module)
                if hasattr(mod, name):
                    actual_symbol = getattr(mod, name)
                    if actual_symbol is symbol:
                        # This is the actual definition location
                        file_path = inspect.getfile(mod)
                        try:
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

            # Single fallback: use inspect methods directly
            file_path = inspect.getfile(symbol)
            line_number = inspect.getsourcelines(symbol)[1]
        except (OSError, TypeError, ImportError):
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
        """Validate the docstring of a Python symbol.

        Args:
            dotted_path: The dotted path to the symbol (e.g., 'dagster.asset')

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult.create(dotted_path)

        try:
            # Try file-based reading first (most accurate for current file state)
            docstring = self._read_docstring_from_file(dotted_path)

            if not docstring:
                # Fall back to import-based reading
                symbol = self._import_symbol(dotted_path)
                docstring = inspect.getdoc(symbol)

            if not docstring:
                return result.with_warning("Symbol has no docstring")

            return self.validate_docstring_text(docstring, dotted_path)

        except (ImportError, AttributeError) as e:
            return result.with_error(f"Failed to import symbol: {e}").with_parsing_failed()

    def _import_symbol(self, dotted_path: str, reload_module: bool = False) -> Any:
        """Import a symbol from a dotted path."""
        parts = dotted_path.split(".")

        for i in range(len(parts), 0, -1):
            module_path = ".".join(parts[:i])
            try:
                module = importlib.import_module(module_path)

                # Reload the module to pick up file changes
                if reload_module:
                    # First get the symbol to find which module actually defines it
                    if i == len(parts):
                        target_module = module
                    else:
                        symbol = module
                        for attr_name in parts[i:]:
                            symbol = getattr(symbol, attr_name)

                        # Get the module that actually defines this symbol
                        if hasattr(symbol, "__module__"):
                            actual_module_name = symbol.__module__
                            if actual_module_name and actual_module_name in sys.modules:
                                target_module = sys.modules[actual_module_name]
                                importlib.reload(target_module)

                # Re-import after potential reload
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

    def _read_docstring_from_file(self, dotted_path: str) -> Optional[str]:
        """Read docstring directly from source file."""
        try:
            # First resolve the symbol to get its source location
            symbol_info = SymbolImporter.import_symbol(dotted_path)

            if not symbol_info.file_path or not symbol_info.line_number:
                return None

            # Read the source file and extract the docstring
            import ast

            with open(symbol_info.file_path, encoding="utf-8") as f:
                source_code = f.read()

            # Parse the AST to find the function and its docstring
            tree = ast.parse(source_code)

            # Look for the function definition
            function_name = symbol_info.name
            candidates = []

            # Find all functions with the matching name
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    candidates.append(node)

            # If we have candidates, pick the one closest to the expected line number
            # or the last one (which is usually the main implementation)
            target_node = None
            if candidates:
                if len(candidates) == 1:
                    target_node = candidates[0]
                else:
                    # Pick the candidate closest to the expected line number
                    target_node = min(
                        candidates, key=lambda n: abs(n.lineno - symbol_info.line_number)
                    )

            if target_node:
                # Check if the function has a docstring
                if (
                    target_node.body
                    and isinstance(target_node.body[0], ast.Expr)
                    and isinstance(target_node.body[0].value, (ast.Str, ast.Constant))
                ):
                    # Extract docstring value
                    docstring_node = target_node.body[0].value
                    raw_docstring = None
                    if isinstance(docstring_node, ast.Str):
                        raw_docstring = docstring_node.s
                    elif isinstance(docstring_node, ast.Constant) and isinstance(
                        docstring_node.value, str
                    ):
                        raw_docstring = docstring_node.value

                    if raw_docstring:
                        # Apply the same normalization that inspect.getdoc() does
                        # Create a dummy object to use inspect.getdoc() normalization
                        class DummyWithDocstring:
                            pass

                        DummyWithDocstring.__doc__ = raw_docstring
                        return inspect.getdoc(DummyWithDocstring)

            return None

        except Exception:
            # Fall back to None if file reading fails
            return None

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
            "py:obj",
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
            "seealso",
            "attribute",
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

        # Check for section header issues that cause indentation errors
        if "Unexpected indentation" in warning_line:
            return (
                "Unexpected indentation. This often indicates a malformed section header. "
                "Check that section headers like 'Args:', 'Returns:', 'Raises:' are formatted correctly "
                "and that content under them is properly indented."
            )

        # Check for block quote issues that often follow section header problems
        if "Block quote ends without a blank line" in warning_line:
            return (
                "Block quote ends without a blank line. This often follows a malformed section header. "
                "Ensure section headers like 'Args:', 'Returns:' end with a colon and are followed by "
                "properly indented content."
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

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # First, use regex to identify potential section headers
            if SECTION_HEADER_PATTERN.match(stripped):
                # Skip if it's already in our allowed list
                if stripped in ALLOWED_SECTION_HEADERS:
                    continue

                # Check for case-insensitive exact matches (wrong case)
                exact_case_match = None
                for section in ALLOWED_SECTION_HEADERS:
                    if stripped.lower() == section.lower():
                        exact_case_match = section
                        break

                if exact_case_match:
                    result = result.with_error(
                        f"Invalid section header: '{stripped}'. Did you mean '{exact_case_match}'?",
                        i,
                    )
                else:
                    # Check for obvious corruptions of known sections using simple string containment
                    possible_match = None
                    for section in ALLOWED_SECTION_HEADERS:
                        section_base = section[:-1].lower()  # Remove colon, lowercase
                        stripped_base = stripped[:-1].lower()  # Remove colon, lowercase

                        # Check if the section name appears intact within the stripped version
                        # This catches cases like "Argsdkjfkdjkfjd" containing "args"
                        if len(section_base) >= 4 and section_base in stripped_base:
                            possible_match = section
                            break

                    if possible_match:
                        result = result.with_error(
                            f"Invalid section header: '{stripped}'. Did you mean '{possible_match}'?",
                            i,
                        )

            # Enhanced section header validation - check for malformed headers
            for section in ALLOWED_SECTION_HEADERS:
                section_base = section.rstrip(":")

                # Check for missing colon
                if stripped == section_base and section != section_base:
                    result = result.with_error(
                        f"Malformed section header: '{stripped}' is missing colon (should be '{section}')",
                        i,
                    )

                # Check for incorrect capitalization or spacing
                elif section_base.lower() in stripped.lower() and section not in stripped:
                    # More specific detection for common mistakes
                    if stripped.lower() == section.lower():
                        result = result.with_error(
                            f"Malformed section header: '{stripped}' has incorrect capitalization (should be '{section}')",
                            i,
                        )
                    elif stripped.lower().replace(" ", "") == section.lower().replace(" ", ""):
                        result = result.with_error(
                            f"Malformed section header: '{stripped}' has incorrect spacing (should be '{section}')",
                            i,
                        )
                    else:
                        result = result.with_warning(
                            f"Possible malformed section header: '{stripped}' (should be '{section}')",
                            i,
                        )

            # Check for completely garbled section headers (like "Argsjdkfjdkjfdk:")
            if ":" in stripped and len(stripped) > 4:
                # Look for patterns that might be corrupted section headers
                for section in ALLOWED_SECTION_HEADERS:
                    section_base = section.rstrip(":")
                    # If the line contains the section name but with extra characters
                    if (
                        section_base.lower() in stripped.lower()
                        and stripped.lower() != section.lower()
                        and len(stripped) > len(section) + 3
                    ):  # Allow some variance
                        # Check if this looks like a corrupted section header
                        if stripped.endswith(":") and not any(
                            section in stripped for section in ALLOWED_SECTION_HEADERS
                        ):
                            result = result.with_error(
                                f"Corrupted section header detected: '{stripped}' (possibly should be '{section}')",
                                i,
                            )
                            break

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
            except ImportError:
                # This module path doesn't exist, try the next shorter one
                continue

            # If we imported the entire path as a module, return the module itself
            if i == len(parts):
                return SymbolInfo.create(module, dotted_path)

            # Otherwise, walk the remaining attribute path
            symbol = module
            for attr_name in parts[i:]:
                symbol = getattr(symbol, attr_name)

            return SymbolInfo.create(symbol, dotted_path)

        raise ImportError(f"Could not import symbol '{dotted_path}'")

    @staticmethod
    def get_all_exported_symbols(module_path: str) -> list[SymbolInfo]:
        """Get all top-level exported symbols from a module (those not starting with '_').

        Args:
            module_path: The dotted path to the module

        Returns:
            List of SymbolInfo objects for all top-level exported symbols
        """
        module = importlib.import_module(module_path)

        symbols = []
        for name in dir(module):
            if not name.startswith("_"):
                symbol = getattr(module, name)
                full_path = f"{module_path}.{name}"
                symbols.append(SymbolInfo.create(symbol, full_path))

        return symbols

    @staticmethod
    def get_all_public_annotated_methods(module_path: str) -> list[SymbolInfo]:
        """Get all @public-annotated methods from top-level exported classes.

        Args:
            module_path: The dotted path to the module

        Returns:
            List of SymbolInfo objects for all @public-annotated methods on top-level exported classes
        """
        module = importlib.import_module(module_path)

        methods = []
        for name in dir(module):
            if not name.startswith("_"):
                symbol = getattr(module, name)
                # Check if this symbol is a top-level exported class with @public annotation
                if inspect.isclass(symbol) and is_public(symbol):
                    # Get all @public-annotated methods from this top-level exported class
                    class_dotted_path = f"{module_path}.{name}"
                    method_paths = get_public_methods_from_class(symbol, class_dotted_path)

                    for method_path in method_paths:
                        # Extract method name and get the actual method object
                        method_name = method_path.split(".")[-1]
                        method = getattr(symbol, method_name)
                        method_info = SymbolInfo.create(method, method_path)
                        methods.append(method_info)

        return methods

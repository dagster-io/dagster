"""Core docstring validation logic using Sphinx parsing pipeline."""

# Import the is_public function to check for @public decorator
import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Optional

from dagster._annotations import is_public
from dagster_shared.record import record
from sphinx.ext.napoleon import GoogleDocstring
from sphinx.util.docutils import docutils_namespace

from automation.dagster_docs.docstring_rules import (
    ValidationContext,
    ValidationFunction,
    ValidationResult,
    create_python_ast_validator,
    create_rst_syntax_validator,
    create_section_header_validator,
    create_sphinx_filter_validator,
)
from automation.dagster_docs.docstring_rules.section_header_rule import SECTION_HEADER_PATTERN
from automation.dagster_docs.public_symbol_utils import get_public_methods_from_class


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


def validate_docstring_text(docstring: str, symbol_path: str = "unknown") -> ValidationResult:
    """Validate a raw docstring text using the rule-based architecture.

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

    # 2. Create validation context
    context = ValidationContext(
        docstring=docstring,
        symbol_path=symbol_path,
        processed_rst=processed_rst,
    )

    # 3. Apply all validation functions in sequence
    validators: list[ValidationFunction] = [
        create_section_header_validator(),
        create_python_ast_validator(),
        create_rst_syntax_validator(),
        create_sphinx_filter_validator(),
    ]

    for validator in validators:
        result = validator(context, result)

    return result


def validate_symbol_docstring(dotted_path: str) -> ValidationResult:
    """Validate the docstring of a Python symbol.

    Args:
        dotted_path: The dotted path to the symbol (e.g., 'dagster.asset')

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult.create(dotted_path)

    try:
        # Try file-based reading first (most accurate for current file state)
        docstring = _read_docstring_from_file(dotted_path)

        if not docstring:
            # Fall back to import-based reading
            symbol = _import_symbol(dotted_path)
            docstring = inspect.getdoc(symbol)

        if not docstring:
            return result.with_warning("Symbol has no docstring")

        return validate_docstring_text(docstring, dotted_path)

    except (ImportError, AttributeError) as e:
        return result.with_error(f"Failed to import symbol: {e}").with_parsing_failed()


def _import_symbol(dotted_path: str, reload_module: bool = False) -> Any:
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


def _read_docstring_from_file(dotted_path: str) -> Optional[str]:
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
                target_node = min(candidates, key=lambda n: abs(n.lineno - symbol_info.line_number))

        if target_node:
            # Check if the function has a docstring
            if (
                target_node.body
                and isinstance(target_node.body[0], ast.Expr)
                and isinstance(target_node.body[0].value, ast.Constant)
                and isinstance(target_node.body[0].value.value, str)
            ):
                # Extract docstring value
                raw_docstring = target_node.body[0].value.value

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

    @staticmethod
    def get_all_public_symbols(module_path: str) -> list[SymbolInfo]:
        """Get all public symbols from a module (exported symbols marked @public + public-annotated methods).

        Args:
            module_path: The dotted path to the module

        Returns:
            List of SymbolInfo objects for all public symbols in the module.
            Includes only top-level exported symbols that are marked with @public decorator
            and all @public-annotated methods from @public classes.

        Raises:
            ImportError: If the module cannot be imported
        """
        public_symbols = []

        # Get top-level exported symbols that are also marked with @public
        exported_symbols = SymbolImporter.get_all_exported_symbols(module_path)
        # Filter to only include symbols that are marked as @public
        for symbol_info in exported_symbols:
            if is_public(symbol_info.symbol):
                public_symbols.append(symbol_info)

        # Get all @public-annotated methods from @public classes
        method_symbols = SymbolImporter.get_all_public_annotated_methods(module_path)
        public_symbols.extend(method_symbols)

        return public_symbols

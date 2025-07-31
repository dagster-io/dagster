"""Utilities for validating consistency between @public decorators and RST documentation."""

import ast
import re
from pathlib import Path
from typing import Optional, Union

from dagster_shared.record import record

from automation.dagster_docs.public_packages import get_public_dagster_packages


@record
class PublicSymbol:
    """Information about a symbol marked with @public decorator."""

    module_path: str
    symbol_name: str
    symbol_type: str  # 'class', 'function', 'method', 'property'
    is_exported: bool  # Whether it's available as top-level export
    source_file: str


@record
class RstSymbol:
    """Information about a symbol documented in RST files."""

    module_path: str
    symbol_name: str
    rst_directive: str  # 'autoclass', 'autofunction', 'autodecorator'
    rst_file: str


@record
class ValidationIssue:
    """Represents a validation issue found during public API checking."""

    issue_type: str  # 'missing_rst', 'missing_public', 'missing_export'
    symbol_name: str
    module_path: str
    details: str


class PublicApiValidator:
    """Validates consistency between @public decorators and RST documentation."""

    def __init__(self, dagster_root: Path):
        self.dagster_root = dagster_root
        self.python_modules_dir = dagster_root / "python_modules"
        self.rst_docs_dir = dagster_root / "docs" / "sphinx" / "sections" / "api" / "apidocs"
        self._package_paths_cache: Optional[dict[str, Path]] = None

    def _discover_packages(self) -> dict[str, Path]:
        """Discover all available packages and their filesystem paths.

        Returns:
            Dict mapping package names (with underscores) to their filesystem paths
        """
        if self._package_paths_cache is not None:
            return self._package_paths_cache

        packages = get_public_dagster_packages(self.dagster_root)
        self._package_paths_cache = {pkg.module_name: pkg.path for pkg in packages}
        return self._package_paths_cache

    def find_public_symbols(self, exclude_modules: Optional[set[str]] = None) -> list[PublicSymbol]:
        """Find all symbols marked with @public decorator in dagster modules.

        Args:
            exclude_modules: Set of module paths to exclude from scanning

        Returns:
            List of PublicSymbol objects
        """
        exclude_modules = exclude_modules or set()
        public_symbols = []

        # Scan dagster core module
        dagster_dir = self.python_modules_dir / "dagster" / "dagster"
        public_symbols.extend(
            self._scan_directory_for_public(dagster_dir, "dagster", exclude_modules)
        )

        # Scan library modules
        libraries_dir = self.python_modules_dir / "libraries"
        if libraries_dir.exists():
            for lib_dir in libraries_dir.iterdir():
                if lib_dir.is_dir() and lib_dir.name.startswith("dagster-"):
                    lib_package_dir = lib_dir / lib_dir.name.replace("-", "_")
                    if lib_package_dir.exists():
                        public_symbols.extend(
                            self._scan_directory_for_public(
                                lib_package_dir, lib_dir.name.replace("-", "_"), exclude_modules
                            )
                        )

        return public_symbols

    def _scan_directory_for_public(
        self, directory: Path, base_module: str, exclude_modules: set[str]
    ) -> list[PublicSymbol]:
        """Recursively scan a directory for @public decorated symbols."""
        public_symbols = []

        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue

            relative_path = py_file.relative_to(directory)
            module_parts = [base_module] + list(relative_path.with_suffix("").parts)

            if relative_path.name == "__init__.py":
                module_parts = module_parts[:-1]

            module_path = ".".join(module_parts)

            if module_path in exclude_modules:
                continue

            # Skip dagster_airbyte generated classes
            if self._is_dagster_airbyte_generated(module_path):
                continue

            try:
                symbols = self._extract_public_symbols_from_file(py_file, module_path)
                public_symbols.extend(symbols)
            except Exception:
                # Skip files that can't be parsed
                continue

        return public_symbols

    def _extract_public_symbols_from_file(
        self, file_path: Path, module_path: str
    ) -> list[PublicSymbol]:
        """Extract @public decorated symbols from a Python file."""
        public_symbols = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return public_symbols

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return public_symbols

        # Look for @public decorated symbols at module level only
        # We exclude methods since they don't need to be individually documented in RST
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if self._has_public_decorator(node) and self._is_module_level_symbol(tree, node):
                    symbol_type = "class" if isinstance(node, ast.ClassDef) else "function"

                    # Check if this symbol is exported at top-level
                    is_exported = self._is_symbol_exported(module_path, node.name)

                    # Use the exported module path if the symbol is exported
                    exported_module_path = self._get_exported_module_path(
                        module_path, node.name, is_exported
                    )

                    public_symbols.append(
                        PublicSymbol(
                            module_path=exported_module_path,
                            symbol_name=node.name,
                            symbol_type=symbol_type,
                            is_exported=is_exported,
                            source_file=str(file_path),
                        )
                    )

        return public_symbols

    def _has_public_decorator(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]
    ) -> bool:
        """Check if a node has @public decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "public":
                return True
            elif isinstance(decorator, ast.Attribute) and decorator.attr == "public":
                return True
        return False

    def _is_module_level_symbol(self, tree: ast.Module, node: ast.AST) -> bool:
        """Check if a node is defined at module level (not inside a class)."""
        # Check if the node is directly in the module body
        return node in tree.body

    def _is_dagster_airbyte_generated(self, module_path: str) -> bool:
        """Check if this is a dagster_airbyte generated module that should be excluded."""
        return module_path.startswith(
            "dagster_airbyte.managed.generated.sources"
        ) or module_path.startswith("dagster_airbyte.managed.generated.destinations")

    def _is_symbol_exported(self, module_path: str, symbol_name: str) -> bool:
        """Check if a symbol is available as a top-level export."""
        try:
            if module_path.startswith("dagster."):
                # Check if it's exported from main dagster module
                return self._check_module_export("dagster", symbol_name)
            elif module_path.startswith("dagster_"):
                # Check if it's exported from the library's top-level
                lib_name = module_path.split(".")[0]
                return self._check_module_export(lib_name, symbol_name)
        except Exception:
            pass
        return False

    def _get_exported_module_path(
        self, internal_module_path: str, symbol_name: str, is_exported: bool
    ) -> str:
        """Get the canonical exported module path for a symbol.

        If a symbol is exported to a top-level module (dagster or library),
        use that as the canonical path instead of the internal implementation path.
        """
        if not is_exported:
            return internal_module_path

        # Check if it's exported from main dagster module
        if internal_module_path.startswith("dagster.") and self._check_module_export(
            "dagster", symbol_name
        ):
            return "dagster"

        # Check if it's exported from a library top-level
        elif internal_module_path.startswith("dagster_"):
            lib_name = internal_module_path.split(".")[0]
            if self._check_module_export(lib_name, symbol_name):
                return lib_name

        # Fallback to internal path if not clearly exported elsewhere
        return internal_module_path

    def _check_module_export(self, module_name: str, symbol_name: str) -> bool:
        """Check if symbol is exported from the specified module using dynamic import."""
        try:
            import importlib
            import sys

            # Use discovered packages to find the correct path
            packages = self._discover_packages()
            if module_name not in packages:
                return False

            package_path = str(packages[module_name])

            if package_path not in sys.path:
                sys.path.insert(0, package_path)

            # Import the module and check if symbol exists
            module = importlib.import_module(module_name)
            return hasattr(module, symbol_name)

        except Exception:
            # Don't fall back to regex - fail the test to surface import issues
            return False

    def find_rst_documented_symbols(
        self, exclude_files: Optional[set[str]] = None
    ) -> list[RstSymbol]:
        """Find all symbols documented in RST files.

        Args:
            exclude_files: Set of RST file paths to exclude

        Returns:
            List of RstSymbol objects
        """
        exclude_files = exclude_files or set()
        rst_symbols = []

        for rst_file in self.rst_docs_dir.rglob("*.rst"):
            if str(rst_file) in exclude_files:
                continue

            try:
                symbols = self._extract_symbols_from_rst(rst_file)
                rst_symbols.extend(symbols)
            except Exception:
                # Skip files that can't be processed
                continue

        return rst_symbols

    def _extract_symbols_from_rst(self, rst_file: Path) -> list[RstSymbol]:
        """Extract documented symbols from an RST file."""
        rst_symbols = []

        try:
            with open(rst_file, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return rst_symbols

        # Look for Sphinx autodoc directives
        patterns = [
            (r"^\.\. autoclass:: ([^\s]+)", "autoclass"),
            (r"^\.\. autofunction:: ([^\s]+)", "autofunction"),
            (r"^\.\. autodecorator:: ([^\s]+)", "autodecorator"),
        ]

        for pattern, directive in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                symbol_path = match.group(1)

                # Parse module and symbol name
                if "." in symbol_path:
                    parts = symbol_path.split(".")
                    module_path = ".".join(parts[:-1])
                    symbol_name = parts[-1]
                else:
                    # Assume it's in current module context
                    module_path = self._infer_module_from_rst_path(rst_file)
                    symbol_name = symbol_path

                rst_symbols.append(
                    RstSymbol(
                        module_path=module_path,
                        symbol_name=symbol_name,
                        rst_directive=directive,
                        rst_file=str(rst_file),
                    )
                )

        return rst_symbols

    def _infer_module_from_rst_path(self, rst_file: Path) -> str:
        """Infer the module path from RST file location.

        For libraries/dagster-some-library.rst files, we assume symbols are exported
        at the top-level of that library (dagster_some_library).
        """
        relative_path = rst_file.relative_to(self.rst_docs_dir)

        if relative_path.parts[0] == "dagster":
            return "dagster"
        elif relative_path.parts[0] == "libraries":
            if len(relative_path.parts) > 1:
                # For library RST files like libraries/dagster-airlift.rst,
                # assume symbols are exported at library top-level: dagster_airlift
                lib_file = relative_path.parts[1]
                if lib_file.endswith(".rst"):
                    lib_name = lib_file[:-4].replace("-", "_")  # Remove .rst and convert dashes
                    return lib_name
                else:
                    lib_name = lib_file.replace("-", "_")
                    return lib_name

        return "unknown"

    def validate_public_in_rst(
        self,
        public_symbols: list[PublicSymbol],
        rst_symbols: list[RstSymbol],
        exclude_symbols: Optional[set[str]] = None,
    ) -> list[ValidationIssue]:
        """Validate that @public symbols are documented in RST files.

        Args:
            public_symbols: List of symbols marked with @public
            rst_symbols: List of symbols documented in RST
            exclude_symbols: Set of symbols to exclude from validation

        Returns:
            List of validation issues found
        """
        exclude_symbols = exclude_symbols or set()
        issues = []

        # Create lookup for RST symbols
        rst_lookup = {(sym.module_path, sym.symbol_name) for sym in rst_symbols}

        for pub_sym in public_symbols:
            symbol_key = f"{pub_sym.module_path}.{pub_sym.symbol_name}"

            if symbol_key in exclude_symbols:
                continue

            # Check if @public symbol has RST documentation
            if (pub_sym.module_path, pub_sym.symbol_name) not in rst_lookup:
                issues.append(
                    ValidationIssue(
                        issue_type="missing_rst",
                        symbol_name=pub_sym.symbol_name,
                        module_path=pub_sym.module_path,
                        details="Symbol marked @public but not documented in RST files",
                    )
                )

            # Check if @public symbol is exported at top-level
            if not pub_sym.is_exported:
                issues.append(
                    ValidationIssue(
                        issue_type="missing_export",
                        symbol_name=pub_sym.symbol_name,
                        module_path=pub_sym.module_path,
                        details="Symbol marked @public but not available as top-level export",
                    )
                )

        return issues

    def validate_rst_has_public(
        self,
        rst_symbols: list[RstSymbol],
        public_symbols: list[PublicSymbol],
        exclude_symbols: Optional[set[str]] = None,
    ) -> list[ValidationIssue]:
        """Validate that RST documented symbols have @public decorators.

        Args:
            rst_symbols: List of symbols documented in RST
            public_symbols: List of symbols marked with @public
            exclude_symbols: Set of symbols to exclude from validation

        Returns:
            List of validation issues found
        """
        exclude_symbols = exclude_symbols or set()
        issues = []

        # Create lookup for @public symbols
        public_lookup = {(sym.module_path, sym.symbol_name) for sym in public_symbols}

        for rst_sym in rst_symbols:
            symbol_key = f"{rst_sym.module_path}.{rst_sym.symbol_name}"

            if symbol_key in exclude_symbols:
                continue

            # Check if RST documented symbol has @public decorator
            if (rst_sym.module_path, rst_sym.symbol_name) not in public_lookup:
                issues.append(
                    ValidationIssue(
                        issue_type="missing_public",
                        symbol_name=rst_sym.symbol_name,
                        module_path=rst_sym.module_path,
                        details="Symbol documented in RST but missing @public decorator",
                    )
                )

        return issues

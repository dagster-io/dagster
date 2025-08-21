"""Sphinx role filtering functions."""

from automation.dagster_docs.docstring_rules.base import (
    ValidationContext,
    ValidationFunction,
    ValidationResult,
)

# Filter out Sphinx role errors and warnings that are valid in the full Sphinx build context
# but appear as errors in standalone docutils validation. These roles like :py:class:,
# :func:, etc. are properly resolved during the actual documentation build with all
# Sphinx extensions loaded, but docutils alone doesn't recognize them.
# Set to False to see all role-related errors/warnings for debugging.
DO_FILTER_OUT_SPHINX_ROLE_WARNINGS = True


def filter_sphinx_warnings(
    context: ValidationContext, result: ValidationResult
) -> ValidationResult:
    """Filter Sphinx role warnings from the result."""
    # Filter warnings
    filtered_warnings = []
    for warning in result.warnings:
        if not _is_sphinx_role_issue(warning):
            filtered_warnings.append(warning)

    # Filter errors
    filtered_errors = []
    for error in result.errors:
        if not _is_sphinx_role_issue(error):
            filtered_errors.append(error)

    return ValidationResult(
        symbol_path=result.symbol_path,
        errors=filtered_errors,
        warnings=filtered_warnings,
        parsing_successful=result.parsing_successful,
    )


def create_sphinx_filter_validator(
    enabled: bool = DO_FILTER_OUT_SPHINX_ROLE_WARNINGS,
) -> ValidationFunction:
    """Create a configurable Sphinx filter validator."""

    def validator(context: ValidationContext, result: ValidationResult) -> ValidationResult:
        if not enabled:
            return result
        return filter_sphinx_warnings(context, result)

    return validator


def _is_sphinx_role_issue(warning_line: str) -> bool:
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

    # Check for RST syntax warnings that contain Sphinx directive content
    # Format: "RST syntax: .. directive:: content"
    if "RST syntax: .. " in warning_line:
        try:
            # Extract the directive part after "RST syntax: .. "
            directive_part = warning_line.split("RST syntax: .. ")[1]
            directive_name = directive_part.split("::")[0].strip()
            if directive_name in sphinx_directives:
                return True
        except (IndexError, AttributeError):
            pass

    # Check for directive option warnings (lines that start with spaces and ":")
    if warning_line.strip().startswith(":") and any(
        opt in warning_line for opt in ["caption", "language", "linenos"]
    ):
        return True

    return False

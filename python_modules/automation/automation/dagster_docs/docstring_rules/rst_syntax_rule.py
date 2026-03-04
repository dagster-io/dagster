"""RST syntax validation functions."""

import io
import warnings

import docutils.core

from automation.dagster_docs.docstring_rules.base import (
    ValidationContext,
    ValidationFunction,
    ValidationResult,
)


def validate_rst_syntax(context: ValidationContext, result: ValidationResult) -> ValidationResult:
    """Validate RST syntax on the processed content."""
    if not context.processed_rst:
        return result.with_error("No processed RST content available for validation")

    try:
        warning_stream = io.StringIO()
        settings = {
            "warning_stream": warning_stream,
            "halt_level": 5,
            "report_level": 1,
        }

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            docutils.core.publish_doctree(context.processed_rst, settings_overrides=settings)

        # Check for RST issues
        warnings_text = warning_stream.getvalue()
        if warnings_text:
            # Check if this is a code-block directive error with missing blank line
            enhanced_full_text = _enhance_full_error_message(warnings_text)
            if enhanced_full_text != warnings_text:
                # We enhanced the message, use it as a single error
                result = result.with_error(f"RST syntax: {enhanced_full_text}")
            else:
                # Process line by line
                for line in warnings_text.strip().split("\n"):
                    if line.strip():
                        line_num = _extract_line_number(line)
                        enhanced_message = _enhance_error_message(line)

                        # Upgrade certain warnings to errors
                        should_be_error = "ERROR" in line or _should_upgrade_warning_to_error(line)

                        if should_be_error:
                            result = result.with_error(f"RST syntax: {enhanced_message}", line_num)
                        else:
                            result = result.with_warning(
                                f"RST syntax: {enhanced_message}", line_num
                            )

    except Exception as e:
        result = result.with_error(f"RST validation failed: {e}")

    return result


def create_rst_syntax_validator(enabled: bool = True) -> ValidationFunction:
    """Create a configurable RST syntax validator."""

    def validator(context: ValidationContext, result: ValidationResult) -> ValidationResult:
        if not enabled:
            return result
        return validate_rst_syntax(context, result)

    return validator


def _extract_line_number(warning_line: str) -> int | None:
    """Extract line number from a docutils warning message."""
    if "(line" in warning_line:
        try:
            return int(warning_line.split("(line")[1].split(")")[0])
        except (IndexError, ValueError):
            pass
    return None


def _enhance_full_error_message(warnings_text: str) -> str:
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


def _enhance_error_message(warning_line: str) -> str:
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


def _should_upgrade_warning_to_error(warning_line: str) -> bool:
    """Determine if a warning should be upgraded to an error."""
    # Unrecognized language in code-block directive is almost certainly an error
    if "No Pygments lexer found for" in warning_line:
        return True

    # Add other warning patterns that should be errors here
    return False

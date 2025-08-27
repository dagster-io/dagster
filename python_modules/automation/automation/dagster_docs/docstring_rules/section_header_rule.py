"""Section header validation functions."""

import re

from automation.dagster_docs.docstring_rules.base import (
    ValidationContext,
    ValidationFunction,
    ValidationResult,
)

# Regex pattern for potential section headers: uppercase letter followed by letters/spaces, ending with colon
# Examples: "Args:", "Example usage:", "See Also:" but not "def function():", etc.
# Indentation is checked separately to avoid matching code examples in code blocks.
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


def _is_inside_code_block(lines: list[str], current_line_index: int) -> bool:
    """Check if the current line is inside a code block.

    Detects RST code blocks like:
    - .. code-block:: python
    - .. code-block:: yaml
    - :: (literal blocks)
    - Lines indented after code block directives
    """
    # Search backwards from current line to find if we're in a code block
    in_code_block = False
    code_block_indent = None

    for i in range(current_line_index):
        line = lines[i]
        stripped = line.strip()
        leading_spaces = len(line) - len(line.lstrip())

        # Check for code block directives
        if stripped.startswith(".. code-block::") or (
            stripped.endswith("::") and not stripped.startswith(":")
        ):
            in_code_block = True
            code_block_indent = leading_spaces
            continue

        # If we found a code block, check if current line is still part of it
        if in_code_block:
            # Empty lines don't break code blocks
            if not stripped:
                continue

            # If this line has less or equal indentation than the code block directive,
            # we've exited the code block
            if code_block_indent is not None and leading_spaces <= code_block_indent:
                in_code_block = False
                code_block_indent = None

    return in_code_block


def validate_section_headers(
    context: ValidationContext, result: ValidationResult
) -> ValidationResult:
    """Validate section headers in docstrings (e.g., Args:, Returns:, etc.)."""
    lines = context.docstring.split("\n")
    lines_with_errors = set()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check indentation first - only validate lines with minimal indentation (0-3 spaces)
        # to avoid matching code examples which are typically indented 4+ spaces
        leading_spaces = len(line) - len(line.lstrip())

        # Skip validation if we're inside a code block
        if _is_inside_code_block(lines, i - 1):  # Convert to 0-based index
            continue

        # First, use regex to identify potential section headers (check dedented line)
        if SECTION_HEADER_PATTERN.match(stripped) and leading_spaces <= 3:
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
                lines_with_errors.add(i)
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
                    lines_with_errors.add(i)

        # Enhanced section header validation - check for malformed headers
        for section in ALLOWED_SECTION_HEADERS:
            section_base = section.rstrip(":")

            # Check for missing colon (case-insensitive)
            if stripped.lower() == section_base.lower() and section != section_base:
                if stripped == section_base:
                    # Exact match except for missing colon
                    result = result.with_error(
                        f"Malformed section header: '{stripped}' is missing colon (should be '{section}')",
                        i,
                    )
                else:
                    # Case mismatch and missing colon
                    result = result.with_error(
                        f"Malformed section header: '{stripped}' is missing colon and has incorrect capitalization (should be '{section}')",
                        i,
                    )
                lines_with_errors.add(i)

            # Check for incorrect capitalization or spacing
            elif section_base.lower() in stripped.lower() and section not in stripped:
                # More specific detection for common mistakes
                if stripped.lower() == section.lower():
                    result = result.with_error(
                        f"Malformed section header: '{stripped}' has incorrect capitalization (should be '{section}')",
                        i,
                    )
                    lines_with_errors.add(i)
                elif stripped.lower().replace(" ", "") == section.lower().replace(" ", ""):
                    result = result.with_error(
                        f"Malformed section header: '{stripped}' has incorrect spacing (should be '{section}')",
                        i,
                    )
                    lines_with_errors.add(i)
                # Only flag as "possible malformed" if the text ends with colon (indicating intent to be a section header)
                # AND either:
                # 1. The stripped text is a single word (to avoid sentences), OR
                # 2. The section header itself is multi-word (legitimate headers like "See Also:")
                elif (
                    stripped.endswith(":")
                    and (" " not in stripped.rstrip(":") or " " in section.rstrip(":"))
                    and i not in lines_with_errors
                ):
                    result = result.with_warning(
                        f"Possible malformed section header: '{stripped}' (should be '{section}')",
                        i,
                    )

        # Check for completely garbled section headers (like "Argsjdkfjdkjfdk:")
        # Only check single words - multi-word phrases are likely legitimate sentences
        if ":" in stripped and len(stripped) > 4 and leading_spaces <= 3:
            # Only validate single words ending with colon as potential section headers
            # Multi-word phrases like "For example, the following..." are legitimate sentences
            if " " not in stripped.rstrip(":"):
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
                            lines_with_errors.add(i)
                            break

    return result


def create_section_header_validator(enabled: bool = True) -> ValidationFunction:
    """Create a configurable section header validator."""

    def validator(context: ValidationContext, result: ValidationResult) -> ValidationResult:
        if not enabled:
            return result
        return validate_section_headers(context, result)

    return validator

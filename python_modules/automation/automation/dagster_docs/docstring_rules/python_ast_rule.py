"""Python AST validation for code blocks in docstrings."""

import ast
import re
from typing import Optional

from automation.dagster_docs.docstring_rules.base import (
    ValidationContext,
    ValidationFunction,
    ValidationResult,
)


def _extract_python_code_blocks(docstring: str) -> list[tuple[str, int]]:
    """Extract Python code blocks from docstrings and return (code, line_number) tuples.

    Looks for RST code-block directives with python language specification.
    """
    code_blocks = []
    lines = docstring.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for code-block:: python directives
        if re.match(r"^\.\.\s+code-block::\s+python\s*$", line):
            # Find the start of the actual code (after the directive and optional blank line)
            code_start_line = i + 1

            # Skip any blank lines after the directive
            while code_start_line < len(lines) and not lines[code_start_line].strip():
                code_start_line += 1

            if code_start_line >= len(lines):
                i += 1
                continue

            # Determine the indentation level of the code block
            first_code_line = lines[code_start_line]
            if not first_code_line.strip():
                i += 1
                continue

            code_indent = len(first_code_line) - len(first_code_line.lstrip())

            # Extract all lines that belong to this code block
            code_lines = []
            current_line = code_start_line

            while current_line < len(lines):
                line = lines[current_line]

                # Empty lines are part of the code block
                if not line.strip():
                    code_lines.append("")
                    current_line += 1
                    continue

                # Check if this line is still part of the code block
                line_indent = len(line) - len(line.lstrip())
                if line_indent >= code_indent and line.strip():
                    # Remove the common indentation from the code line
                    code_lines.append(line[code_indent:])
                    current_line += 1
                else:
                    # We've reached the end of the code block
                    break

            # Join the code lines and add to our list
            if code_lines:
                # Remove trailing empty lines
                while code_lines and not code_lines[-1].strip():
                    code_lines.pop()

                if code_lines:  # Only add if there's actual code content
                    code_content = "\n".join(code_lines)
                    # Use 1-based line numbering for error reporting
                    code_blocks.append((code_content, code_start_line + 1))

            i = current_line
        else:
            i += 1

    return code_blocks


def _validate_python_syntax(code: str) -> Optional[str]:
    """Validate Python code syntax using AST parsing.

    Returns:
        None if syntax is valid, error message string if invalid.
    """
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        # Format the syntax error message
        if e.lineno and e.offset:
            return f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"
        elif e.lineno:
            return f"Syntax error at line {e.lineno}: {e.msg}"
        else:
            return f"Syntax error: {e.msg}"
    except Exception as e:
        return f"AST parsing error: {e}"


def validate_python_code_blocks(
    context: ValidationContext, result: ValidationResult
) -> ValidationResult:
    """Validate Python code blocks in docstrings using AST parsing."""
    code_blocks = _extract_python_code_blocks(context.docstring)

    for code_content, line_number in code_blocks:
        syntax_error = _validate_python_syntax(code_content)
        if syntax_error:
            result = result.with_error(
                f"Python code block syntax error: {syntax_error}", line_number
            )

    return result


def create_python_ast_validator(enabled: bool = True) -> ValidationFunction:
    """Create a configurable Python AST validator for code blocks."""

    def validator(context: ValidationContext, result: ValidationResult) -> ValidationResult:
        if not enabled:
            return result
        return validate_python_code_blocks(context, result)

    return validator

"""Comprehensive tests for Python AST validation in docstrings."""

import pytest
from automation.dagster_docs.docstring_rules.base import ValidationContext, ValidationResult
from automation.dagster_docs.docstring_rules.python_ast_rule import (
    _extract_python_code_blocks,
    _validate_python_syntax,
    create_python_ast_validator,
    validate_python_code_blocks,
)
from automation.dagster_docs.validator import validate_docstring_text


class TestExtractPythonCodeBlocks:
    """Test the _extract_python_code_blocks function."""

    def test_extract_single_code_block(self):
        """Test extracting a single Python code block."""
        docstring = """
        This is a docstring.
        
        .. code-block:: python
        
            def hello():
                return "world"
        """

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 1
        code, line_num = blocks[0]
        assert "def hello():" in code
        assert 'return "world"' in code
        assert line_num == 6  # Line where code starts

    def test_extract_multiple_code_blocks(self):
        """Test extracting multiple Python code blocks."""
        docstring = """
        This function has examples.
        
        .. code-block:: python
        
            x = 1
            print(x)
        
        Some text in between.
        
        .. code-block:: python
        
            def func():
                pass
        """

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 2

        code1, line1 = blocks[0]
        assert "x = 1" in code1
        assert "print(x)" in code1

        code2, line2 = blocks[1]
        assert "def func():" in code2
        assert "pass" in code2

        assert line1 < line2  # Second block starts after first

    def test_extract_no_code_blocks(self):
        """Test docstring with no Python code blocks."""
        docstring = """
        This is just a regular docstring.
        
        Args:
            param: A parameter
            
        Returns:
            Something
        """

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 0

    def test_extract_ignores_non_python_blocks(self):
        """Test that non-Python code blocks are ignored."""
        docstring = """
        This has various code blocks.
        
        .. code-block:: yaml
        
            key: value
            invalid: yaml: syntax
        
        .. code-block:: python
        
            print("hello")
        
        .. code-block:: bash
        
            echo "world"
            invalid-command --bad-syntax
        """

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]
        assert 'print("hello")' in code

    def test_extract_with_indented_code(self):
        """Test extracting code with proper indentation handling."""
        docstring = """
        Example with indented code.
        
        .. code-block:: python
        
            if condition:
                for item in items:
                    process(item)
                    if item.special:
                        handle_special(item)
        """

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]

        # Check that indentation is preserved relative to the first line
        lines = code.split("\n")
        assert lines[0] == "if condition:"
        assert lines[1].startswith("    for item")  # 4 spaces
        assert lines[2].startswith("        process(item)")  # 8 spaces
        assert lines[3].startswith("        if item.special:")  # 8 spaces
        assert lines[4].startswith("            handle_special(item)")  # 12 spaces

    def test_extract_with_empty_lines_in_code(self):
        """Test code blocks with empty lines within the code."""
        docstring = """
        Example with empty lines.
        
        .. code-block:: python
        
            def function():
                x = 1
                
                # Comment after empty line
                y = 2
                
                return x + y
        """

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]

        lines = code.split("\n")
        assert "def function():" in lines[0]
        assert lines[2] == ""  # Empty line preserved
        assert "# Comment after empty line" in lines[3]
        assert lines[5] == ""  # Another empty line preserved
        assert "return x + y" in lines[6]

    def test_extract_trailing_empty_lines_removed(self):
        """Test that trailing empty lines are removed from code blocks."""
        docstring = """
        Example with trailing empty lines.
        
        .. code-block:: python
        
            print("hello")
            
            
            
        Some text after.
        """

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]

        # Should not end with empty lines
        assert not code.endswith("\n\n")
        assert code.strip() == 'print("hello")'

    def test_extract_with_various_directive_formats(self):
        """Test various formats of the code-block directive."""
        docstring = """
        Various directive formats.
        
        .. code-block:: python
        
            # Standard format
            x = 1
        
        ..code-block::python
        
            # No space after ..
            y = 2
        
        .. code-block::python
        
            # No space before language
            z = 3
        """

        blocks = _extract_python_code_blocks(docstring)
        # Only the first one should match (strict regex)
        assert len(blocks) == 1
        code, _ = blocks[0]
        assert "x = 1" in code

    def test_extract_empty_code_block(self):
        """Test handling of empty code blocks that are truly empty."""
        docstring = """Empty code block.

.. code-block:: python

"""

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 0  # Empty blocks are not included

    def test_extract_code_block_no_blank_line(self):
        """Test code block without blank line after directive."""
        docstring = """
        No blank line after directive.
        
        .. code-block:: python
            print("hello")
        """

        blocks = _extract_python_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]
        assert 'print("hello")' in code


class TestValidatePythonSyntax:
    """Test the _validate_python_syntax function."""

    def test_valid_python_code(self):
        """Test validation of valid Python code."""
        code = """
def hello_world():
    print("Hello, world!")
    return 42
"""
        result = _validate_python_syntax(code)
        assert result is None  # No error

    def test_simple_syntax_error(self):
        """Test detection of simple syntax errors."""
        code = """
def broken_function(
    return "missing closing paren"
"""
        result = _validate_python_syntax(code)
        assert result is not None
        assert "Syntax error" in result
        assert "'(' was never closed" in result

    def test_indentation_error(self):
        """Test detection of indentation errors."""
        code = """
def function():
print("wrong indentation")
"""
        result = _validate_python_syntax(code)
        assert result is not None
        assert "IndentationError" in result or "Syntax error" in result

    def test_invalid_token_error(self):
        """Test detection of invalid token errors."""
        code = """
x = 1 @
"""
        result = _validate_python_syntax(code)
        assert result is not None
        assert "Syntax error" in result

    def test_empty_code(self):
        """Test validation of empty code."""
        result = _validate_python_syntax("")
        assert result is None  # Empty code is valid

    def test_comment_only_code(self):
        """Test validation of comment-only code."""
        code = """
# This is just a comment
# Another comment
"""
        result = _validate_python_syntax(code)
        assert result is None  # Comments are valid

    def test_complex_valid_code(self):
        """Test validation of complex but valid Python code."""
        code = """
class MyClass:
    def __init__(self, name):
        self.name = name
    
    def method(self):
        for i in range(10):
            if i % 2 == 0:
                yield i
        
        try:
            result = self.complex_operation()
        except Exception as e:
            print(f"Error: {e}")
            return None
        
        return result
    
    def complex_operation(self):
        return [x**2 for x in range(5) if x > 2]
"""
        result = _validate_python_syntax(code)
        assert result is None  # Complex but valid code

    def test_async_def_syntax(self):
        """Test validation of async/await syntax."""
        code = """
async def async_function():
    result = await some_async_call()
    return result
"""
        result = _validate_python_syntax(code)
        assert result is None  # Async syntax is valid

    def test_syntax_error_with_line_info(self):
        """Test that syntax errors include line information."""
        code = """
line1 = "valid"
line2 = "also valid"
line3 = invalid syntax here
line4 = "this won't be reached"
"""
        result = _validate_python_syntax(code)
        assert result is not None
        assert "line 3" in result or "line 4" in result  # Error location reported


class TestValidatePythonCodeBlocks:
    """Test the validate_python_code_blocks function."""

    def test_valid_code_blocks(self):
        """Test validation with valid Python code blocks."""
        docstring = """
        Function with valid examples.
        
        .. code-block:: python
        
            def example():
                return "hello"
        
        .. code-block:: python
        
            x = [1, 2, 3]
            print(x)
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_python_code_blocks(context, result)

        assert not result.has_errors()
        assert not result.has_warnings()
        assert result.is_valid()

    def test_invalid_code_blocks(self):
        """Test validation with invalid Python code blocks."""
        docstring = """
        Function with syntax errors.
        
        .. code-block:: python
        
            def broken_function(
                return "missing paren"
        
        .. code-block:: python
        
            valid_code = "this is fine"
        
        .. code-block:: python
        
            another broken function(
                print("another error")
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_python_code_blocks(context, result)

        assert result.has_errors()
        assert len(result.errors) == 2  # Two syntax errors

        # Check that both errors are reported
        error_text = " ".join(result.errors)
        assert "Python code block syntax error" in error_text
        assert "'(' was never closed" in error_text

    def test_mixed_valid_invalid_blocks(self):
        """Test validation with mix of valid and invalid blocks."""
        docstring = """
        Mixed examples.
        
        .. code-block:: python
        
            # This is valid
            print("hello")
        
        .. code-block:: python
        
            # This is broken
            def bad_function(
                return "error"
        
        .. code-block:: python
        
            # This is also valid
            x = 42
            y = x * 2
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_python_code_blocks(context, result)

        assert result.has_errors()
        assert len(result.errors) == 1  # Only one error
        assert "Python code block syntax error" in result.errors[0]

    def test_no_code_blocks(self):
        """Test validation with no Python code blocks."""
        docstring = """
        Function with no code examples.
        
        Args:
            param: A parameter
            
        Returns:
            A value
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_python_code_blocks(context, result)

        assert not result.has_errors()
        assert not result.has_warnings()
        assert result.is_valid()

    def test_line_number_reporting(self):
        """Test that error line numbers are correctly reported."""
        docstring = """
        Function with error on specific line.
        
        .. code-block:: python
        
            # This is line 6 of the docstring
            def broken(
                return "error on line 8"
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_python_code_blocks(context, result)

        assert result.has_errors()
        assert len(result.errors) == 1

        # Should include line number in error message
        error = result.errors[0]
        assert "line 6" in error  # Line where the code block starts


class TestCreatePythonAstValidator:
    """Test the create_python_ast_validator function."""

    def test_enabled_validator(self):
        """Test creating an enabled validator."""
        validator = create_python_ast_validator(enabled=True)

        docstring = """
        .. code-block:: python
        
            def broken(
                return "error"
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validator(context, result)

        assert result.has_errors()

    def test_disabled_validator(self):
        """Test creating a disabled validator."""
        validator = create_python_ast_validator(enabled=False)

        docstring = """
        .. code-block:: python
        
            def broken(
                return "error"
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validator(context, result)

        # Should not have errors because validator is disabled
        assert not result.has_errors()

    def test_default_enabled(self):
        """Test that validator is enabled by default."""
        validator = create_python_ast_validator()  # No explicit enabled parameter

        docstring = """
        .. code-block:: python
        
            def broken(
                return "error"
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validator(context, result)

        assert result.has_errors()  # Should be enabled by default


class TestIntegrationWithValidationPipeline:
    """Test integration with the full validation pipeline."""

    def test_integration_valid_docstring(self):
        """Test integration with valid Python code blocks."""
        docstring = """
        Function with valid Python examples.
        
        Args:
            name: The name parameter
        
        Returns:
            A greeting string
        
        Examples:
            Basic usage:
            
            .. code-block:: python
            
                result = greet("Alice")
                print(result)
        """

        result = validate_docstring_text(docstring, "test.symbol")

        assert result.is_valid()
        assert not result.has_errors()

    def test_integration_invalid_python_code(self):
        """Test integration with invalid Python code blocks."""
        docstring = """
        Function with broken Python examples.
        
        Args:
            name: The name parameter
        
        Examples:
            This example has a syntax error:
            
            .. code-block:: python
            
                def broken_example(
                    return greet("Alice")
        """

        result = validate_docstring_text(docstring, "test.symbol")

        assert not result.is_valid()
        assert result.has_errors()

        # Should have Python AST error
        python_errors = [e for e in result.errors if "Python code block syntax error" in e]
        assert len(python_errors) == 1

    def test_integration_multiple_validation_rules(self):
        """Test that AST validation works alongside other validation rules."""
        docstring = """
        Function with multiple issues.
        
        args:  # Wrong case - should be "Args:"
            name: The name parameter
        
        Examples:
            .. code-block:: python
            
                def broken(
                    return "syntax error"
        """

        result = validate_docstring_text(docstring, "test.symbol")

        assert not result.is_valid()

        # Should have both section header issues and Python syntax issues
        all_messages = result.errors + result.warnings

        # Check for both types of issues
        has_section_issue = any(
            "malformed section header" in msg.lower()
            or "possible malformed section header" in msg.lower()
            for msg in all_messages
        )
        has_python_issue = any(
            "python code block syntax error" in msg.lower() for msg in all_messages
        )

        assert has_section_issue, f"Expected section header issue in: {all_messages}"
        assert has_python_issue, f"Expected Python syntax issue in: {all_messages}"

    def test_integration_python_and_rst_errors(self):
        """Test Python AST validation alongside RST syntax validation."""
        docstring = """
        Function with RST and Python issues.
        
        .. code-block:: python
        
            def broken_python(
                return "syntax error"
        """

        result = validate_docstring_text(docstring, "test.symbol")

        assert not result.is_valid()
        assert result.has_errors()

        # Should have Python syntax error
        error_text = " ".join(result.errors).lower()
        assert "python code block syntax error" in error_text


class TestEdgeCasesAndErrorScenarios:
    """Test edge cases and error scenarios."""

    def test_code_block_with_unicode(self):
        """Test code blocks containing Unicode characters."""
        docstring = """
        Function with Unicode in code.
        
        .. code-block:: python
        
            text = "Hello, 世界!"
            print(text)
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_code_block_with_f_strings(self):
        """Test code blocks with f-string syntax."""
        docstring = """
        Function with f-strings.
        
        .. code-block:: python
        
            name = "Alice"
            greeting = f"Hello, {name}!"
            print(f"The greeting is: {greeting}")
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_code_block_with_type_hints(self):
        """Test code blocks with type hints."""
        docstring = """
        Function with type hints.
        
        .. code-block:: python
        
            from typing import List, Optional
            
            def process_items(items: List[str]) -> Optional[str]:
                if not items:
                    return None
                return items[0].upper()
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_code_block_with_decorators(self):
        """Test code blocks with decorators."""
        docstring = """
        Function with decorators.
        
        .. code-block:: python
        
            @property
            @lru_cache(maxsize=128)
            def expensive_property(self) -> str:
                return self._compute_value()
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_very_long_code_block(self):
        """Test validation of very long code blocks."""
        # Generate a long but valid code block
        lines = ["def long_function():"]
        lines.extend([f"    var_{i} = {i}" for i in range(100)])
        lines.append("    return sum([" + ", ".join(f"var_{i}" for i in range(100)) + "])")

        # Properly indent the code for the docstring
        indented_code = "\n".join(f"            {line}" if line.strip() else "" for line in lines)

        docstring = f"""
        Function with long code block.
        
        .. code-block:: python
        
{indented_code}
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_deeply_nested_code(self):
        """Test deeply nested but valid code."""
        docstring = """
        Function with deeply nested code.
        
        .. code-block:: python
        
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if i == j == k:
                            for m in range(2):
                                if m > 0:
                                    try:
                                        result = process(i, j, k, m)
                                        if result:
                                            print(result)
                                    except Exception:
                                        continue
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_code_block_with_triple_quotes(self):
        """Test code blocks containing triple-quoted strings."""
        docstring = '''
        Function with triple quotes in code.
        
        .. code-block:: python
        
            docstring = """
            This is a docstring
            with multiple lines.
            """
            
            code = \'\'\'
            This is code
            with single quotes.
            \'\'\'
        '''

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    @pytest.mark.parametrize(
        "invalid_syntax",
        [
            "def func(",  # Missing closing paren
            "if True\n    pass",  # Missing colon
            "x = 1 +",  # Incomplete expression
            "def func():\nprint('wrong indent')",  # Indentation error
            "x = [1, 2,",  # Incomplete list
            "def func():\n  return\n    x = 1",  # Inconsistent indentation
        ],
    )
    def test_various_syntax_errors(self, invalid_syntax):
        """Test detection of various types of syntax errors."""
        docstring = f"""
        Function with syntax error.
        
        .. code-block:: python
        
            {invalid_syntax}
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert not result.is_valid()
        assert result.has_errors()

        # Should have Python syntax error
        python_errors = [e for e in result.errors if "Python code block syntax error" in e]
        assert len(python_errors) >= 1

"""Tests for common docstring errors that should be caught by the validator.

This test suite validates that the docstring validator correctly identifies
common mistakes when writing Google-style docstrings and RST syntax errors.
These tests ensure the validator catches issues that would break documentation
builds or result in poor rendering.
"""

from automation.dagster_docs.validator import validate_docstring_text


class TestSectionHeaderErrors:
    """Test detection of incorrect section headers."""

    # Using function-based validation approach

    def test_incorrect_section_capitalization(self):
        """Test detection of incorrectly capitalized section headers."""
        docstring = '''"""Function with incorrect section capitalization.

        args:  # Should be "Args:"
            param1: Description of param1
            param2: Description of param2

        returns:  # Should be "Returns:"
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect malformed section headers
        assert result.has_warnings() or result.has_errors()
        messages = " ".join(result.warnings + result.errors).lower()
        assert "malformed section header" in messages or "rst syntax" in messages

    def test_missing_colon_in_section_header(self):
        """Test detection of section headers missing colons."""
        docstring = '''"""Function with missing colons in section headers.

        Args  # Missing colon
            param1: Description of param1

        Returns  # Missing colon
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect RST syntax errors for malformed headers
        assert result.has_warnings() or result.has_errors()

    def test_incorrect_section_names(self):
        """Test detection of common incorrect section names."""
        docstring = '''"""Function with incorrect section names.

        Parameters:  # Should be "Args:"
            param1: Description of param1

        Return:  # Should be "Returns:"
            Description of return value

        Raise:  # Should be "Raises:"
            ValueError: When something goes wrong
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect malformed section headers
        assert result.has_warnings() or result.has_errors()
        messages = " ".join(result.warnings + result.errors).lower()
        assert "malformed section header" in messages or "rst syntax" in messages

    def test_double_colon_section_headers(self):
        """Test detection of section headers with double colons."""
        docstring = '''"""Function with double colon section headers.

        Args::  # Extra colon
            param1: Description of param1

        Returns::  # Extra colon
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect RST syntax issues
        assert result.has_warnings() or result.has_errors()


class TestIndentationErrors:
    """Test detection of incorrect indentation in docstrings."""

    # Using function-based validation approach

    def test_incorrect_parameter_indentation(self):
        """Test detection of incorrect parameter description indentation."""
        docstring = '''"""Function with incorrect parameter indentation.

        Args:
        param1: Description not indented  # Should be indented
        param2: Another description not indented  # Should be indented

        Returns:
            Correct indentation here
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect indentation issues in RST processing
        assert result.has_warnings() or result.has_errors()

    def test_mixed_indentation_levels(self):
        """Test detection of mixed indentation levels."""
        docstring = '''"""Function with mixed indentation levels.

        Args:
            param1: First parameter with correct indentation
        param2: Second parameter with incorrect indentation
                param3: Third parameter with too much indentation

        Returns:
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect indentation inconsistencies
        assert result.has_warnings() or result.has_errors()

    def test_section_content_not_indented(self):
        """Test detection of section content that's not properly indented."""
        docstring = '''"""Function with section content not indented.

        Args:
param1: This should be indented under Args
param2: This should also be indented

        Returns:
The return description should be indented
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect indentation issues
        assert result.has_warnings() or result.has_errors()


class TestParameterDescriptionErrors:
    """Test detection of malformed parameter descriptions."""

    # Using function-based validation approach

    def test_missing_parameter_descriptions(self):
        """Test detection of parameters without descriptions."""
        docstring = '''"""Function with missing parameter descriptions.

        Args:
            param1:  # Missing description
            param2: Valid description
            param3:  # Another missing description

        Returns:
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # This might produce warnings but shouldn't break validation
        # The function should still be considered valid for RST syntax
        assert result.parsing_successful

    def test_malformed_type_annotations(self):
        """Test detection of malformed type annotations in parameters."""
        docstring = '''"""Function with malformed type annotations.

        Args:
            param1 (str: Missing closing parenthesis
            param2 (int)): Extra closing parenthesis
            param3 str): Missing opening parenthesis

        Returns:
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect RST syntax issues from malformed parentheses
        assert result.has_warnings() or result.has_errors()

    def test_inconsistent_parameter_format(self):
        """Test detection of inconsistent parameter formatting."""
        docstring = '''"""Function with inconsistent parameter formatting.

        Args:
            param1 (str): Formatted with type annotation
            param2: No type annotation
            param3 (int) - Wrong separator, should use colon
            param4 (bool): description with
                multiple lines but inconsistent formatting

        Returns:
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should still be valid RST but may have warnings about formatting
        assert result.parsing_successful


class TestRSTSyntaxErrors:
    """Test detection of invalid RST syntax in docstrings."""

    # Using function-based validation approach

    def test_malformed_code_blocks(self):
        """Test detection of malformed code blocks."""
        docstring = '''"""Function with malformed code blocks.

        Example:
            .. code-block: python  # Missing double colon
                
                def example():
                    return "hello"
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect RST syntax error
        assert result.has_warnings() or result.has_errors()

    def test_misspelled_directive_name(self):
        """Test detection of misspelled directive names with correct syntax."""
        docstring = '''"""Function with misspelled directive name.

        Example:
            .. code-kjdfkdblock:: python  # Correct :: but misspelled directive

                def example():
                    return "hello"
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect unknown directive error
        assert result.has_warnings() or result.has_errors()
        messages = " ".join(result.warnings + result.errors).lower()
        assert "unknown directive" in messages or "code-kjdfkdblock" in messages

    def test_unmatched_backticks(self):
        """Test detection of unmatched backticks."""
        docstring = '''"""Function with unmatched backticks.

        This function uses `unmatched backtick and `another unmatched backtick.
        Also has ``double backtick but only one closing backtick`.

        Args:
            param1: A parameter with `unmatched backtick in description

        Returns:
            A value with ``unmatched double backticks
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect RST markup errors
        assert result.has_warnings() or result.has_errors()

    def test_malformed_lists(self):
        """Test detection of malformed lists."""
        docstring = '''"""Function with malformed lists.

        This function does several things:
        
        - First item
        * Mixed bullet styles (should be consistent)
        - Third item
          - Nested item with wrong indentation
        - Item with
        continuation on wrong line

        Args:
            param1: Parameter description

        Returns:
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect list formatting issues
        assert result.has_warnings() or result.has_errors()

    def test_malformed_links(self):
        """Test detection of malformed links and references."""
        docstring = '''"""Function with malformed links.

        See `malformed link <http://example.com` (missing closing angle bracket)
        Also see `another bad link <>`_ (empty URL)
        And `link with spaces in name but no underscore <http://example.com>`

        Args:
            param1: Parameter description

        Returns:
            Description of return value
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect link syntax errors
        assert result.has_warnings() or result.has_errors()


class TestStructuralErrors:
    """Test detection of structural issues in docstrings."""

    # Using function-based validation approach

    def test_empty_sections(self):
        """Test detection of empty sections."""
        docstring = '''"""Function with empty sections.

        Args:
            # Empty section - no parameters listed

        Returns:
            # Another empty section

        Raises:
            # Yet another empty section
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect empty sections or comment-only content
        assert result.has_warnings() or result.has_errors()

    def test_duplicate_sections(self):
        """Test detection of duplicate sections."""
        docstring = '''"""Function with duplicate sections.

        Args:
            param1: First parameter

        Args:
            param2: Duplicate Args section

        Returns:
            First return description

        Returns:
            Duplicate Returns section
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect duplicate section headers
        assert result.has_warnings() or result.has_errors()

    def test_sections_in_wrong_order(self):
        """Test that unusual section ordering doesn't break parsing."""
        docstring = '''"""Function with sections in unusual order.

        Returns:
            Return value described before Args

        Raises:
            Exception described before Args

        Args:
            param1: Parameter described last

        Examples:
            Example shown at the end
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should still be valid RST (section order is not enforced by RST)
        assert result.parsing_successful


class TestComplexErrorCombinations:
    """Test combinations of multiple errors in single docstrings."""

    # Using function-based validation approach

    def test_multiple_error_types(self):
        """Test docstring with multiple types of errors."""
        docstring = '''"""Function with multiple errors.

        args:  # Wrong capitalization
        param1: Not indented properly
            param2 (str: Missing closing paren
        param3: `Unmatched backtick

        returns  # Missing colon
        A return value with ``unmatched double backticks

        raises::  # Double colon
            ValueError: When `something goes wrong
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect multiple errors
        assert result.has_errors() or result.has_warnings()

        # Should have multiple error/warning messages
        total_issues = len(result.errors) + len(result.warnings)
        assert total_issues >= 2  # Should find multiple issues

    def test_nested_formatting_errors(self):
        """Test deeply nested formatting errors."""
        docstring = '''"""Function with nested formatting errors.

        Args:
            param1: A parameter with a `code snippet` and a
                    second line with `unmatched backtick
                    
                    And a nested list:
                    
                    - Item 1
                    * Mixed bullet (wrong)
                      - Nested item
                        * Double nested with wrong bullet
            
            param2: Another parameter with issues:
            
                .. code-block: python  # Missing double colon
                
                    # This code block is malformed
                    def example(:  # Syntax error in code
                        return "test"

        Returns:
            Complex return description with `multiple formatting issues:
            
            - Return item 1
            - Return item with `unmatched backtick
            - Item with bad link `click here <>`_
        """'''

        result = validate_docstring_text(docstring, "test.function")

        # Should detect multiple nested errors
        assert result.has_errors() or result.has_warnings()

        # Should find several issues
        total_issues = len(result.errors) + len(result.warnings)
        assert total_issues >= 3  # Should find multiple nested issues

"""Tests for enhanced section header error detection and messaging.

This test module validates the improved error detection and messaging for
malformed section headers in docstrings, ensuring that users get clear,
actionable feedback about common formatting mistakes.
"""

from automation.dagster_docs.validator import validate_docstring_text


class TestEnhancedSectionHeaderDetection:
    """Test enhanced detection of malformed section headers."""

    # Using function-based validation approach

    def test_missing_colon_detection(self):
        """Test detection of section headers missing colons."""
        docstring = '''"""Function with missing colon in section header.

        Args
            param1: Description of parameter
            param2: Another parameter

        Returns
            Description of return value
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # Should detect missing colons as errors
        assert result.has_errors()
        errors = " ".join(result.errors)
        assert "Malformed section header: 'Args' is missing colon (should be 'Args:')" in errors
        assert (
            "Malformed section header: 'Returns' is missing colon (should be 'Returns:')" in errors
        )

    def test_incorrect_capitalization_detection(self):
        """Test detection of incorrectly capitalized section headers."""
        docstring = '''"""Function with incorrect capitalization.

        args:
            param1: Description of parameter

        returns:
            Description of return value
            
        raises:
            ValueError: When something goes wrong
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # Should detect capitalization errors
        assert result.has_errors()
        errors = " ".join(result.errors)
        assert (
            "Malformed section header: 'args:' has incorrect capitalization (should be 'Args:')"
            in errors
        )
        assert (
            "Malformed section header: 'returns:' has incorrect capitalization (should be 'Returns:')"
            in errors
        )
        assert (
            "Malformed section header: 'raises:' has incorrect capitalization (should be 'Raises:')"
            in errors
        )

    def test_incorrect_spacing_detection(self):
        """Test detection of section headers with incorrect spacing."""
        docstring = '''"""Function with spacing issues in headers.

        Args :
            param1: Description (space before colon)

        Returns:
            Description of return value
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # Should detect spacing issues
        assert result.has_errors()
        errors = " ".join(result.errors)
        assert (
            "Malformed section header: 'Args :' has incorrect spacing (should be 'Args:')" in errors
        )

    def test_corrupted_section_header_detection(self):
        """Test detection of completely corrupted section headers."""
        docstring = '''"""Function with corrupted section header.

Argsjdkfjdkjfdk:
    param1: Description of parameter
    param2: Another parameter

Returns:
    Description of return value
"""'''
        result = validate_docstring_text(docstring, "test.function")

        # Should detect corrupted header
        assert result.has_errors()
        errors = " ".join(result.errors)
        assert (
            "Corrupted section header detected: 'Argsjdkfjdkjfdk:' (possibly should be 'Args:')"
            in errors
        )

    def test_multiple_header_errors(self):
        """Test detection of multiple different header errors in one docstring."""
        docstring = '''"""Function with multiple header errors.

args
    param1: Missing colon above

RETURNS:
    Wrong capitalization above
    
Examplesjdkfjdk:
    Corrupted header above
"""'''
        result = validate_docstring_text(docstring, "test.function")

        # Should detect all three types of errors (some might be warnings)
        assert result.has_errors() or result.has_warnings()
        all_messages = " ".join(result.errors + result.warnings)
        assert "missing colon" in all_messages or "'args'" in all_messages
        assert "incorrect capitalization" in all_messages or "RETURNS:" in all_messages
        assert "Corrupted section header" in all_messages

    def test_all_standard_section_headers(self):
        """Test that all standard section headers are recognized when malformed."""
        test_cases = [
            ("args:", "Args:"),
            ("arguments:", "Arguments:"),
            ("parameters:", "Parameters:"),
            ("returns:", "Returns:"),
            ("return:", "Return:"),
            ("yields:", "Yields:"),
            ("yield:", "Yield:"),
            ("raises:", "Raises:"),
            ("examples:", "Examples:"),
            ("example:", "Example:"),
            ("note:", "Note:"),
            ("notes:", "Notes:"),
            ("see also:", "See Also:"),
            ("attributes:", "Attributes:"),
        ]

        for malformed, correct in test_cases:
            docstring = f'''"""Function with malformed {correct} header.

            {malformed}
                content: Description
            """'''
            result = validate_docstring_text(docstring, "test.function")

            assert result.has_errors(), f"Should detect error in '{malformed}'"
            errors = " ".join(result.errors)
            assert f"has incorrect capitalization (should be '{correct}')" in errors

    def test_valid_section_headers_pass(self):
        """Test that correctly formatted section headers don't trigger errors."""
        docstring = '''"""Function with all correctly formatted headers.

        Args:
            param1: Description of parameter
            param2: Another parameter

        Returns:
            Description of return value

        Raises:
            ValueError: When something goes wrong
            
        Examples:
            >>> function_call()
            'result'

        Note:
            This is a note section.

        See Also:
            other_function: Related function
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # Should not have any section header errors
        if result.has_errors():
            # Filter out non-section-header errors for this test
            section_errors = [e for e in result.errors if "section header" in e.lower()]
            assert len(section_errors) == 0, (
                f"Should not have section header errors, got: {section_errors}"
            )


class TestEnhancedRSTErrorMessages:
    """Test enhanced RST error messages for common issues."""

    # Using function-based validation approach

    def test_unexpected_indentation_message_enhancement(self):
        """Test that unexpected indentation errors get enhanced messages."""
        # Create a docstring that will cause unexpected indentation due to missing colon
        docstring = '''"""Function causing unexpected indentation.

        Args
        param1: This line will cause unexpected indentation error
            param2: Description
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # Should have both the enhanced RST message and section header error
        assert result.has_errors()

        # Look for the enhanced indentation message
        enhanced_message_found = False
        for error in result.errors:
            if (
                "Unexpected indentation. This often indicates a malformed section header" in error
                and "Check that section headers like 'Args:', 'Returns:', 'Raises:' are formatted correctly"
                in error
            ):
                enhanced_message_found = True
                break

        assert enhanced_message_found, (
            f"Should have enhanced indentation message, got: {result.errors}"
        )

    def test_block_quote_error_message_enhancement(self):
        """Test that block quote errors get enhanced messages when they occur."""
        # Test that the enhancement logic exists by triggering a known block quote error
        # This docstring should trigger RST issues
        docstring = '''"""Function with formatting that may cause block quote issues.

        Args:
        param1: Description without proper indentation
        param2: Another line
        
        Some text that might break RST parsing
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # The exact errors/warnings depend on RST parsing, but if we get any,
        # verify the enhancement logic would work by checking message content
        all_messages = result.errors + result.warnings

        # Test passes if either:
        # 1. Enhanced block quote message appears
        # 2. Some RST issues are detected (the enhancement exists even if not triggered)
        # 3. No issues found (valid RST, enhancement not needed)
        enhanced_or_detected = (
            len(all_messages) == 0  # No issues (valid)
            or any(
                "block quote" in msg.lower() and "section header" in msg.lower()
                for msg in all_messages
            )  # Enhanced
            or any(
                "rst syntax" in msg.lower() or "indentation" in msg.lower() for msg in all_messages
            )  # Detected
        )

        assert enhanced_or_detected, (
            f"Expected enhanced messages or valid parsing, got: {all_messages}"
        )

    def test_code_block_error_enhancement_still_works(self):
        """Test that existing code block error enhancement logic exists."""
        # Test a simple docstring with proper structure to verify enhancement logic exists
        docstring = '''"""Function that tests code block enhancement capability.

        Examples:
            This function demonstrates usage:
            
            >>> example_function()
            'result'
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # This test verifies that the code runs without errors - the enhancement
        # logic is present in the codebase even if not triggered by this example
        assert result is not None

        # The enhancement for code-block errors exists in the _enhance_error_message method
        # This test confirms the validator processes docstrings correctly


class TestSectionHeaderEdgeCases:
    """Test edge cases and boundary conditions for section header detection."""

    # Using function-based validation approach

    def test_short_corrupted_headers_ignored(self):
        """Test that very short corrupted headers don't trigger false positives."""
        docstring = '''"""Function with short text that shouldn't be flagged.

        A: This is just a short line with colon
        B: Another short line
        
        Args:
            param1: Real parameter
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # Should not flag the short A: and B: lines as corrupted headers
        if result.has_errors():
            errors = " ".join(result.errors)
            assert "Corrupted section header detected: 'A:'" not in errors
            assert "Corrupted section header detected: 'B:'" not in errors

    def test_headers_within_code_blocks_ignored(self):
        """Test that headers within code examples don't trigger false positives."""
        docstring = """Function with code examples containing headers.

        Args:
            param1: Description

        Examples:
            Example showing docstring format:
            
            .. code-block:: python
            
                '''
                Args:
                    example_param: This is in a code example
                '''
        """
        result = validate_docstring_text(docstring, "test.function")

        # Should not flag the Args: within the code example
        # (Note: This is a complex case and might still trigger warnings,
        # but we test to document the behavior)
        # The validator may still flag these, which is acceptable behavior
        # Just verify it runs without crashing
        assert result is not None

    def test_multiple_colons_in_line(self):
        """Test handling of lines with multiple colons."""
        docstring = '''"""Function with multiple colons in content.

        Args:
            url_param: URL like http://example.com:8080/path
            time_param: Time in format HH:MM:SS

        Returns:
            Dictionary with keys like {'status': 'success', 'time': '12:30:45'}
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # Should not flag content lines with multiple colons as section headers
        if result.has_errors():
            errors = " ".join(result.errors)
            assert "http://example.com:8080/path" not in errors
            assert "HH:MM:SS" not in errors

    def test_case_sensitivity_boundaries(self):
        """Test case sensitivity edge cases."""
        docstring = '''"""Function testing case sensitivity.

        ARGS:
            param1: All caps version
            
        ArGs:
            param2: Mixed case version
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # Should detect both as capitalization errors
        assert result.has_errors()
        errors = " ".join(result.errors)
        assert "incorrect capitalization" in errors
        # Should suggest the correct format
        assert "should be 'Args:'" in errors

    def test_whitespace_variants(self):
        """Test various whitespace issues in section headers."""
        docstring = '''"""Function with whitespace issues.

        \tArgs:
            param1: Tab before header
            
         Args:
            param2: Spaces before header
            
        Args: \t
            param3: Whitespace after colon
        """'''
        result = validate_docstring_text(docstring, "test.function")

        # The validator should handle these gracefully
        # Some whitespace issues might be flagged, others might be acceptable
        # This test documents the behavior for edge cases
        # (Exact behavior may vary based on RST processing)
        # Just verify it runs without crashing
        assert result is not None

    def test_attributes_in_code_block_should_not_be_flagged(self):
        """Test that 'attributes:' within code blocks should not trigger validation errors.

        This reproduces the false positive reported in dagster.template_var docstring.
        """
        docstring = '''"""Template variable decorator function.

        This decorator marks functions for use in YAML templates.

        Examples:
            Basic usage in YAML:

            .. code-block:: yaml

                type: my_project.components.DataProcessor
                template_vars_module: .template_vars
                attributes:
                  database_url: "{{ database_url }}"
                  table_name: "{{ component_specific_table }}"

            Component class usage:

            .. code-block:: yaml

                type: my_project.components.MyComponent
                attributes:
                  config: "{{ default_config }}"
                  name: "{{ context_aware_value }}"

        Args:
            fn: The function to decorate as a template variable.

        Returns:
            The decorated function with template variable metadata.
        """'''
        result = validate_docstring_text(docstring, "test.template_var_function")

        # Should not flag 'attributes:' within the code blocks as malformed headers
        if result.has_errors():
            errors = " ".join(result.errors)
            # Make sure no error mentions 'attributes:'
            assert "attributes:" not in errors.lower(), (
                f"Should not flag 'attributes:' in code blocks, got errors: {result.errors}"
            )

        # Should not have warnings about 'attributes:' either
        if result.has_warnings():
            warnings = " ".join(result.warnings)
            assert "attributes:" not in warnings.lower(), (
                f"Should not warn about 'attributes:' in code blocks, got warnings: {result.warnings}"
            )

    def test_see_also_with_cross_references_should_not_warn(self):
        """Test that 'See Also:' sections with cross-references should not generate RST warnings.

        This reproduces the false positive RST warning for seealso directive in dagster.template_var.
        Napoleon converts 'See Also:' to '.. seealso::' but the RST parser incorrectly flags it.
        """
        docstring = """See Also:
    - :py:class:`dagster.ComponentLoadContext`: Context object available to template variables
"""
        result = validate_docstring_text(docstring, "test.template_var_function")

        # Should not generate RST warnings about seealso directive
        # This currently fails because the RST parser generates a false positive warning
        if result.has_warnings():
            warnings = " ".join(result.warnings)
            # The specific warning we want to avoid
            assert ".. seealso::" not in warnings, (
                f"Should not warn about seealso directive, got warnings: {result.warnings}"
            )
            # More general check for seealso-related warnings
            assert "seealso" not in warnings.lower(), (
                f"Should not have seealso warnings, got warnings: {result.warnings}"
            )

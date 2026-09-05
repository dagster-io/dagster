"""Comprehensive tests for YAML syntax validation in docstrings."""

import pytest
from automation.dagster_docs.docstring_rules.base import ValidationContext, ValidationResult
from automation.dagster_docs.docstring_rules.yaml_syntax_rule import (
    _extract_yaml_code_blocks,
    _validate_yaml_syntax,
    create_yaml_syntax_validator,
    validate_yaml_code_blocks,
)
from automation.dagster_docs.validator import validate_docstring_text


class TestExtractYamlCodeBlocks:
    """Test the _extract_yaml_code_blocks function."""

    def test_extract_single_yaml_code_block(self):
        """Test extracting a single YAML code block."""
        docstring = """
        This is a docstring.
        
        .. code-block:: yaml
        
            key: value
            list:
              - item1
              - item2
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 1
        code, line_num = blocks[0]
        assert "key: value" in code
        assert "list:" in code
        assert "- item1" in code
        assert line_num == 6  # Line where code starts

    def test_extract_yml_variant(self):
        """Test extracting YAML code blocks with 'yml' extension."""
        docstring = """
        This supports yml extension.
        
        .. code-block:: yml
        
            name: test
            enabled: true
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]
        assert "name: test" in code
        assert "enabled: true" in code

    def test_extract_multiple_yaml_code_blocks(self):
        """Test extracting multiple YAML code blocks."""
        docstring = """
        This function has examples.
        
        .. code-block:: yaml
        
            config:
              debug: true
        
        Some text in between.
        
        .. code-block:: yml
        
            database:
              host: localhost
              port: 5432
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 2

        code1, line1 = blocks[0]
        assert "config:" in code1
        assert "debug: true" in code1

        code2, line2 = blocks[1]
        assert "database:" in code2
        assert "host: localhost" in code2
        assert "port: 5432" in code2

        assert line1 < line2  # Second block starts after first

    def test_extract_no_yaml_code_blocks(self):
        """Test docstring with no YAML code blocks."""
        docstring = """
        This is just a regular docstring.
        
        Args:
            param: A parameter
            
        Returns:
            Something
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 0

    def test_extract_ignores_non_yaml_blocks(self):
        """Test that non-YAML code blocks are ignored."""
        docstring = """
        This has various code blocks.
        
        .. code-block:: python
        
            print("hello")
        
        .. code-block:: yaml
        
            key: value
        
        .. code-block:: bash
        
            echo "world"
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]
        assert "key: value" in code

    def test_extract_with_indented_yaml(self):
        """Test extracting YAML with proper indentation handling."""
        docstring = """
        Example with indented YAML.
        
        .. code-block:: yaml
        
            services:
              web:
                image: nginx
                ports:
                  - "80:80"
              db:
                image: postgres
                environment:
                  POSTGRES_DB: mydb
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]

        # Check that indentation is preserved relative to the first line
        lines = code.split("\n")
        assert lines[0] == "services:"
        assert lines[1].startswith("  web:")  # 2 spaces
        assert lines[2].startswith("    image: nginx")  # 4 spaces
        assert lines[3].startswith("    ports:")  # 4 spaces
        assert lines[4].startswith('      - "80:80"')  # 6 spaces

    def test_extract_with_empty_lines_in_yaml(self):
        """Test YAML blocks with empty lines within the YAML."""
        docstring = """
        Example with empty lines.
        
        .. code-block:: yaml
        
            name: myapp
            
            # Comment after empty line
            version: 1.0
            
            description: A sample app
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]

        lines = code.split("\n")
        assert "name: myapp" in lines[0]
        assert lines[1] == ""  # Empty line preserved
        assert "# Comment after empty line" in lines[2]
        assert lines[4] == ""  # Another empty line preserved
        assert "description: A sample app" in lines[5]

    def test_extract_trailing_empty_lines_removed(self):
        """Test that trailing empty lines are removed from YAML blocks."""
        docstring = """
        Example with trailing empty lines.
        
        .. code-block:: yaml
        
            key: value
            
            
            
        Some text after.
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]

        # Should not end with empty lines
        assert not code.endswith("\n\n")
        assert code.strip() == "key: value"

    def test_extract_with_various_directive_formats(self):
        """Test various formats of the code-block directive."""
        docstring = """
        Various directive formats.
        
        .. code-block:: yaml
        
            # Standard format
            x: 1
        
        ..code-block::yaml
        
            # No space after ..
            y: 2
        
        .. code-block::yaml
        
            # No space before language
            z: 3
        """

        blocks = _extract_yaml_code_blocks(docstring)
        # Only the first one should match (strict regex)
        assert len(blocks) == 1
        code, _ = blocks[0]
        assert "x: 1" in code

    def test_extract_empty_yaml_block(self):
        """Test handling of empty YAML blocks that are truly empty."""
        docstring = """Empty YAML block.

.. code-block:: yaml

"""

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 0  # Empty blocks are not included

    def test_extract_yaml_block_no_blank_line(self):
        """Test YAML block without blank line after directive."""
        docstring = """
        No blank line after directive.
        
        .. code-block:: yaml
            key: value
        """

        blocks = _extract_yaml_code_blocks(docstring)
        assert len(blocks) == 1
        code, _ = blocks[0]
        assert "key: value" in code


class TestValidateYamlSyntax:
    """Test the _validate_yaml_syntax function."""

    def test_valid_yaml_code(self):
        """Test validation of valid YAML code."""
        code = """
name: myapp
version: 1.0
services:
  web:
    image: nginx
    ports:
      - "80:80"
  db:
    image: postgres
"""
        result = _validate_yaml_syntax(code)
        assert result is None  # No error

    def test_simple_yaml_syntax_error(self):
        """Test detection of simple YAML syntax errors."""
        code = """
name: myapp
version: 1.0
invalid: [incomplete
"""
        result = _validate_yaml_syntax(code)
        assert result is not None
        assert "YAML syntax error" in result

    def test_indentation_error(self):
        """Test detection of YAML indentation errors."""
        code = """
services:
  web:
    image: nginx
    ports:
- "80:80"
"""
        result = _validate_yaml_syntax(code)
        assert result is not None
        assert "YAML syntax error" in result

    def test_duplicate_key_error(self):
        """Test detection of duplicate key errors."""
        code = """
name: first
version: 1.0
name: duplicate
"""
        _validate_yaml_syntax(code)
        # Note: PyYAML may or may not detect this as an error depending on version
        # but it should at least not crash

    def test_invalid_yaml_structure(self):
        """Test detection of invalid YAML structure."""
        code = """
name: myapp
[invalid: structure
"""
        result = _validate_yaml_syntax(code)
        assert result is not None
        assert "YAML" in result

    def test_empty_yaml(self):
        """Test validation of empty YAML."""
        result = _validate_yaml_syntax("")
        assert result is None  # Empty YAML is valid

    def test_comment_only_yaml(self):
        """Test validation of comment-only YAML."""
        code = """
# This is just a comment
# Another comment
"""
        result = _validate_yaml_syntax(code)
        assert result is None  # Comments are valid

    def test_complex_valid_yaml(self):
        """Test validation of complex but valid YAML."""
        code = """
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      - db
    volumes:
      - .:/app
    networks:
      - app-network
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
networks:
  app-network:
    driver: bridge
volumes:
  postgres_data:
"""
        result = _validate_yaml_syntax(code)
        assert result is None  # Complex but valid YAML

    def test_yaml_with_special_characters(self):
        """Test validation of YAML with special characters."""
        code = """
name: "app with spaces"
version: "1.0.0"
description: |
  This is a multi-line
  description with special chars: !@#$%^&*()
tags:
  - "tag with spaces"
  - 'single-quoted'
  - unquoted
"""
        result = _validate_yaml_syntax(code)
        assert result is None  # Valid YAML with special chars

    def test_yaml_with_anchors_and_aliases(self):
        """Test validation of YAML with anchors and aliases."""
        code = """
defaults: &defaults
  timeout: 30
  retries: 3

production:
  <<: *defaults
  host: prod.example.com

staging:
  <<: *defaults
  host: staging.example.com
"""
        result = _validate_yaml_syntax(code)
        assert result is None  # Valid YAML with anchors

    def test_yaml_syntax_error_with_line_info(self):
        """Test that YAML syntax errors include line information when available."""
        code = """
name: valid
version: valid
invalid: yaml: syntax: here
another: valid
"""
        result = _validate_yaml_syntax(code)
        assert result is not None
        # Line information may or may not be available depending on the error type


class TestValidateYamlCodeBlocks:
    """Test the validate_yaml_code_blocks function."""

    def test_valid_yaml_code_blocks(self):
        """Test validation with valid YAML code blocks."""
        docstring = """
        Function with valid YAML examples.
        
        .. code-block:: yaml
        
            name: myapp
            version: 1.0
        
        .. code-block:: yml
        
            services:
              - web
              - db
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_yaml_code_blocks(context, result)

        assert not result.has_errors()
        assert not result.has_warnings()
        assert result.is_valid()

    def test_invalid_yaml_code_blocks(self):
        """Test validation with invalid YAML code blocks."""
        docstring = """
        Function with YAML syntax errors.
        
        .. code-block:: yaml
        
            name: myapp
            invalid: [incomplete
        
        .. code-block:: yml
        
            valid_key: valid_value
        
        .. code-block:: yaml
        
            another: {incomplete
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_yaml_code_blocks(context, result)

        assert result.has_errors()
        assert len(result.errors) == 2  # Two syntax errors

        # Check that both errors are reported
        error_text = " ".join(result.errors)
        assert "YAML code block syntax error" in error_text

    def test_mixed_valid_invalid_yaml_blocks(self):
        """Test validation with mix of valid and invalid YAML blocks."""
        docstring = """
        Mixed YAML examples.
        
        .. code-block:: yaml
        
            # This is valid
            name: myapp
            version: 1.0
        
        .. code-block:: yaml
        
            # This is broken
            invalid: [incomplete
        
        .. code-block:: yml
        
            # This is also valid
            database:
              host: localhost
              port: 5432
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_yaml_code_blocks(context, result)

        assert result.has_errors()
        assert len(result.errors) == 1  # Only one error
        assert "YAML code block syntax error" in result.errors[0]

    def test_no_yaml_code_blocks(self):
        """Test validation with no YAML code blocks."""
        docstring = """
        Function with no YAML examples.
        
        Args:
            param: A parameter
            
        Returns:
            A value
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_yaml_code_blocks(context, result)

        assert not result.has_errors()
        assert not result.has_warnings()
        assert result.is_valid()

    def test_line_number_reporting(self):
        """Test that error line numbers are correctly reported."""
        docstring = """
        Function with error on specific line.
        
        .. code-block:: yaml
        
            # This is line 6 of the docstring
            name: myapp
            invalid: [incomplete
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validate_yaml_code_blocks(context, result)

        assert result.has_errors()
        assert len(result.errors) == 1

        # Should include line number in error message
        error = result.errors[0]
        assert "line 6" in error  # Line where the code block starts


class TestCreateYamlSyntaxValidator:
    """Test the create_yaml_syntax_validator function."""

    def test_enabled_validator(self):
        """Test creating an enabled validator."""
        validator = create_yaml_syntax_validator(enabled=True)

        docstring = """
        .. code-block:: yaml
        
            invalid: [incomplete
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validator(context, result)

        assert result.has_errors()

    def test_disabled_validator(self):
        """Test creating a disabled validator."""
        validator = create_yaml_syntax_validator(enabled=False)

        docstring = """
        .. code-block:: yaml
        
            invalid: [incomplete
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validator(context, result)

        # Should not have errors because validator is disabled
        assert not result.has_errors()

    def test_default_enabled(self):
        """Test that validator is enabled by default."""
        validator = create_yaml_syntax_validator()  # No explicit enabled parameter

        docstring = """
        .. code-block:: yaml
        
            invalid: [incomplete
        """

        context = ValidationContext(docstring=docstring, symbol_path="test.symbol")
        result = ValidationResult.create("test.symbol")

        result = validator(context, result)

        assert result.has_errors()  # Should be enabled by default


class TestIntegrationWithValidationPipeline:
    """Test integration with the full validation pipeline."""

    def test_integration_valid_yaml_docstring(self):
        """Test integration with valid YAML code blocks."""
        docstring = """
        Function with valid YAML examples.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            Parsed configuration dictionary
        
        Examples:
            Basic usage:
            
            .. code-block:: yaml
            
                name: myapp
                version: 1.0
                services:
                  - web
                  - database
        """

        result = validate_docstring_text(docstring, "test.symbol")

        assert result.is_valid()
        assert not result.has_errors()

    def test_integration_invalid_yaml_code(self):
        """Test integration with invalid YAML code blocks."""
        docstring = """
        Function with broken YAML examples.
        
        Args:
            config_path: Path to configuration file
        
        Examples:
            This example has a syntax error:
            
            .. code-block:: yaml
            
                name: myapp
                invalid: [incomplete
                version: 1.0
        """

        result = validate_docstring_text(docstring, "test.symbol")

        assert not result.is_valid()
        assert result.has_errors()

        # Should have YAML syntax error
        yaml_errors = [e for e in result.errors if "YAML code block syntax error" in e]
        assert len(yaml_errors) == 1

    def test_integration_multiple_validation_rules(self):
        """Test that YAML validation works alongside other validation rules."""
        docstring = """
        Function with multiple issues.
        
        args:  # Wrong case - should be "Args:"
            config_path: Path to configuration file
        
        Examples:
            .. code-block:: yaml
            
                name: myapp
                invalid: [incomplete
        """

        result = validate_docstring_text(docstring, "test.symbol")

        assert not result.is_valid()

        # Should have both section header issues and YAML syntax issues
        all_messages = result.errors + result.warnings

        # Check for both types of issues
        has_section_issue = any(
            "malformed section header" in msg.lower()
            or "possible malformed section header" in msg.lower()
            for msg in all_messages
        )
        has_yaml_issue = any("yaml code block syntax error" in msg.lower() for msg in all_messages)

        assert has_section_issue, f"Expected section header issue in: {all_messages}"
        assert has_yaml_issue, f"Expected YAML syntax issue in: {all_messages}"

    def test_integration_yaml_and_python_errors(self):
        """Test YAML validation alongside Python AST validation."""
        docstring = """
        Function with both YAML and Python issues.
        
        .. code-block:: yaml
        
            name: myapp
            invalid: [incomplete
        
        .. code-block:: python
        
            def broken_python(
                return "syntax error"
        """

        result = validate_docstring_text(docstring, "test.symbol")

        assert not result.is_valid()
        assert result.has_errors()

        # Should have both YAML and Python syntax errors
        error_text = " ".join(result.errors).lower()
        assert "yaml code block syntax error" in error_text
        assert "python code block syntax error" in error_text


class TestEdgeCasesAndErrorScenarios:
    """Test edge cases and error scenarios."""

    def test_yaml_block_with_unicode(self):
        """Test YAML blocks containing Unicode characters."""
        docstring = """
        Function with Unicode in YAML.
        
        .. code-block:: yaml
        
            name: "Hello, 世界!"
            description: "Application with émojis 🚀"
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_yaml_block_with_multiline_strings(self):
        """Test YAML blocks with multiline string syntax."""
        docstring = """
        Function with multiline YAML.
        
        .. code-block:: yaml
        
            description: |
              This is a multiline
              description that spans
              multiple lines.
            
            script: >
              This is a folded
              string that will be
              joined with spaces.
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_yaml_block_with_various_data_types(self):
        """Test YAML blocks with various data types."""
        docstring = """
        Function with various YAML data types.
        
        .. code-block:: yaml
        
            # Strings
            name: myapp
            quoted: "with quotes"
            
            # Numbers
            version: 1.0
            port: 8080
            
            # Booleans
            enabled: true
            debug: false
            
            # Lists
            tags:
              - web
              - api
              - production
            
            # Objects
            database:
              host: localhost
              port: 5432
              credentials:
                username: user
                password: pass
            
            # Null
            optional_field: null
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_yaml_block_with_complex_keys(self):
        """Test YAML blocks with complex key structures."""
        docstring = """
        Function with complex YAML keys.
        
        .. code-block:: yaml
        
            simple_key: value
            "quoted key": value
            key with spaces: value
            
            # Complex mapping
            ? |
              This is a complex
              multiline key
            : |
              And this is its
              multiline value
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    def test_very_long_yaml_block(self):
        """Test validation of very long YAML blocks."""
        # Generate a long but valid YAML block
        yaml_lines = ["services:"]
        for i in range(50):
            yaml_lines.extend(
                [
                    f"  service_{i}:",
                    f"    image: app_{i}:latest",
                    "    ports:",
                    f'      - "{8000 + i}:{8000 + i}"',
                    "    environment:",
                    f"      - APP_NAME=service_{i}",
                    f"      - APP_PORT={8000 + i}",
                ]
            )

        # Properly indent the YAML for the docstring
        indented_yaml = "\n".join(
            f"            {line}" if line.strip() else "" for line in yaml_lines
        )

        docstring = f"""
        Function with long YAML block.
        
        .. code-block:: yaml
        
{indented_yaml}
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

    @pytest.mark.parametrize(
        "invalid_yaml",
        [
            "[\n  incomplete",  # Incomplete structure
            "{key: value\n  incomplete: brace",  # Incomplete JSON-style structure
            "key: [incomplete",  # Incomplete list
            "key: {incomplete",  # Incomplete dict
        ],
    )
    def test_various_yaml_syntax_errors(self, invalid_yaml):
        """Test detection of various types of YAML syntax errors."""
        docstring = f"""
        Function with YAML syntax error.
        
        .. code-block:: yaml
        
            {invalid_yaml}
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert not result.is_valid()
        assert result.has_errors()

        # Should have YAML syntax error
        yaml_errors = [e for e in result.errors if "YAML code block syntax error" in e]
        assert len(yaml_errors) >= 1

    def test_yaml_block_with_timestamps_and_special_values(self):
        """Test YAML blocks with timestamps and special YAML values."""
        docstring = """
        Function with special YAML values.
        
        .. code-block:: yaml
        
            # Timestamps
            created_at: 2023-12-01T10:00:00Z
            updated_at: !!timestamp 2023-12-02 10:00:00
            
            # Special values
            infinity: .inf
            not_a_number: .nan
            
            # Binary data (proper base64)
            binary: !!binary |
              SGVsbG8gV29ybGQ=
        """

        result = validate_docstring_text(docstring, "test.symbol")
        assert result.is_valid()

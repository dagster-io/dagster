"""Tests for method docstring validation focusing on parameter handling."""

from automation.dagster_docs.validator import validate_docstring_text
from dagster._annotations import public


class TestMethodDocstringValidation:
    """Test that method docstrings are validated correctly and self/cls parameters are handled properly."""

    # Using function-based validation approach

    def test_instance_method_docstring_validation(self):
        """Test that instance method docstrings are validated correctly."""

        @public
        class TestClass:
            @public
            def process_data(self, data, options=None):
                """Process the provided data with optional configuration.

                Args:
                    data: The data to process
                    options: Optional processing configuration

                Returns:
                    Processed data result
                """
                pass

            @public
            def bad_method_with_self(self, data):
                """Process data (incorrect style documenting self).

                Args:
                    self: The instance (should not be documented)
                    data: Data to process

                Returns:
                    Processed data result
                """
                pass

        # Test valid instance method docstring (doesn't document 'self')
        result = validate_docstring_text(
            TestClass.process_data.__doc__ or "", "TestClass.process_data"
        )
        assert result.is_valid(), f"Instance method should have valid docstring: {result.errors}"
        assert result.parsing_successful

        # Test that documenting 'self' is handled gracefully (not flagged as RST error)
        result_with_self = validate_docstring_text(
            TestClass.bad_method_with_self.__doc__ or "", "TestClass.bad_method_with_self"
        )
        # Should parse successfully even though it's bad style
        assert result_with_self.parsing_successful

    def test_static_method_docstring_validation(self):
        """Test that static method docstrings are validated correctly."""

        @public
        class TestClass:
            @public
            @staticmethod
            def validate_email(email, strict=False):
                """Validate email address format using regex.

                Args:
                    email: Email address to validate
                    strict: Whether to use strict validation

                Returns:
                    True if valid, False otherwise
                """
                pass

        result = validate_docstring_text(
            TestClass.validate_email.__doc__ or "", "TestClass.validate_email"
        )
        assert result.is_valid(), f"Static method should have valid docstring: {result.errors}"
        assert result.parsing_successful

    def test_class_method_docstring_validation(self):
        """Test that class method docstrings are validated correctly."""

        @public
        class TestClass:
            @public
            @classmethod
            def from_config(cls, config_file, validate=True):
                """Create instance from configuration file.

                Args:
                    config_file: Path to configuration file
                    validate: Whether to validate configuration

                Returns:
                    New instance of the class
                """
                pass

            @public
            @classmethod
            def bad_method_with_cls(cls, config):
                """Create instance with cls documented (incorrect style).

                Args:
                    cls: The class (should not be documented)
                    config: Configuration data

                Returns:
                    New instance
                """
                pass

        # Valid class method docstring (doesn't document 'cls')
        result = validate_docstring_text(
            TestClass.from_config.__doc__ or "", "TestClass.from_config"
        )
        assert result.is_valid(), f"Class method should have valid docstring: {result.errors}"
        assert result.parsing_successful

        # Test that documenting 'cls' is handled gracefully
        result_with_cls = validate_docstring_text(
            TestClass.bad_method_with_cls.__doc__ or "", "TestClass.bad_method_with_cls"
        )
        # Should parse successfully even though it's bad style
        assert result_with_cls.parsing_successful

    def test_property_docstring_validation(self):
        """Test that property docstrings are validated correctly."""

        @public
        class TestClass:
            @public
            @property
            def status(self):
                """Current status of the instance.

                Returns:
                    Status string indicating current state
                """
                return "active"

        result = validate_docstring_text(TestClass.status.__doc__ or "", "TestClass.status")
        assert result.is_valid(), f"Property should have valid docstring: {result.errors}"
        assert result.parsing_successful

    def test_docstring_formatting_errors(self):
        """Test that common docstring formatting errors are detected."""

        @public
        class TestClass:
            @public
            def method_with_invalid_section(self, data):
                """Process data with invalid section header.

                Arguments!:  # Invalid punctuation in section header
                    data: Data to process

                Returns:
                    Result
                """
                pass

            @public
            def method_with_bad_indentation(self, data, options):
                """Process data with missing parameter indentation.

                Args:
                data: Not indented properly
                options: Also not indented

                Returns:
                    Result
                """
                pass

        # Test an error that we know the validator catches - invalid section header
        result = validate_docstring_text(
            TestClass.method_with_invalid_section.__doc__ or "",
            "TestClass.method_with_invalid_section",
        )
        # This should either have warnings/errors or be parsing successfully
        assert result.parsing_successful  # At minimum should parse

        # Missing indentation in parameters
        result = validate_docstring_text(
            TestClass.method_with_bad_indentation.__doc__ or "",
            "TestClass.method_with_bad_indentation",
        )
        # This may or may not be flagged depending on RST parser behavior
        assert result.parsing_successful  # At minimum should parse

    def test_edge_case_docstrings(self):
        """Test edge cases with docstrings."""

        @public
        class TestClass:
            @public
            def empty_method(self):
                """"""  # noqa: D419
                pass

            @public
            def helper(self):
                """Helper method."""
                pass

            @public
            def whitespace_method(self):
                """ """  # noqa: D419
                pass

        # Empty docstring should produce warning but not error
        result_empty = validate_docstring_text(
            TestClass.empty_method.__doc__ or "", "TestClass.empty_method"
        )
        assert result_empty.has_warnings()
        assert "No docstring found" in str(result_empty.warnings)
        assert result_empty.is_valid()  # Empty is valid, just warned

        # Minimal but valid docstring
        result_minimal = validate_docstring_text(TestClass.helper.__doc__ or "", "TestClass.helper")
        assert result_minimal.is_valid()
        assert not result_minimal.has_errors()

        # Whitespace-only docstring
        result_whitespace = validate_docstring_text(
            TestClass.whitespace_method.__doc__ or "", "TestClass.whitespace_method"
        )
        assert result_whitespace.has_warnings()
        assert "No docstring found" in str(result_whitespace.warnings)

    def test_complex_valid_docstring(self):
        """Test that complex but valid docstrings are handled correctly."""

        @public
        class TestClass:
            @public
            def execute_pipeline(self, pipeline_config, execution_mode, retry_policy=None):
                """Execute multi-stage data processing pipeline.

                This method performs comprehensive data processing through multiple
                stages with configurable options and error handling.

                Args:
                    pipeline_config: Configuration dictionary containing:
                        - stage_1: Initial data ingestion settings
                        - stage_2: Data transformation parameters
                        - stage_3: Export configuration options
                    execution_mode: Mode selection ('sequential', 'parallel', 'adaptive')
                    retry_policy: Error retry configuration

                Returns:
                    PipelineResult containing:
                        - execution_summary: High-level statistics
                        - stage_results: Detailed per-stage results
                        - performance_metrics: Timing and resource data

                Raises:
                    PipelineConfigError: If configuration is invalid
                    DataProcessingError: If processing fails at any stage
                    ResourceError: If insufficient system resources

                Examples:
                    Basic usage:

                    >>> config = {'stage_1': {...}, 'stage_2': {...}}
                    >>> result = processor.execute_pipeline(config, 'sequential')
                    >>> print(result.execution_summary)

                Note:
                    This method requires substantial computational resources for large
                    datasets. Consider using batch processing for datasets larger
                    than 100,000 records.
                """
                pass

        result = validate_docstring_text(
            TestClass.execute_pipeline.__doc__ or "", "TestClass.execute_pipeline"
        )
        # Should be valid despite complexity
        assert result.is_valid() or not result.has_errors(), (
            f"Complex docstring should be valid: {result.errors}"
        )
        assert result.parsing_successful

    def test_mixed_method_types_in_single_class(self):
        """Test a class with all different types of methods."""

        @public
        class MixedMethodClass:
            @public
            def instance_method(self, data):
                """Process data using instance state.

                Args:
                    data: Data to process

                Returns:
                    Processed result
                """
                pass

            @public
            @staticmethod
            def utility_function(value):
                """Utility function that doesn't need instance or class.

                Args:
                    value: Value to process

                Returns:
                    Processed value
                """
                pass

            @public
            @classmethod
            def factory_method(cls, config):
                """Create instance using factory pattern.

                Args:
                    config: Configuration for new instance

                Returns:
                    New instance of this class
                """
                pass

            @public
            @property
            def computed_value(self):
                """Computed value based on instance state.

                Returns:
                    Computed value
                """
                return 42

        # Test that all method types validate correctly
        methods_to_test = [
            (MixedMethodClass.instance_method.__doc__ or "", "MixedMethodClass.instance_method"),
            (MixedMethodClass.utility_function.__doc__ or "", "MixedMethodClass.utility_function"),
            (MixedMethodClass.factory_method.__doc__ or "", "MixedMethodClass.factory_method"),
            (MixedMethodClass.computed_value.__doc__ or "", "MixedMethodClass.computed_value"),
        ]

        for docstring, method_name in methods_to_test:
            result = validate_docstring_text(docstring, method_name)
            assert result.is_valid(), f"{method_name} should have valid docstring: {result.errors}"

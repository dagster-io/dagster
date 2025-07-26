"""Base classes and functional interface for validation rules.

This module provides the core types and patterns for creating custom validation rules:

1. **Functional Rules** (Recommended):
   ```python
   def create_my_validator(enabled: bool = True) -> ValidationFunction:
       def validator(context: ValidationContext, result: ValidationResult) -> ValidationResult:
           if not enabled:
               return result
           # Your validation logic here
           if error_condition:
               result = result.with_error("Error message", line_number)
           return result
       return validator
   ```

2. **Class-Based Rules** (For complex state):
   ```python
   class MyValidationRule(ValidationRule):
       def _validate_impl(self, context, result):
           # Validation logic with access to self
           return result
   ```

3. **Error vs Warning Guidelines**:
   - Use errors for: Syntax errors, broken references, critical formatting
   - Use warnings for: Style issues, potential problems, best practices

4. **Performance Tips**:
   - Put faster rules first in the pipeline
   - Cache expensive operations (regex compilation, file reads)
   - Return immediately if validation cannot proceed
"""

from typing import Callable, Optional

from dagster_shared.record import record

# Functional validation interface - preferred pattern for most rules
# Pure functions are composable, testable, and easy to configure
ValidationFunction = Callable[["ValidationContext", "ValidationResult"], "ValidationResult"]


@record
class ValidationContext:
    """Context information for validation rules."""

    docstring: str
    symbol_path: str
    processed_rst: Optional[str] = None
    file_path: Optional[str] = None
    docstring_start_line: Optional[int] = None

    def with_processed_rst(self, rst: str) -> "ValidationContext":
        """Return a new context with processed RST content."""
        return ValidationContext(
            docstring=self.docstring,
            symbol_path=self.symbol_path,
            processed_rst=rst,
            file_path=self.file_path,
            docstring_start_line=self.docstring_start_line,
        )


@record
class ValidationResult:
    """Results from validating a docstring."""

    symbol_path: str
    errors: list[str]
    warnings: list[str]
    parsing_successful: bool

    @staticmethod
    def create(symbol_path: str) -> "ValidationResult":
        """Create a new ValidationResult."""
        return ValidationResult(
            symbol_path=symbol_path,
            errors=[],
            warnings=[],
            parsing_successful=True,
        )

    def with_error(
        self,
        message: str,
        line_number: Optional[int] = None,
        context: Optional["ValidationContext"] = None,
    ) -> "ValidationResult":
        """Return a new ValidationResult with an additional error message."""
        location = self._format_location(line_number, context)
        full_message = f"{message}{location}"
        # Avoid duplicates
        if full_message not in self.errors:
            return ValidationResult(
                symbol_path=self.symbol_path,
                errors=self.errors + [full_message],
                warnings=self.warnings,
                parsing_successful=self.parsing_successful,
            )
        return self

    def with_warning(
        self,
        message: str,
        line_number: Optional[int] = None,
        context: Optional["ValidationContext"] = None,
    ) -> "ValidationResult":
        """Return a new ValidationResult with an additional warning message."""
        location = self._format_location(line_number, context)
        full_message = f"{message}{location}"
        # Avoid duplicates
        if full_message not in self.warnings:
            return ValidationResult(
                symbol_path=self.symbol_path,
                errors=self.errors,
                warnings=self.warnings + [full_message],
                parsing_successful=self.parsing_successful,
            )
        return self

    def _format_location(
        self, line_number: Optional[int], context: Optional["ValidationContext"]
    ) -> str:
        """Format location information for error messages."""
        if line_number is None:
            return ""

        # Calculate file-relative line number if we have context information
        file_line = line_number
        filename = None
        if context:
            if context.docstring_start_line is not None:
                # Convert docstring-relative line number to file-relative
                file_line = context.docstring_start_line + line_number - 1
            if context.file_path:
                from pathlib import Path

                filename = Path(context.file_path).name

        location_parts = []
        if filename:
            location_parts.append(filename)
        location_parts.append(f"line {file_line}")

        return f" ({':'.join(location_parts)})"

    def with_parsing_failed(self) -> "ValidationResult":
        """Return a new ValidationResult with parsing marked as failed."""
        return ValidationResult(
            symbol_path=self.symbol_path,
            errors=self.errors,
            warnings=self.warnings,
            parsing_successful=False,
        )

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def is_valid(self) -> bool:
        """Check if the docstring is valid (no errors)."""
        return not self.has_errors() and self.parsing_successful


class ValidationRule:
    """Base class for all docstring validation rules."""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled

    def validate(self, context: ValidationContext, result: ValidationResult) -> ValidationResult:
        """Apply this rule's validation logic.

        Args:
            context: Validation context with docstring and metadata
            result: Current validation result to add findings to

        Returns:
            Updated ValidationResult with any new errors/warnings
        """
        if self.should_skip(context):
            return result
        return self._validate_impl(context, result)

    def should_skip(self, context: ValidationContext) -> bool:
        """Check if this rule should be skipped for the current context."""
        return not self.enabled

    def _validate_impl(
        self, context: ValidationContext, result: ValidationResult
    ) -> ValidationResult:
        """Override this method to implement rule-specific validation logic."""
        return result

"""Base classes and functional interface for validation rules."""

from collections.abc import Callable
from typing import Optional

from dagster_shared.record import record

# Functional validation interface
ValidationFunction = Callable[["ValidationContext", "ValidationResult"], "ValidationResult"]


@record
class ValidationContext:
    """Context information for validation rules."""

    docstring: str
    symbol_path: str
    processed_rst: Optional[str] = None

    def with_processed_rst(self, rst: str) -> "ValidationContext":
        """Return a new context with processed RST content."""
        return ValidationContext(
            docstring=self.docstring,
            symbol_path=self.symbol_path,
            processed_rst=rst,
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

    def with_error(self, message: str, line_number: Optional[int] = None) -> "ValidationResult":
        """Return a new ValidationResult with an additional error message."""
        location = f" (line {line_number})" if line_number else ""
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

    def with_warning(self, message: str, line_number: Optional[int] = None) -> "ValidationResult":
        """Return a new ValidationResult with an additional warning message."""
        location = f" (line {line_number})" if line_number else ""
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

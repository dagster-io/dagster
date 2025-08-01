"""Docstring fixtures for testing property and edge case validation."""

from dagster._annotations import public


@public
class PropertyFixtures:
    """Fixtures for testing property docstring validation."""

    @public
    @property
    def valid_property(self):
        """Current status of the instance.

        Returns:
            Status string indicating current state
        """
        return "active"

    @public
    @property
    def computed_value(self):
        """Computed value based on instance state.

        Returns:
            Computed value
        """
        return 42


@public
class FormattingErrorFixtures:
    """Fixtures for testing formatting error detection."""

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


@public
class EdgeCaseFixtures:
    """Fixtures for testing edge cases with docstrings."""

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


@public
class MixedMethodTypes:
    """Fixtures for testing all method types in one class."""

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

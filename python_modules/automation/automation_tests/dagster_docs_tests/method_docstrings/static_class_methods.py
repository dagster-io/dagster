"""Docstring fixtures for testing static and class method validation."""

from dagster._annotations import public


@public
class StaticMethodFixtures:
    """Fixtures for testing static method docstring validation."""

    @public
    @staticmethod
    def valid_static_method(email, strict=False):
        """Validate email address format using regex.

        Args:
            email: Email address to validate
            strict: Whether to use strict validation

        Returns:
            True if valid, False otherwise
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
class ClassMethodFixtures:
    """Fixtures for testing class method docstring validation."""

    @public
    @classmethod
    def valid_class_method(cls, config_file, validate=True):
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
    def class_method_documenting_cls(cls, config):
        """Create instance with cls documented (incorrect style).

        Args:
            cls: The class (should not be documented)
            config: Configuration data

        Returns:
            New instance
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

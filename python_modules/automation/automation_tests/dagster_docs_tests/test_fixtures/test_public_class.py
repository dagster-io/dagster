"""Test fixtures for @public method validation.

This module contains test classes with various combinations of public and non-public methods
to verify that the docstring validator correctly identifies only @public methods on @public classes.
"""

from dagster._annotations import public


@public
class PublicClass:
    """A public class with mixed public and non-public methods."""

    @public
    def public_instance_method(self):
        """This is a public instance method that should be validated."""
        return "public_instance"

    def non_public_instance_method(self):
        """This is a non-public instance method that should NOT be validated."""
        return "non_public_instance"

    @staticmethod
    @public
    def public_static_method():
        """This is a public static method that should be validated."""
        return "public_static"

    @staticmethod
    def non_public_static_method():
        """This is a non-public static method that should NOT be validated."""
        return "non_public_static"

    @classmethod
    @public
    def public_class_method(cls):
        """This is a public class method that should be validated."""
        return "public_class"

    @classmethod
    def non_public_class_method(cls):
        """This is a non-public class method that should NOT be validated."""
        return "non_public_class"

    @property
    @public
    def public_property(self):
        """This is a public property that should be validated."""
        return "public_property"

    @property
    def non_public_property(self):
        """This is a non-public property that should NOT be validated."""
        return "non_public_property"


class NonPublicClass:
    """A non-public class - none of its methods should be validated even if marked @public."""

    @public
    def public_method_on_non_public_class(self):
        """This should NOT be validated because the class is not @public."""
        return "should_not_validate"

    def regular_method_on_non_public_class(self):
        """This should NOT be validated."""
        return "should_not_validate"


@public
class AnotherPublicClass:
    """Another public class to test multiple classes."""

    @public
    def another_public_method(self):
        """Another public method that should be validated."""
        return "another_public"

    def another_non_public_method(self):
        """Another non-public method that should NOT be validated."""
        return "another_non_public"

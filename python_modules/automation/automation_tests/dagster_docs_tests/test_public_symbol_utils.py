"""Tests for public symbol utility functions."""

from automation.dagster_docs.public_symbol_utils import (
    get_public_methods_from_class,
    is_valid_public_method,
)
from dagster._annotations import public


class TestIsValidPublicMethod:
    """Test the is_valid_public_method function."""

    def test_regular_method_with_public_annotation(self):
        """Test that a regular method with @public annotation is detected correctly."""

        @public
        def mock_method():
            """A mock method."""
            pass

        is_valid, target = is_valid_public_method(mock_method)

        assert is_valid is True
        assert target is mock_method

    def test_regular_method_without_public_annotation(self):
        """Test that a regular method without @public annotation is not detected."""

        def mock_method():
            """A mock method."""
            pass

        is_valid, target = is_valid_public_method(mock_method)

        assert is_valid is False
        assert target is mock_method

    def test_property_with_public_annotation(self):
        """Test that a property with @public annotation is detected correctly."""

        @public
        @property
        def mock_property(self):
            """A mock property."""
            return "value"

        is_valid, target = is_valid_public_method(mock_property)

        assert is_valid is True
        assert target is mock_property.fget

    def test_property_without_public_annotation(self):
        """Test that a property without @public annotation is not detected."""

        @property
        def mock_property(self):
            """A mock property."""
            return "value"

        is_valid, target = is_valid_public_method(mock_property)

        assert is_valid is False
        assert target is mock_property.fget

    def test_staticmethod_with_public_annotation(self):
        """Test that a staticmethod with @public annotation is detected correctly."""

        @public
        @staticmethod
        def mock_staticmethod():
            """A mock static method."""
            pass

        is_valid, target = is_valid_public_method(mock_staticmethod)

        assert is_valid is True
        assert target is mock_staticmethod

    def test_staticmethod_without_public_annotation(self):
        """Test that a staticmethod without @public annotation is not detected."""

        @staticmethod
        def mock_staticmethod():
            """A mock static method."""
            pass

        is_valid, target = is_valid_public_method(mock_staticmethod)

        assert is_valid is False
        assert target is mock_staticmethod

    def test_classmethod_with_public_annotation(self):
        """Test that a classmethod with @public annotation is detected correctly."""

        @public
        @classmethod
        def mock_classmethod(cls):
            """A mock class method."""
            pass

        is_valid, target = is_valid_public_method(mock_classmethod)

        assert is_valid is True
        assert target is mock_classmethod

    def test_classmethod_without_public_annotation(self):
        """Test that a classmethod without @public annotation is not detected."""

        @classmethod
        def mock_classmethod(cls):
            """A mock class method."""
            pass

        is_valid, target = is_valid_public_method(mock_classmethod)

        assert is_valid is False
        assert target is mock_classmethod

    def test_non_callable_object(self):
        """Test that non-callable objects are not considered valid methods."""
        mock_object = "not_a_method"

        is_valid, target = is_valid_public_method(mock_object)

        assert is_valid is False
        assert target is mock_object

    def test_bound_method_with_public_annotation(self):
        """Test that bound methods with @public annotation are detected correctly."""

        class MockClass:
            @public
            def method(self):
                """A mock method."""
                pass

        instance = MockClass()
        bound_method = instance.method

        is_valid, target = is_valid_public_method(bound_method)

        assert is_valid is True
        assert target is bound_method

    def test_bound_method_without_public_annotation(self):
        """Test that bound methods without @public annotation are not detected."""

        class MockClass:
            def method(self):
                """A mock method."""
                pass

        instance = MockClass()
        bound_method = instance.method

        is_valid, target = is_valid_public_method(bound_method)

        assert is_valid is False
        assert target is bound_method


class TestGetPublicMethodsFromClass:
    """Test the get_public_methods_from_class function."""

    def test_class_with_public_methods(self):
        """Test extracting @public methods from a class."""

        class MockClass:
            @public
            def public_method(self):
                """A public method."""
                pass

            def private_method(self):
                """A private method."""
                pass

            @public
            @property
            def public_property(self):
                """A public property."""
                return "value"

            @public
            @staticmethod
            def public_static():
                """A public static method."""
                pass

            @public
            @classmethod
            def public_class_method(cls):
                """A public class method."""
                pass

            def _internal_method(self):
                """An internal method (starts with underscore)."""
                pass

        methods = get_public_methods_from_class(MockClass, "test.MockClass")

        expected_methods = [
            "test.MockClass.public_method",
            "test.MockClass.public_property",
            "test.MockClass.public_static",
            "test.MockClass.public_class_method",
        ]

        assert sorted(methods) == sorted(expected_methods)

    def test_class_with_no_public_methods(self):
        """Test a class with no @public methods."""

        class MockClass:
            def private_method(self):
                """A private method."""
                pass

            def _internal_method(self):
                """An internal method."""
                pass

            @property
            def non_public_property(self):
                """A non-public property."""
                return "value"

        methods = get_public_methods_from_class(MockClass, "test.MockClass")

        assert methods == []

    def test_class_with_attribute_access_errors(self):
        """Test that the function handles attribute access errors gracefully."""

        class MockClass:
            @public
            def good_method(self):
                """A good method."""
                pass

        # Simulate an attribute that causes an exception when accessed
        # We'll temporarily add a problematic attribute
        def problematic_attr(self):
            raise RuntimeError("Cannot access this attribute")

        MockClass.problematic_attr = property(problematic_attr)  # type: ignore[misc]

        try:
            methods = get_public_methods_from_class(MockClass, "test.MockClass")

            # Should still return the good method and not crash
            assert methods == ["test.MockClass.good_method"]
        finally:
            # Clean up
            delattr(MockClass, "problematic_attr")

    def test_empty_class(self):
        """Test an empty class with no methods."""

        class EmptyClass:
            pass

        methods = get_public_methods_from_class(EmptyClass, "test.EmptyClass")

        assert methods == []

    def test_class_with_inherited_methods(self):
        """Test that inherited methods are included in the results."""

        class BaseClass:
            @public
            def base_method(self):
                """A base method."""
                pass

        class DerivedClass(BaseClass):
            @public
            def derived_method(self):
                """A derived method."""
                pass

        methods = get_public_methods_from_class(DerivedClass, "test.DerivedClass")

        expected_methods = ["test.DerivedClass.base_method", "test.DerivedClass.derived_method"]

        assert sorted(methods) == sorted(expected_methods)

    def test_class_with_mixed_method_types(self):
        """Test a class with various types of methods, some public, some not."""

        class MixedClass:
            @public
            def public_instance_method(self):
                """A public instance method."""
                pass

            def private_instance_method(self):
                """A private instance method."""
                pass

            @public
            @staticmethod
            def public_static_method():
                """A public static method."""
                pass

            @staticmethod
            def private_static_method():
                """A private static method."""
                pass

            @public
            @classmethod
            def public_class_method(cls):
                """A public class method."""
                pass

            @classmethod
            def private_class_method(cls):
                """A private class method."""
                pass

            @public
            @property
            def public_property(self):
                """A public property."""
                return "value"

            @property
            def private_property(self):
                """A private property."""
                return "value"

        methods = get_public_methods_from_class(MixedClass, "test.MixedClass")

        expected_methods = [
            "test.MixedClass.public_instance_method",
            "test.MixedClass.public_static_method",
            "test.MixedClass.public_class_method",
            "test.MixedClass.public_property",
        ]

        assert sorted(methods) == sorted(expected_methods)

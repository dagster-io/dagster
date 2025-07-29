"""Tests for validating @public methods on @public classes."""

import pytest
from automation.dagster_docs.validator import SymbolImporter


class TestPublicMethodFiltering:
    """Test that only @public methods on @public classes are identified for validation."""

    def test_identifies_only_public_methods_on_public_classes(self):
        """Test that only @public methods on @public classes are found for validation.

        This is the core test that verifies the main functionality:
        - @public methods on @public classes should be included
        - Non-public methods on @public classes should be excluded
        - All methods on non-public classes should be excluded (even if marked @public)
        - Different method types (instance, static, class, property) should all work
        """
        # Import our test module
        module_path = "automation_tests.dagster_docs_tests.test_fixtures.test_public_class"

        methods = SymbolImporter.get_all_public_annotated_methods(module_path)

        # Extract just the method names from the full dotted paths for easier testing
        method_names = [method.dotted_path.split(".")[-1] for method in methods]

        # Methods that SHOULD be found (public methods on public classes)
        expected_public_methods = {
            "public_instance_method",
            "public_static_method",
            "public_class_method",
            "public_property",
            "another_public_method",  # From AnotherPublicClass
        }

        # Methods that should NOT be found
        excluded_methods = {
            # Non-public methods on public classes
            "non_public_instance_method",
            "non_public_static_method",
            "non_public_class_method",
            "non_public_property",
            "another_non_public_method",
            # Any methods from NonPublicClass (even if marked @public)
            "public_method_on_non_public_class",
            "regular_method_on_non_public_class",
        }

        # Verify that all expected public methods are found
        for expected_method in expected_public_methods:
            assert expected_method in method_names, (
                f"Expected @public method '{expected_method}' was not found"
            )

        # Verify that excluded methods are NOT found
        for excluded_method in excluded_methods:
            assert excluded_method not in method_names, (
                f"Non-public method '{excluded_method}' should not be found"
            )

        # Verify the total count matches expectations
        assert len(methods) == len(expected_public_methods), (
            f"Expected {len(expected_public_methods)} public methods, but found {len(methods)}. "
            f"Found methods: {method_names}"
        )

    def test_method_types_are_correctly_handled(self):
        """Test that different method types (instance, static, class, property) are all handled correctly."""
        module_path = "automation_tests.dagster_docs_tests.test_fixtures.test_public_class"

        methods = SymbolImporter.get_all_public_annotated_methods(module_path)

        # Create a mapping of method names to their SymbolInfo objects
        methods_by_name = {method.dotted_path.split(".")[-1]: method for method in methods}

        # Verify we have the expected method types
        assert "public_instance_method" in methods_by_name
        assert "public_static_method" in methods_by_name
        assert "public_class_method" in methods_by_name
        assert "public_property" in methods_by_name

        # Verify each method has the correct symbol type and docstring
        instance_method = methods_by_name["public_instance_method"]
        assert instance_method.docstring is not None
        assert "public instance method" in instance_method.docstring

        static_method = methods_by_name["public_static_method"]
        assert static_method.docstring is not None
        assert "public static method" in static_method.docstring

        class_method = methods_by_name["public_class_method"]
        assert class_method.docstring is not None
        assert "public class method" in class_method.docstring

        property_method = methods_by_name["public_property"]
        assert property_method.docstring is not None
        assert "public property" in property_method.docstring

    def test_multiple_public_classes_are_handled(self):
        """Test that methods from multiple @public classes in the same module are found."""
        module_path = "automation_tests.dagster_docs_tests.test_fixtures.test_public_class"

        methods = SymbolImporter.get_all_public_annotated_methods(module_path)

        # Extract class names from the dotted paths
        class_names = set()
        for method in methods:
            parts = method.dotted_path.split(".")
            if len(parts) >= 2:
                class_names.add(parts[-2])  # Second to last part is class name

        # Should find methods from both public classes
        expected_classes = {"PublicClass", "AnotherPublicClass"}
        assert expected_classes.issubset(class_names), (
            f"Expected to find methods from classes {expected_classes}, "
            f"but only found classes {class_names}"
        )

        # Should NOT find any methods from NonPublicClass
        assert "NonPublicClass" not in class_names, (
            "Should not find any methods from NonPublicClass"
        )

    def test_nonexistent_module_raises_import_error(self):
        """Test that trying to analyze a nonexistent module raises ModuleNotFoundError."""
        with pytest.raises(ModuleNotFoundError, match="No module named"):
            SymbolImporter.get_all_public_annotated_methods(
                "nonexistent.module.that.does.not.exist"
            )

    def test_empty_module_returns_empty_list(self):
        """Test that a module with no @public classes returns an empty list."""
        # Use a standard library module that shouldn't have @public decorators
        try:
            methods = SymbolImporter.get_all_public_annotated_methods("json")
            assert isinstance(methods, list)
            # Should be empty since standard library modules don't use @public decorators
            assert len(methods) == 0
        except ImportError:
            pytest.skip("json module not available for testing")

    def test_dotted_paths_are_correctly_formed(self):
        """Test that the dotted paths in SymbolInfo objects are correctly formed."""
        module_path = "automation_tests.dagster_docs_tests.test_fixtures.test_public_class"

        methods = SymbolImporter.get_all_public_annotated_methods(module_path)

        for method in methods:
            # Each dotted path should have the format: module.class.method
            parts = method.dotted_path.split(".")
            assert len(parts) >= 3, (
                f"Dotted path '{method.dotted_path}' should have at least 3 parts"
            )

            # Module part should match what we requested
            module_part = ".".join(parts[:-2])  # All but last 2 parts
            assert module_part == module_path

            # Class part should be one of our public classes
            class_part = parts[-2]
            assert class_part in {"PublicClass", "AnotherPublicClass"}

            # Method part should be one of our expected public methods
            method_part = parts[-1]
            expected_methods = {
                "public_instance_method",
                "public_static_method",
                "public_class_method",
                "public_property",
                "another_public_method",
            }
            assert method_part in expected_methods

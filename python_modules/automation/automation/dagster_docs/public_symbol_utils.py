"""Utilities for working with @public-annotated symbols in the Dagster codebase."""

import inspect
from typing import Any, Optional

from dagster._annotations import is_public


def is_valid_public_method(method: Any) -> tuple[bool, Optional[Any]]:
    """Check if a method is valid and @public-annotated.

    This function handles the different types of methods (properties, static methods,
    class methods, and regular methods) and determines if they have the @public
    annotation from dagster._annotations.

    Args:
        method: The method object to check

    Returns:
        A tuple of (is_valid_and_public, target_for_public_check) where:
        - is_valid_and_public: True if the method is valid and has @public annotation
        - target_for_public_check: The object that was checked for @public annotation
    """
    is_valid_method = False
    target_for_public_check = method

    if isinstance(method, property):
        # For properties, check the @public decorator on the getter function
        is_valid_method = True
        target_for_public_check = method.fget
    elif isinstance(method, (staticmethod, classmethod)):
        # For static/class methods, check the decorator on the underlying function
        is_valid_method = True
        target_for_public_check = method
    elif callable(method) and (inspect.ismethod(method) or inspect.isfunction(method)):
        # For regular instance methods and functions
        is_valid_method = True
        target_for_public_check = method

    # Only return True if the method is valid and has @public annotation
    if is_valid_method and is_public(target_for_public_check):
        return True, target_for_public_check

    return False, target_for_public_check


def get_public_methods_from_class(cls: Any, class_dotted_path: str) -> list[str]:
    """Get all @public-annotated methods from a class.

    Args:
        cls: The class object to inspect
        class_dotted_path: The dotted path to the class (e.g., 'dagster.AssetExecutionContext')

    Returns:
        List of dotted paths to @public methods (e.g., ['dagster.AssetExecutionContext.log'])
    """
    methods = []

    for method_name in dir(cls):
        if not method_name.startswith("_"):
            method = getattr(cls, method_name)
            is_valid_and_public, _ = is_valid_public_method(method)

            if is_valid_and_public:
                full_path = f"{class_dotted_path}.{method_name}"
                methods.append(full_path)

    return methods

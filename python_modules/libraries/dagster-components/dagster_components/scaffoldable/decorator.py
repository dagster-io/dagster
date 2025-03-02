from typing import Callable, TypeVar

from dagster import _check as check

from dagster_components.scaffoldable.scaffolder import ComponentScaffolder

# Type variable for generic class handling
T = TypeVar("T")

# Constant for scaffolder attribute name
SCAFFOLDER_ATTRIBUTE = "__scaffolder_class__"


def scaffoldable(scaffolder: type[ComponentScaffolder]) -> Callable[[type[T]], type[T]]:
    """A decorator that attaches a scaffolder class to the decorated class.

    Args:
        scaffolder: A class that inherits from Scaffoldable

    Returns:
        Decorator function that enhances the target class
    """

    def decorator(cls: type[T]) -> type[T]:
        # Store the scaffolder class as an attribute using the constant
        setattr(cls, SCAFFOLDER_ATTRIBUTE, scaffolder)
        return cls

    return decorator


def is_scaffoldable_class(cls: type) -> bool:
    """Determines if a class has been decorated with scaffoldable.

    Args:
        cls: The class to check

    Returns:
        True if the class has a scaffolder attached, False otherwise
    """
    return hasattr(cls, SCAFFOLDER_ATTRIBUTE)


def get_scaffolder(cls: type) -> type[ComponentScaffolder]:
    """Retrieves the scaffolder class attached to the decorated class.

    Args:
        cls: The class to inspect

    Returns:
        The scaffolder class attached to the decorated class. Raises CheckError if the class is not decorated with @scaffoldable.
    """
    check.param_invariant(
        is_scaffoldable_class(cls), "cls", "Class must be decorated with @scaffoldable"
    )
    return getattr(cls, SCAFFOLDER_ATTRIBUTE)

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

from dagster import _check as check
from dagster._record import record
from pydantic import BaseModel

# Type variable for generic class handling
T = TypeVar("T")

# Constant for scaffolder attribute name
BLUEPRINT_ATTRIBUTE = "__blueprint__"


def blueprint(
    blueprint_cls: Union[type["Blueprint"], "BlueprintUnavailableReason"],
) -> Callable[[type[T]], type[T]]:
    """A decorator that attaches a scaffolder class to the decorated class.

    Args:
        scaffolder: A class that inherits from Scaffoldable

    Returns:
        Decorator function that enhances the target class
    """

    def decorator(cls: type[T]) -> type[T]:
        # Store the scaffolder class as an attribute using the constant
        setattr(cls, BLUEPRINT_ATTRIBUTE, blueprint_cls)
        return cls

    return decorator


def has_blueprint(cls: type) -> bool:
    """Determines if a class has been decorated with scaffoldable.

    Args:
        cls: The class to check

    Returns:
        True if the class has a scaffolder attached, False otherwise
    """
    return hasattr(cls, BLUEPRINT_ATTRIBUTE)


def get_blueprint(
    cls: type,
) -> Union["Blueprint", "BlueprintUnavailableReason"]:
    """Retrieves the scaffolder class attached to the decorated class.

    Args:
        cls: The class to inspect

    Returns:
        The scaffolder class attached to the decorated class. Raises CheckError if the class is not decorated with @scaffoldable.
    """
    check.param_invariant(has_blueprint(cls), "cls", "Class must be decorated with @scaffoldable")
    attr = getattr(cls, BLUEPRINT_ATTRIBUTE)
    return attr if isinstance(attr, BlueprintUnavailableReason) else attr()


@dataclass
class BlueprintUnavailableReason:
    message: str


@record
class ScaffoldRequest:
    # fully qualified class name of the scaffolded class
    type_name: str
    # target path for the scaffold request. Typically used to construct absolute paths
    target_path: Path


class Blueprint:
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return None

    @abstractmethod
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None: ...

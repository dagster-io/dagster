from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

from dagster import _check as check
from dagster._record import record
from pydantic import BaseModel

# Type variable for generic class handling
T = TypeVar("T")

# Constant for object attribute name
SCAFFOLDER_CLS_ATTRIBUTE = "__scaffolder_cls__"


def scaffold_with(
    scaffolder_cls: Union[type["Scaffolder"], "ScaffolderUnavailableReason"],
) -> Callable[[type[T]], type[T]]:
    """A decorator that declares what scaffolder is used to scaffold the artifact.

    Args:
        scaffolder_cls: A class that inherits from Scaffolder

    Returns:
        Decorator function that enhances the target class
    """

    def decorator(cls: type[T]) -> type[T]:
        # Store the scaffolder class as an attribute using the constant
        setattr(cls, SCAFFOLDER_CLS_ATTRIBUTE, scaffolder_cls)
        return cls

    return decorator


def has_scaffolder(cls: type) -> bool:
    """Determines if a class has been decorated with `@scaffold_with`.

    Args:
        cls: The class to check

    Returns:
        True if the class has a Scaffolder attached, False otherwise
    """
    return hasattr(cls, SCAFFOLDER_CLS_ATTRIBUTE)


def get_scaffolder(
    cls: type,
) -> Union["Scaffolder", "ScaffolderUnavailableReason"]:
    """Retrieves the scaffolder class attached to the decorated class.

    Args:
        cls: The class to inspect

    Returns:
        The scaffolder class attached to the decorated class. Raises CheckError if the class is not decorated with @scaffold_with.
    """
    check.param_invariant(has_scaffolder(cls), "cls", "Class must be decorated with @scaffold_with")
    attr = getattr(cls, SCAFFOLDER_CLS_ATTRIBUTE)
    return attr if isinstance(attr, ScaffolderUnavailableReason) else attr()


@dataclass
class ScaffolderUnavailableReason:
    message: str


@record
class ScaffoldRequest:
    # fully qualified class name of the decorated class
    type_name: str
    # target path for the scaffold request. Typically used to construct absolute paths
    target_path: Path


class Scaffolder:
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return None

    @abstractmethod
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None: ...

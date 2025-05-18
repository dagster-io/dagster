from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Generic, Literal, Optional, Union

from pydantic import BaseModel
from typing_extensions import TypeAlias, TypeVar

from dagster import _check as check
from dagster._annotations import preview, public

# Constant for object attribute name
SCAFFOLDER_CLS_ATTRIBUTE: str = "__scaffolder_cls__"


class NoParams(BaseModel): ...


# Type variable for generic class handling
T = TypeVar("T")
TModel = TypeVar("TModel", bound=BaseModel, default=NoParams)


@public
@preview(emit_runtime_warning=False)
def scaffold_with(
    scaffolder_cls: Union[type["Scaffolder[Any]"], "ScaffolderUnavailableReason"],
) -> Callable[[T], T]:
    """A decorator that declares what Scaffolder is used to scaffold the artifact.

    Args:
        scaffolder_cls: A class that inherits from Scaffolder

    Returns:
        Decorator function that enhances the target class
    """
    from dagster.components.core.package_entry import PACKAGE_ENTRY_ATTR

    def decorator(obj: T) -> T:
        # Store the scaffolder class as an attribute using the constant
        setattr(obj, SCAFFOLDER_CLS_ATTRIBUTE, scaffolder_cls)
        # All scaffoldable objects are library objects
        setattr(obj, PACKAGE_ENTRY_ATTR, True)
        return obj

    return decorator


def has_scaffolder(obj: object) -> bool:
    """Determines if an object has been decorated with `@scaffold_with`.

    Args:
        obj: The object to check

    Returns:
        True if the object has a Scaffolder attached, False otherwise
    """
    return hasattr(obj, SCAFFOLDER_CLS_ATTRIBUTE)


def get_scaffolder(obj: object) -> Union["Scaffolder[Any]", "ScaffolderUnavailableReason"]:
    """Retrieves the scaffolder class attached to the decorated object.

    Args:
        obj: The object to inspect

    Returns:
        The scaffolder class attached to the decorated object. Raises CheckError if the object is not decorated with @scaffold_with.
    """
    check.param_invariant(
        has_scaffolder(obj), "obj", "Object must be decorated with @scaffold_with"
    )
    attr = getattr(obj, SCAFFOLDER_CLS_ATTRIBUTE)
    return attr if isinstance(attr, ScaffolderUnavailableReason) else attr()


@dataclass
class ScaffolderUnavailableReason:
    message: str


ScaffoldFormatOptions: TypeAlias = Literal["yaml", "python"]


@public
@preview(emit_runtime_warning=False)
@dataclass
class ScaffoldRequest(Generic[TModel]):
    """The details about the current scaffolding operation."""

    # fully qualified class name of the decorated object
    type_name: str
    # target path for the scaffold request. Typically used to construct absolute paths
    target_path: Path
    # yaml or python
    scaffold_format: ScaffoldFormatOptions
    # the root of the dg project
    project_root: Optional[Path]
    # optional params for scaffolding
    params: TModel


@public
@preview(emit_runtime_warning=False)
class Scaffolder(Generic[TModel]):
    """Handles scaffolding its associated scaffold target."""

    @classmethod
    def get_scaffold_params(cls) -> type[TModel]:
        return NoParams  # type: ignore

    @abstractmethod
    def scaffold(self, request: ScaffoldRequest[TModel]) -> None:
        """Scaffold the target with the given request.

        Args:
            request: The scaffold request containing type name, target path, format, project root and params
        """
        ...

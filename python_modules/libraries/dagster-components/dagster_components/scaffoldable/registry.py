from typing import Any, Callable, Final, TypeVar, Union

from dagster import _check as check
from dagster._record import record

from dagster_components.scaffoldable.scaffolder import Scaffolder, ScaffolderUnavailableReason

# Type variable for generic class handling
T = TypeVar("T")


@record
class ScaffolderRegistry:
    scaffolders: dict[str, Union[type["Scaffolder"], "ScaffolderUnavailableReason"]]

    def register(
        self,
        obj: Any,
        scaffolder: Union[type["Scaffolder"], "ScaffolderUnavailableReason"],
    ) -> None:
        self.scaffolders[obj.__name__] = scaffolder

    def has(self, obj: Any) -> bool:
        return obj.__name__ in self.scaffolders

    def get(self, obj: Any) -> Union["Scaffolder", "ScaffolderUnavailableReason"]:
        value = self.scaffolders[obj.__name__]
        return value if isinstance(value, ScaffolderUnavailableReason) else value()

    @staticmethod
    def create() -> "ScaffolderRegistry":
        return ScaffolderRegistry(scaffolders={})


_SCAFFOLDER_REGISTRY: Final[ScaffolderRegistry] = ScaffolderRegistry.create()


def _make_scaffoldable(
    obj: Any,
    scaffolder: Union[type["Scaffolder"], "ScaffolderUnavailableReason"],
    registry: ScaffolderRegistry,
) -> None:
    registry.register(obj, scaffolder)


def make_scaffoldable(
    obj: Any,
    scaffolder: Union[type["Scaffolder"], "ScaffolderUnavailableReason"],
) -> None:
    _make_scaffoldable(obj, scaffolder, _SCAFFOLDER_REGISTRY)


def _scaffoldable(
    scaffolder: Union[type["Scaffolder"], "ScaffolderUnavailableReason"],
    registry: ScaffolderRegistry,
) -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        _make_scaffoldable(cls, scaffolder, registry)
        return cls

    return decorator


def scaffoldable(
    scaffolder: Union[type["Scaffolder"], "ScaffolderUnavailableReason"],
) -> Callable[[type[T]], type[T]]:
    """A decorator that attaches a scaffolder class to the decorated class.

    Args:
        scaffolder: A class that inherits from Scaffoldable

    Returns:
        Decorator function that enhances the target class
    """
    return _scaffoldable(scaffolder, _SCAFFOLDER_REGISTRY)


def is_scaffoldable(obj: Any) -> bool:
    """Determines if an object has been made scaffoldable.

    Args:
        obj: The object to check

    Returns:
        True if the object has a scaffolder attached, False otherwise
    """
    return _SCAFFOLDER_REGISTRY.has(obj)


def get_scaffolder(
    obj: Any,
) -> Union["Scaffolder", "ScaffolderUnavailableReason"]:
    """Retrieves the scaffolder class attached to the decorated class.

    Args:
        cls: The class to inspect

    Returns:
        The scaffolder class attached to the decorated class. Raises CheckError if the class is not decorated with @scaffoldable.
    """
    check.param_invariant(is_scaffoldable(obj), "cls", "Class must be decorated with @scaffoldable")
    return _SCAFFOLDER_REGISTRY.get(obj)

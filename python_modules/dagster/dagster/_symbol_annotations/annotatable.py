import inspect
from typing import Any, Optional, TypeVar

from dagster_shared import check
from typing_extensions import TypeAlias

# For the time being, `Annotatable` is set to `Any` even though it should be set to `Decoratable` to
# avoid choking the type checker. Choking happens because of a niche scenario where
# `ResourceDefinition`, which is part of `Decoratable`, is used as an argument to a function that
# accepts `Annotatable`. There is a certain circularity here that current versions of pyright fail
# on. It will likely be resolved by future versions of pyright, and then `Annotatable` should be set
# to `Decoratable`.
Annotatable: TypeAlias = Any

T_Annotatable = TypeVar("T_Annotatable", bound=Annotatable)


def _get_annotation_target(obj: Annotatable) -> object:
    """Given an object to be annotated, return the underlying object that will actually store the annotations.
    This is necessary because not all objects are mutable, and so can't be annotated directly.
    """
    if isinstance(obj, property):
        return obj.fget
    elif isinstance(obj, (staticmethod, classmethod)):
        return obj.__func__
    else:
        return obj


def _get_subject(obj: Annotatable, param: Optional[str] = None) -> str:
    from dagster._core.decorator_utils import is_resource_def

    """Get the string representation of an annotated object that will appear in
    annotation-generated warnings about the object.
    """
    if param:
        if isinstance(obj, type):
            return f"Parameter `{param}` of initializer `{obj.__qualname__}.__init__`"
        else:
            fn_subject = _get_subject(obj)
            return f"Parameter `{param}` of {fn_subject[:1].lower() + fn_subject[1:]}"
    else:
        if isinstance(obj, type):
            return f"Class `{obj.__qualname__}`"
        elif isinstance(obj, property):
            return f"Property `{obj.fget.__qualname__ if obj.fget else obj}`"
        # classmethod and staticmethod don't themselves get a `__qualname__` attr until Python 3.10.
        elif isinstance(obj, classmethod):
            return f"Class method `{_get_annotation_target(obj).__qualname__}`"
        elif isinstance(obj, staticmethod):
            return f"Static method `{_get_annotation_target(obj).__qualname__}`"
        elif inspect.isfunction(obj):
            return f"Function `{obj.__qualname__}`"
        elif is_resource_def(obj):
            return f"Dagster resource `{obj.__qualname__}`"
        else:
            check.failed(f"Unexpected object type: {type(obj)}")


def copy_annotations(dest: Annotatable, src: Annotatable) -> None:
    """Copy all Dagster annotations from one object to another object."""
    dest_target = _get_annotation_target(dest)
    src_target = _get_annotation_target(src)

    # Copy all known annotation attributes
    annotation_attrs = [
        "_is_public",
        "_deprecated",
        "_deprecated_params",
        "_superseded",
        "_preview",
        "_beta",
        "_beta_params",
    ]

    for attr_name in annotation_attrs:
        if hasattr(src_target, attr_name):
            setattr(dest_target, attr_name, getattr(src_target, attr_name))

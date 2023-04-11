from typing import TYPE_CHECKING, Any, Generic, Optional, Type, TypeVar, Union, cast

import pydantic
from pydantic import Field
from typing_extensions import dataclass_transform, get_origin

from .utils import safe_is_subclass

if TYPE_CHECKING:
    from dagster._config.pythonic_config import PartialResource


# Since a metaclass is invoked by Resource before Resource or PartialResource is defined, we need to
# define a temporary class to use as a placeholder for use in the initial metaclass invocation.
#
# These initial invocations will use the placeholder values, which is fine, since there's no
# attributes on the Resource class which would be affected. The only time the metaclass will
# actually change the type annotations is when it's invoked for a user-created subclass of Resource,
# at which point the placeholder values will be replaced with the actual types.
class LateBoundTypesForResourceTypeChecking:
    _TResValue = TypeVar("_TResValue")

    class _Temp(Generic[_TResValue]):
        pass

    _ResourceDep: Type = _Temp
    _Resource: Type = _Temp
    _PartialResource: Type = _Temp

    @staticmethod
    def get_resource_rep_type() -> Type:
        return LateBoundTypesForResourceTypeChecking._ResourceDep  # noqa: SLF001

    @staticmethod
    def get_resource_type() -> Type:
        return LateBoundTypesForResourceTypeChecking._Resource  # noqa: SLF001

    @staticmethod
    def get_partial_resource_type(base: Type) -> Type:
        return LateBoundTypesForResourceTypeChecking._PartialResource[base]  # noqa: SLF001

    @staticmethod
    def set_actual_types_for_type_checking(
        resource_dep_type: Type, resource_type: Type, partial_resource_type: Type
    ) -> None:
        LateBoundTypesForResourceTypeChecking._ResourceDep = resource_dep_type  # noqa: SLF001
        LateBoundTypesForResourceTypeChecking._Resource = resource_type  # noqa: SLF001
        LateBoundTypesForResourceTypeChecking._PartialResource = (  # noqa: SLF001
            partial_resource_type
        )


@dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
class BaseResourceMeta(pydantic.main.ModelMetaclass):
    """Custom metaclass for Resource and PartialResource. This metaclass is responsible for
    transforming the type annotations on the class so that Pydantic constructor-time validation
    does not error when users provide partially configured resources to resource params.

    For example, the following code would ordinarily fail Pydantic validation:

    .. code-block:: python

        class FooResource(ConfigurableResource):
            bar: BarResource

        # Types as PartialResource[BarResource]
        partial_bar = BarResource.configure_at_runtime()

        # Pydantic validation fails because bar is not a BarResource
        foo = FooResource(bar=partial_bar)

    This metaclass transforms the type annotations on the class so that Pydantic validation
    accepts either a PartialResource or a Resource as a value for the resource dependency.
    """

    def __new__(cls, name, bases, namespaces, **kwargs) -> Any:
        # Gather all type annotations from the class and its base classes
        annotations = namespaces.get("__annotations__", {})
        for field in annotations:
            if not field.startswith("__"):
                # Check if the annotation is a ResourceDependency
                if (
                    get_origin(annotations[field])
                    == LateBoundTypesForResourceTypeChecking.get_resource_rep_type()
                ):
                    # arg = get_args(annotations[field])[0]
                    # If so, we treat it as a Union of a PartialResource and a Resource
                    # for Pydantic's sake.
                    annotations[field] = Any
                elif safe_is_subclass(
                    annotations[field], LateBoundTypesForResourceTypeChecking.get_resource_type()
                ):
                    # If the annotation is a Resource, we treat it as a Union of a PartialResource
                    # and a Resource for Pydantic's sake, so that a user can pass in a partially
                    # configured resource.
                    base = annotations[field]
                    annotations[field] = Union[
                        LateBoundTypesForResourceTypeChecking.get_partial_resource_type(base), base
                    ]

        namespaces["__annotations__"] = annotations
        return super().__new__(cls, name, bases, namespaces, **kwargs)


Self = TypeVar("Self", bound="TypecheckAllowPartialResourceInitParams")


class TypecheckAllowPartialResourceInitParams:
    """Implementation of the Python descriptor protocol (https://docs.python.org/3/howto/descriptor.html)
    to adjust the types of resource inputs and outputs, e.g. resource dependencies can be passed in
    as PartialResources or Resources, but will always be returned as Resources.

    For example, given a resource with the following signature:

    .. code-block:: python

        class FooResource(Resource):
            bar: BarResource

    The following code will work:

    .. code-block:: python

        # Types as PartialResource[BarResource]
        partial_bar = BarResource.configure_at_runtime()

        # bar parameter takes BarResource | PartialResource[BarResource]
        foo = FooResource(bar=partial_bar)

        # initialization of FooResource succeeds,
        # populating the bar attribute with a full BarResource

        # bar attribute is typed as BarResource, since
        # it is fully initialized when a user accesses it
        print(foo.bar)

    Very similar to https://github.com/pydantic/pydantic/discussions/4262.
    """

    def __set_name__(self, _owner, name):
        self._assigned_name = name

    def __get__(self: "Self", obj: Any, __owner: Any) -> "Self":
        # no-op implementation (only used to affect type signature)
        return cast(Self, getattr(obj, self._assigned_name))

    def __set__(
        self: "Self", obj: Optional[object], value: Union["Self", "PartialResource[Self]"]
    ) -> None:
        # no-op implementation (only used to affect type signature)
        setattr(obj, self._assigned_name, value)

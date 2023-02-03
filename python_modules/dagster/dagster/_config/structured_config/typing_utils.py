from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union, cast

if TYPE_CHECKING:
    from dagster._config.structured_config import PartialResource

Self = TypeVar("Self", bound="AllowPartialResourceInitParams")


class AllowPartialResourceInitParams:
    """
    Implementation of the Python descriptor protocol (https://docs.python.org/3/howto/descriptor.html)
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

        # bar attribute is BarResource
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

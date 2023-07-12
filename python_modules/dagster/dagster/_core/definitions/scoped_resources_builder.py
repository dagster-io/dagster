# NOTE: This file has been factored out from "resource_definition" and type-ignored due to a mypy bug
# when processing dynamically generated namedtuples. This code corrupts the mypy cache and causes
# mypy to fail. When mypy fixes this bug, the type-ignore can be removed and the file contents
# folded back into "resource_definition".
#
# See: https://github.com/python/mypy/issues/7281

from collections import namedtuple
from typing import AbstractSet, Any, Mapping, NamedTuple, Optional

import dagster._check as check
from dagster._core.errors import DagsterUnknownResourceError


class IContainsGenerator:
    """This class adds an additional tag to indicate that the resources object has at least one
    resource that has been yielded from a generator, and thus may require teardown.
    """


class Resources:
    """This class functions as a "tag" that we can use to type the namedtuple returned by
    ScopedResourcesBuilder.build(). The way that we create the namedtuple returned by build() is
    incompatible with type annotations on its own due to its dynamic attributes, so this tag class
    provides a workaround.
    """

    def __getattr__(self, name: str) -> Any:
        raise DagsterUnknownResourceError(name)

    @property
    def _original_resource_dict(self) -> Mapping[str, object]:
        raise NotImplementedError()


class ScopedResourcesBuilder(
    NamedTuple(
        "_ScopedResourcesBuilder",
        [("resource_instance_dict", Mapping[str, object]), ("contains_generator", bool)],
    )
):
    """There are concepts in the codebase (e.g. ops, system storage) that receive
    only the resources that they have specified in required_resource_keys.
    ScopedResourcesBuilder is responsible for dynamically building a class with
    only those required resources and returning an instance of that class.
    """

    def __new__(
        cls,
        resource_instance_dict: Optional[Mapping[str, object]] = None,
        contains_generator: bool = False,
    ):
        return super(ScopedResourcesBuilder, cls).__new__(
            cls,
            resource_instance_dict=check.opt_mapping_param(
                resource_instance_dict, "resource_instance_dict", key_type=str
            ),
            contains_generator=contains_generator,
        )

    def build(self, required_resource_keys: Optional[AbstractSet[str]]) -> Resources:
        from dagster._config.pythonic_config import IAttachDifferentObjectToOpContext

        """We dynamically create a type that has the resource keys as properties, to enable dotting into
        the resources from a context.

        For example, given:

        resources = {'foo': <some resource>, 'bar': <some other resource>}

        then this will create the type Resource(namedtuple('foo bar'))

        and then binds the specified resources into an instance of this object, which can be consumed
        as, e.g., context.resources.foo.
        """
        required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )
        # it is possible that the surrounding context does NOT have the required resource keys
        # because we are building a context for steps that we are not going to execute (e.g. in the
        # resume/retry case, in order to generate copy intermediates events)
        resource_instance_dict = {
            key: self.resource_instance_dict[key]
            for key in required_resource_keys
            if key in self.resource_instance_dict
        }
        resources_to_attach_to_context = {
            k: (
                v.get_object_to_set_on_execution_context()
                if isinstance(v, IAttachDifferentObjectToOpContext)
                else v
            )
            for k, v in resource_instance_dict.items()
        }

        # If any of the resources are generators, add the IContainsGenerator subclass to flag that
        # this is the case.
        if self.contains_generator:

            class _ScopedResourcesContainsGenerator(
                namedtuple(
                    "_ScopedResourcesContainsGenerator",
                    list(resources_to_attach_to_context.keys()),
                ),
                Resources,
                IContainsGenerator,
            ):
                @property
                def _original_resource_dict(self) -> Mapping[str, object]:
                    return resource_instance_dict

            return _ScopedResourcesContainsGenerator(**resources_to_attach_to_context)

        else:

            class _ScopedResources(
                namedtuple("_ScopedResources", list(resources_to_attach_to_context.keys())),
                Resources,
            ):
                @property
                def _original_resource_dict(self) -> Mapping[str, object]:
                    return resource_instance_dict

            return _ScopedResources(**resources_to_attach_to_context)

    @classmethod
    def build_empty(cls) -> Resources:
        """Returns an empty Resources object, equivalent to ScopedResourcesBuilder().build(None)."""
        return cls().build(None)

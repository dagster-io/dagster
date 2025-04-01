from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

from dagster import AssetKey, AssetSpec, AutoMaterializePolicy, AutomationCondition
from dagster._annotations import public, superseded
from dagster._record import record
from dagster._utils.warnings import supersession_warning
from dlt.common.destination import Destination
from dlt.extract.resource import DltResource


@record
class DltResourceTranslatorData:
    resource: DltResource
    destination: Optional[Destination]


@dataclass
class DagsterDltTranslator:
    def get_asset_spec(self, data: DltResourceTranslatorData) -> AssetSpec:
        """Defines the asset spec for a given dlt resource.

        This method can be overridden to provide custom asset key for a dlt resource.

        Args:
            data (DltResourceTranslatorData): The dlt data to pass to the translator,
                including the resource and the destination.

        Returns:
            The :py:class:`dagster.AssetSpec` for the given dlt resource

        """
        return AssetSpec(
            key=self._resolve_back_compat_method(
                "get_asset_key", self._default_asset_key_fn, data.resource
            ),
            automation_condition=self._resolve_back_compat_method(
                "get_automation_condition", self._default_automation_condition_fn, data.resource
            ),
            deps=self._resolve_back_compat_method(
                "get_deps_asset_keys", self._default_deps_fn, data.resource
            ),
            description=self._resolve_back_compat_method(
                "get_description", self._default_description_fn, data.resource
            ),
            group_name=self._resolve_back_compat_method(
                "get_group_name", self._default_group_name_fn, data.resource
            ),
            metadata=self._resolve_back_compat_method(
                "get_metadata", self._default_metadata_fn, data.resource
            ),
            owners=self._resolve_back_compat_method(
                "get_owners", self._default_owners_fn, data.resource
            ),
            tags=self._resolve_back_compat_method("get_tags", self._default_tags_fn, data.resource),
            kinds=self._resolve_back_compat_method(
                "get_kinds", self._default_kinds_fn, data.resource, data.destination
            ),
        )

    def _resolve_back_compat_method(
        self,
        method_name: str,
        default_fn: Union[Callable[[DltResource], Any], Callable[[DltResource, Destination], Any]],
        resource: DltResource,
        destination: Optional[Destination] = None,
    ):
        method = getattr(type(self), method_name)
        base_method = getattr(DagsterDltTranslator, method_name)
        args = (resource,)
        if method_name == "get_kinds":
            args += (destination,)
        if method is not base_method:  # user defined this
            supersession_warning(
                subject=method_name,
                additional_warn_text=(
                    f"Instead of overriding DagsterDltTranslator.{method_name}(), "
                    f"override DagsterDltTranslator.get_asset_spec()."
                ),
            )
            return method(self, *args)
        else:
            return default_fn(*args)  # type: ignore

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).key` instead.",
    )
    @public
    def get_asset_key(self, resource: DltResource) -> AssetKey:
        """Defines asset key for a given dlt resource key and dataset name.

        This method can be overridden to provide custom asset key for a dlt resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            AssetKey of Dagster asset derived from dlt resource

        """
        return self._default_asset_key_fn(resource)

    def _default_asset_key_fn(self, resource: DltResource) -> AssetKey:
        """Defines asset key for a given dlt resource key and dataset name.

        Args:
            resource (DltResource): dlt resource

        Returns:
            AssetKey of Dagster asset derived from dlt resource

        """
        return AssetKey(f"dlt_{resource.source_name}_{resource.name}")

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).auto_materialize_policy` instead.",
    )
    @public
    def get_auto_materialize_policy(self, resource: DltResource) -> Optional[AutoMaterializePolicy]:
        """Defines resource specific auto materialize policy.

        This method can be overridden to provide custom auto materialize policy for a dlt resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[AutoMaterializePolicy]: The auto-materialize policy for a resource

        """
        return self._default_auto_materialize_policy_fn(resource)

    def _default_auto_materialize_policy_fn(
        self, resource: DltResource
    ) -> Optional[AutoMaterializePolicy]:
        """Defines resource specific auto materialize policy.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[AutoMaterializePolicy]: The auto-materialize policy for a resource

        """
        return None

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).automation_condition` instead.",
    )
    @public
    def get_automation_condition(self, resource: DltResource) -> Optional[AutomationCondition]:
        """Defines resource specific automation condition.

        This method can be overridden to provide custom automation condition for a dlt resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[AutomationCondition]: The automation condition for a resource

        """
        return self._default_automation_condition_fn(resource)

    def _default_automation_condition_fn(
        self, resource: DltResource
    ) -> Optional[AutomationCondition]:
        """Defines resource specific automation condition.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[AutomationCondition]: The automation condition for a resource

        """
        auto_materialize_policy = self._default_auto_materialize_policy_fn(resource)
        return (
            auto_materialize_policy.to_automation_condition() if auto_materialize_policy else None
        )

    @superseded(
        additional_warn_text=(
            "Iterate over `DagsterDltTranslator.get_asset_spec(...).deps` to access `AssetDep.asset_key` instead."
        ),
    )
    @public
    def get_deps_asset_keys(self, resource: DltResource) -> Iterable[AssetKey]:
        """Defines upstream asset dependencies given a dlt resource.

        Defaults to a concatenation of `resource.source_name` and `resource.name`.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Iterable[AssetKey]: The Dagster asset keys upstream of `dlt_resource_key`.

        """
        return self._default_deps_fn(resource)

    def _default_deps_fn(self, resource: DltResource) -> Iterable[AssetKey]:
        """Defines upstream asset dependencies given a dlt resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Iterable[AssetKey]: The Dagster asset keys upstream of `dlt_resource_key`.

        """
        if resource.is_transformer:
            pipe = resource._pipe  # noqa: SLF001
            while pipe.has_parent:
                pipe = pipe.parent
            return [AssetKey(f"{resource.source_name}_{pipe.name}")]
        return [AssetKey(f"{resource.source_name}_{resource.name}")]

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).description` instead.",
    )
    @public
    def get_description(self, resource: DltResource) -> Optional[str]:
        """A method that takes in a dlt resource returns the Dagster description of the resource.

        This method can be overridden to provide a custom description for a dlt resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[str]: The Dagster description for the dlt resource.
        """
        return self._default_description_fn(resource)

    def _default_description_fn(self, resource: DltResource) -> Optional[str]:
        """A method that takes in a dlt resource returns the Dagster description of the resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[str]: The Dagster description for the dlt resource.
        """
        pipe = resource._pipe  # noqa: SLF001
        # If the function underlying the resource is a single callable,
        # return the docstring of the callable.
        if len(pipe.steps) == 1 and callable(pipe.steps[0]):
            return pipe.steps[0].__doc__
        return None

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).group_name` instead.",
    )
    @public
    def get_group_name(self, resource: DltResource) -> Optional[str]:
        """A method that takes in a dlt resource and returns the Dagster group name of the resource.

        This method can be overridden to provide a custom group name for a dlt resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[str]: A Dagster group name for the dlt resource.
        """
        return self._default_group_name_fn(resource)

    def _default_group_name_fn(self, resource: DltResource) -> Optional[str]:
        """A method that takes in a dlt resource and returns the Dagster group name of the resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[str]: A Dagster group name for the dlt resource.
        """
        return None

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).metadata` instead.",
    )
    @public
    def get_metadata(self, resource: DltResource) -> Mapping[str, Any]:
        """Defines resource specific metadata.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Mapping[str, Any]: The custom metadata entries for this resource.
        """
        return self._default_metadata_fn(resource)

    def _default_metadata_fn(self, resource: DltResource) -> Mapping[str, Any]:
        """Defines resource specific metadata.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Mapping[str, Any]: The custom metadata entries for this resource.
        """
        return {}

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).owners` instead.",
    )
    @public
    def get_owners(self, resource: DltResource) -> Optional[Sequence[str]]:
        """A method that takes in a dlt resource and returns the Dagster owners of the resource.

        This method can be overridden to provide custom owners for a dlt resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[Sequence[str]]: A sequence of Dagster owners for the dlt resource.
        """
        return self._default_owners_fn(resource)

    def _default_owners_fn(self, resource: DltResource) -> Optional[Sequence[str]]:
        """A method that takes in a dlt resource and returns the Dagster owners of the resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[Sequence[str]]: A sequence of Dagster owners for the dlt resource.
        """
        return None

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).tags` instead.",
    )
    @public
    def get_tags(self, resource: DltResource) -> Mapping[str, str]:
        """A method that takes in a dlt resource and returns the Dagster tags of the structure.

        This method can be overridden to provide custom tags for a dlt resource.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[Mapping[str, str]]: A dictionary representing the Dagster tags for the
                dlt resource.
        """
        return self._default_tags_fn(resource)

    def _default_tags_fn(self, resource: DltResource) -> Mapping[str, str]:
        """A method that takes in a dlt resource and returns the Dagster tags of the structure.

        Args:
            resource (DltResource): dlt resource

        Returns:
            Optional[Mapping[str, str]]: A dictionary representing the Dagster tags for the
                dlt resource.
        """
        return {}

    @superseded(
        additional_warn_text="Use `DagsterDltTranslator.get_asset_spec(...).kinds` instead.",
    )
    @public
    def get_kinds(self, resource: DltResource, destination: Destination) -> set[str]:
        """A method that takes in a dlt resource and returns the kinds which should be
        attached. Defaults to the destination type and "dlt".

        This method can be overridden to provide custom kinds for a dlt resource.

        Args:
            resource (DltResource): dlt resource
            destination (Destination): dlt destination

        Returns:
            Set[str]: The kinds of the asset.
        """
        return self._default_kinds_fn(resource, destination)

    def _default_kinds_fn(
        self, resource: DltResource, destination: Optional[Destination]
    ) -> set[str]:
        """A method that takes in a dlt resource and returns the kinds which should be
        attached. Defaults to the destination type and "dlt".

        Args:
            resource (DltResource): dlt resource
            destination (Optional[Destination]): dlt destination

        Returns:
            Set[str]: The kinds of the asset.
        """
        kinds = {"dlt"}
        destination_set = {destination.destination_name} if destination else set()
        return kinds.union(destination_set)

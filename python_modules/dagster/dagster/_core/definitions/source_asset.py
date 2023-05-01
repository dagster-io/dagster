from __future__ import annotations

import warnings
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    Iterator,
    Mapping,
    Optional,
    cast,
)

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.data_version import DATA_VERSION_TAG, DataVersion
from dagster._core.definitions.events import AssetKey, AssetObservation, CoercibleToAssetKey
from dagster._core.definitions.metadata import (
    ArbitraryMetadataMapping,
    MetadataMapping,
    normalize_metadata,
)
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import (
    ResourceAddable,
    ResourceRequirement,
    SourceAssetIOManagerRequirement,
    ensure_requirements_satisfied,
    get_resource_key_conflicts,
)
from dagster._core.definitions.utils import (
    DEFAULT_GROUP_NAME,
    DEFAULT_IO_MANAGER_KEY,
    validate_group_name,
)
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._utils.backcompat import ExperimentalWarning, experimental_arg_warning
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._core.execution.context.compute import (
        OpExecutionContext,
    )


# Going with this catch-all for the time-being to permit pythonic resources
SourceAssetObserveFunction: TypeAlias = Callable[..., Any]


class SourceAsset(ResourceAddable):
    """A SourceAsset represents an asset that will be loaded by (but not updated by) Dagster.

    Attributes:
        key (Union[AssetKey, Sequence[str], str]): The key of the asset.
        metadata (Mapping[str, MetadataValue]): Metadata associated with the asset.
        io_manager_key (Optional[str]): The key for the IOManager that will be used to load the contents of
            the asset when it's used as an input to other assets inside a job.
        io_manager_def (Optional[IOManagerDefinition]): (Experimental) The definition of the IOManager that will be used to load the contents of
            the asset when it's used as an input to other assets inside a job.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]): (Experimental) resource definitions that may be required by the :py:class:`dagster.IOManagerDefinition` provided in the `io_manager_def` argument.
        description (Optional[str]): The description of the asset.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        observe_fn (Optional[SourceAssetObserveFunction]) Observation function for the source asset.
    """

    key: PublicAttr[AssetKey]
    metadata: PublicAttr[MetadataMapping]
    raw_metadata: PublicAttr[ArbitraryMetadataMapping]
    io_manager_key: PublicAttr[Optional[str]]
    _io_manager_def: PublicAttr[Optional[IOManagerDefinition]]
    description: PublicAttr[Optional[str]]
    partitions_def: PublicAttr[Optional[PartitionsDefinition]]
    group_name: PublicAttr[str]
    resource_defs: PublicAttr[Dict[str, ResourceDefinition]]
    observe_fn: PublicAttr[Optional[SourceAssetObserveFunction]]
    _node_def: Optional[OpDefinition]  # computed lazily

    def __init__(
        self,
        key: CoercibleToAssetKey,
        metadata: Optional[ArbitraryMetadataMapping] = None,
        io_manager_key: Optional[str] = None,
        io_manager_def: Optional[IOManagerDefinition] = None,
        description: Optional[str] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        group_name: Optional[str] = None,
        resource_defs: Optional[Mapping[str, object]] = None,
        observe_fn: Optional[SourceAssetObserveFunction] = None,
        # This is currently private because it is necessary for source asset observation functions,
        # but we have not yet decided on a final API for associated one or more ops with a source
        # asset. If we were to make this public, then we would have a canonical public
        # `required_resource_keys` used for observation that might end up conflicting with a set of
        # required resource keys for a different operation.
        _required_resource_keys: Optional[AbstractSet[str]] = None,
        # Add additional fields to with_resources and with_group below
    ):
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        if partitions_def is not None and observe_fn is not None:
            raise DagsterInvalidDefinitionError(
                "Cannot specify a `partitions_def` for an observable source asset."
            )

        if resource_defs is not None:
            experimental_arg_warning("resource_defs", "SourceAsset.__new__")

        if io_manager_def is not None:
            experimental_arg_warning("io_manager_def", "SourceAsset.__new__")

        self.key = AssetKey.from_coerceable(key)
        metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        self.raw_metadata = metadata
        self.metadata = normalize_metadata(metadata, allow_invalid=True)
        self.resource_defs = wrap_resources_for_execution(
            dict(check.opt_mapping_param(resource_defs, "resource_defs"))
        )
        self._io_manager_def = check.opt_inst_param(
            io_manager_def, "io_manager_def", IOManagerDefinition
        )
        if self._io_manager_def:
            if not io_manager_key:
                io_manager_key = self.key.to_python_identifier("io_manager")

            if (
                io_manager_key in self.resource_defs
                and self.resource_defs[io_manager_key] != io_manager_def
            ):
                raise DagsterInvalidDefinitionError(
                    f"Provided conflicting definitions for io manager key '{io_manager_key}'."
                    " Please provide only one definition per key."
                )

            self.resource_defs[io_manager_key] = self._io_manager_def

        self.io_manager_key = check.opt_str_param(io_manager_key, "io_manager_key")
        self.partitions_def = check.opt_inst_param(
            partitions_def, "partitions_def", PartitionsDefinition
        )
        self.group_name = validate_group_name(group_name)
        self.description = check.opt_str_param(description, "description")
        self.observe_fn = check.opt_callable_param(observe_fn, "observe_fn")
        self._required_resource_keys = check.opt_set_param(
            _required_resource_keys, "_required_resource_keys", of_type=str
        )
        self._node_def = None

    def get_io_manager_key(self) -> str:
        return self.io_manager_key or DEFAULT_IO_MANAGER_KEY

    @property
    def io_manager_def(self) -> Optional[IOManagerDefinition]:
        io_manager_key = self.get_io_manager_key()
        return cast(
            Optional[IOManagerDefinition],
            self.resource_defs.get(io_manager_key) if io_manager_key else None,
        )

    @public
    @property
    def op(self) -> OpDefinition:
        check.invariant(
            isinstance(self.node_def, OpDefinition),
            "The NodeDefinition for this AssetsDefinition is not of type OpDefinition.",
        )
        return cast(OpDefinition, self.node_def)

    @public
    @property
    def is_observable(self) -> bool:
        return self.node_def is not None

    def _get_op_def_compute_fn(self, observe_fn: SourceAssetObserveFunction):
        from dagster._core.definitions.decorators.op_decorator import (
            DecoratedOpFunction,
            is_context_provided,
        )

        observe_fn_has_context = is_context_provided(get_function_params(observe_fn))

        def fn(context: OpExecutionContext):
            resource_kwarg_keys = [param.name for param in get_resource_args(observe_fn)]
            resource_kwargs = {key: getattr(context.resources, key) for key in resource_kwarg_keys}
            data_version = (
                observe_fn(context, **resource_kwargs)
                if observe_fn_has_context
                else observe_fn(**resource_kwargs)
            )

            check.inst(
                data_version,
                DataVersion,
                "Source asset observation function must return a DataVersion",
            )
            tags = {DATA_VERSION_TAG: data_version.value}
            context.log_event(
                AssetObservation(
                    asset_key=self.key,
                    tags=tags,
                )
            )

        return DecoratedOpFunction(fn)

    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return {requirement.key for requirement in self.get_resource_requirements()}

    @property
    def node_def(self) -> Optional[OpDefinition]:
        """Op that generates observation metadata for a source asset."""
        if self.observe_fn is None:
            return None

        if self._node_def is None:
            self._node_def = OpDefinition(
                compute_fn=self._get_op_def_compute_fn(self.observe_fn),
                name=self.key.to_python_identifier(),
                description=self.description,
                required_resource_keys=self._required_resource_keys,
            )
        return self._node_def

    def with_resources(self, resource_defs) -> "SourceAsset":
        from dagster._core.execution.resources_init import get_transitive_required_resource_keys

        overlapping_keys = get_resource_key_conflicts(self.resource_defs, resource_defs)
        if overlapping_keys:
            raise DagsterInvalidInvocationError(
                f"SourceAsset with key {self.key} has conflicting resource "
                "definitions with provided resources for the following keys: "
                f"{sorted(list(overlapping_keys))}. Either remove the existing "
                "resources from the asset or change the resource keys so that "
                "they don't overlap."
            )

        merged_resource_defs = merge_dicts(resource_defs, self.resource_defs)

        # Ensure top-level resource requirements are met - except for
        # io_manager, since that is a default it can be resolved later.
        ensure_requirements_satisfied(merged_resource_defs, list(self.get_resource_requirements()))

        io_manager_def = merged_resource_defs.get(self.get_io_manager_key())
        if not io_manager_def and self.get_io_manager_key() != DEFAULT_IO_MANAGER_KEY:
            raise DagsterInvalidDefinitionError(
                f"SourceAsset with asset key {self.key} requires IO manager with key"
                f" '{self.get_io_manager_key()}', but none was provided."
            )
        relevant_keys = get_transitive_required_resource_keys(
            {*self._required_resource_keys, self.get_io_manager_key()}, merged_resource_defs
        )

        relevant_resource_defs = {
            key: resource_def
            for key, resource_def in merged_resource_defs.items()
            if key in relevant_keys
        }

        io_manager_key = (
            self.get_io_manager_key()
            if self.get_io_manager_key() != DEFAULT_IO_MANAGER_KEY
            else None
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            return SourceAsset(
                key=self.key,
                io_manager_key=io_manager_key,
                description=self.description,
                partitions_def=self.partitions_def,
                metadata=self.raw_metadata,
                resource_defs=relevant_resource_defs,
                group_name=self.group_name,
                observe_fn=self.observe_fn,
                _required_resource_keys=self._required_resource_keys,
            )

    def with_attributes(
        self, group_name: Optional[str] = None, key: Optional[AssetKey] = None
    ) -> "SourceAsset":
        if group_name is not None and self.group_name != DEFAULT_GROUP_NAME:
            raise DagsterInvalidDefinitionError(
                "A group name has already been provided to source asset"
                f" {self.key.to_user_string()}"
            )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            return SourceAsset(
                key=key or self.key,
                metadata=self.raw_metadata,
                io_manager_key=self.io_manager_key,
                io_manager_def=self.io_manager_def,
                description=self.description,
                partitions_def=self.partitions_def,
                group_name=group_name,
                resource_defs=self.resource_defs,
                observe_fn=self.observe_fn,
                _required_resource_keys=self._required_resource_keys,
            )

    def get_resource_requirements(self) -> Iterator[ResourceRequirement]:
        if self.node_def is not None:
            yield from self.node_def.get_resource_requirements()
        yield SourceAssetIOManagerRequirement(
            key=self.get_io_manager_key(), asset_key=self.key.to_string()
        )
        for source_key, resource_def in self.resource_defs.items():
            yield from resource_def.get_resource_requirements(outer_context=source_key)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SourceAsset):
            return False
        else:
            return (
                self.key == other.key
                and self.raw_metadata == other.raw_metadata
                and self.io_manager_key == other.io_manager_key
                and self.description == other.description
                and self.group_name == other.group_name
                and self.resource_defs == other.resource_defs
                and self.observe_fn == other.observe_fn
            )

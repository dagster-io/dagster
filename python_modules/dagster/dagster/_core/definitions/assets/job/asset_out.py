from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union

import dagster._check as check
from dagster._annotations import (
    deprecated_param,
    hidden_param,
    only_allow_hidden_params_in_kwargs,
    public,
)
from dagster._core.definitions.assets.definition.asset_dep import AssetDep
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.events import (
    AssetKey,
    CoercibleToAssetKey,
    CoercibleToAssetKeyPrefix,
)
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.input import NoValueSentinel
from dagster._core.definitions.output import Out
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.utils import resolve_automation_condition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.tags import normalize_tags
from dagster._utils.warnings import disable_dagster_warnings

# Unfortunate, since AssetOut stores nearly all of the properties of
# an AssetSpec except for the key, we use a sentinel value to represent
# an unspecified key
EMPTY_ASSET_KEY_SENTINEL = AssetKey([])


@deprecated_param(param="legacy_freshness_policy", breaking_version="1.12.0")
@hidden_param(
    param="auto_materialize_policy",
    breaking_version="1.10.0",
    additional_warn_text="use `automation_condition` instead",
)
@public
class AssetOut:
    """Defines one of the assets produced by a :py:func:`@multi_asset <multi_asset>`.

    Args:
        key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the asset's key is the
            concatenation of the key_prefix and the asset's name. When using ``@multi_asset``, the
            asset name defaults to the key of the "outs" dictionary Only one of the "key_prefix" and
            "key" arguments should be provided.
        key (Optional[Union[str, Sequence[str], AssetKey]]): The asset's key. Only one of the
            "key_prefix" and "key" arguments should be provided.
        dagster_type (Optional[Union[Type, DagsterType]]]):
            The type of this output. Should only be set if the correct type can not
            be inferred directly from the type signature of the decorated function.
        description (Optional[str]): Human-readable description of the output.
        is_required (bool): Whether the presence of this field is required. (default: True)
        io_manager_key (Optional[str]): The resource key of the IO manager used for this output.
            (default: "io_manager").
        metadata (Optional[Dict[str, Any]]): A dict of the metadata for the output.
            For example, users can provide a file path if the data object will be stored in a
            filesystem, or provide information of a database table when it is going to load the data
            into the table.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If
            not provided, the name "default" is used.
        code_version (Optional[str]): The version of the code that generates this asset.
        automation_condition (Optional[AutomationCondition]): AutomationCondition to apply to the
            specified asset.
        backfill_policy (Optional[BackfillPolicy]): BackfillPolicy to apply to the specified asset.
        owners (Optional[Sequence[str]]): A list of strings representing owners of the asset. Each
            string can be a user's email address, or a team name prefixed with `team:`,
            e.g. `team:finops`.
        tags (Optional[Mapping[str, str]]): Tags for filtering and organizing. These tags are not
            attached to runs of the asset.
        kinds (Optional[set[str]]): A set of strings representing the kinds of the asset. These
    will be made visible in the Dagster UI.
    """

    _spec: AssetSpec
    key_prefix: Optional[Sequence[str]]
    dagster_type: Union[type, DagsterType]
    is_required: bool
    io_manager_key: Optional[str]
    backfill_policy: Optional[BackfillPolicy]

    def __init__(
        self,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        key: Optional[CoercibleToAssetKey] = None,
        dagster_type: Union[type, DagsterType] = NoValueSentinel,
        description: Optional[str] = None,
        is_required: bool = True,
        io_manager_key: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        group_name: Optional[str] = None,
        code_version: Optional[str] = None,
        automation_condition: Optional[AutomationCondition] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        owners: Optional[Sequence[str]] = None,
        tags: Optional[Mapping[str, str]] = None,
        kinds: Optional[set[str]] = None,
        legacy_freshness_policy: Optional[LegacyFreshnessPolicy] = None,
        freshness_policy: Optional[InternalFreshnessPolicy] = None,
        **kwargs,
    ):
        # Accept a hidden "spec" argument to allow for the AssetOut to be constructed from an AssetSpec
        # directly. This is used in the AssetOut.from_spec method.
        spec = kwargs.get("spec")
        if spec:
            del kwargs["spec"]

        only_allow_hidden_params_in_kwargs(AssetOut, kwargs)
        if isinstance(key_prefix, str):
            key_prefix = [key_prefix]

        check.invariant(
            not (key_prefix and key), "Only one of key_prefix and key should be provided"
        )

        auto_materialize_policy = kwargs.get("auto_materialize_policy")
        has_any_spec_args = any(
            [
                key,
                description,
                metadata,
                group_name,
                code_version,
                automation_condition,
                auto_materialize_policy,
                legacy_freshness_policy,
                freshness_policy,
                owners,
                tags,
                kinds,
            ]
        )
        check.invariant(
            not has_any_spec_args or not spec,
            "Cannot provide both spec and spec-related arguments (key, description, metadata, etc.)",
        )

        with disable_dagster_warnings():
            # This is a bit of a hack, since technically AssetOut does not hold all of the
            # properties of an AssetSpec - chiefly, it is missing a key. Still, this reduces
            # the amount of code duplication storing each of the properties in both AssetOut
            # and AssetSpec, and allows us to implement the from_spec method below.
            self._spec = spec or AssetSpec(
                key=AssetKey.from_coercible(key) if key is not None else EMPTY_ASSET_KEY_SENTINEL,
                description=check.opt_str_param(description, "description"),
                metadata=check.opt_mapping_param(metadata, "metadata", key_type=str),
                group_name=check.opt_str_param(group_name, "group_name"),
                code_version=check.opt_str_param(code_version, "code_version"),
                automation_condition=check.opt_inst_param(
                    resolve_automation_condition(automation_condition, auto_materialize_policy),
                    "automation_condition",
                    AutomationCondition,
                ),
                legacy_freshness_policy=check.opt_inst_param(
                    legacy_freshness_policy,
                    "legacy_freshness_policy",
                    LegacyFreshnessPolicy,
                ),
                freshness_policy=check.opt_inst_param(
                    freshness_policy,
                    "freshness_policy",
                    InternalFreshnessPolicy,
                ),
                owners=check.opt_sequence_param(owners, "owners", of_type=str),
                tags=normalize_tags(tags or {}, strict=True),
                kinds=check.opt_set_param(kinds, "kinds", of_type=str),
            )
        self.key_prefix = key_prefix
        self.dagster_type = dagster_type
        self.is_required = is_required
        self.io_manager_key = io_manager_key
        self.backfill_policy = backfill_policy

    @property
    def key(self) -> Optional[AssetKey]:
        return self._spec.key if self._spec.key != EMPTY_ASSET_KEY_SENTINEL else None

    @property
    def metadata(self) -> Optional[Mapping[str, Any]]:
        return self._spec.metadata

    @property
    def description(self) -> Optional[str]:
        return self._spec.description

    @property
    def group_name(self) -> Optional[str]:
        return self._spec.group_name

    @property
    def code_version(self) -> Optional[str]:
        return self._spec.code_version

    @property
    def legacy_freshness_policy(self) -> Optional[LegacyFreshnessPolicy]:
        return self._spec.legacy_freshness_policy

    @property
    def freshness_policy(self) -> Optional[InternalFreshnessPolicy]:
        return self._spec.freshness_policy

    @property
    def automation_condition(self) -> Optional[AutomationCondition]:
        return self._spec.automation_condition

    @property
    def owners(self) -> Optional[Sequence[str]]:
        return self._spec.owners

    @property
    def tags(self) -> Optional[Mapping[str, str]]:
        return self._spec.tags

    @property
    def kinds(self) -> Optional[set[str]]:
        return self._spec.kinds

    def to_out(self) -> Out:
        return Out(
            dagster_type=self.dagster_type,
            description=self.description,
            metadata=self.metadata,
            is_required=self.is_required,
            io_manager_key=self.io_manager_key,
            code_version=self.code_version,
        )

    def to_spec(
        self,
        key: AssetKey,
        deps: Sequence[AssetDep],
        additional_tags: Mapping[str, str] = {},
        partitions_def: Optional[PartitionsDefinition] = ...,
    ) -> AssetSpec:
        return self._spec.replace_attributes(
            key=key,
            tags={**additional_tags, **self.tags} if self.tags else additional_tags,
            kinds=self.kinds,
            deps=[*self._spec.deps, *deps],
            partitions_def=partitions_def if partitions_def is not None else ...,
        )

    @public
    @staticmethod
    def from_spec(
        spec: AssetSpec,
        dagster_type: Union[type, DagsterType] = NoValueSentinel,
        is_required: bool = True,
        io_manager_key: Optional[str] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
    ) -> "AssetOut":
        """Builds an AssetOut from the passed spec.

        Args:
            spec (AssetSpec): The spec to build the AssetOut from.
            dagster_type (Optional[Union[Type, DagsterType]]): The type of this output. Should only
                be set if the correct type can not be inferred directly from the type signature of
                the decorated function.
            is_required (bool): Whether the presence of this field is required. (default: True)
            io_manager_key (Optional[str]): The resource key of the IO manager used for this output.
                (default: "io_manager").
            backfill_policy (Optional[BackfillPolicy]): BackfillPolicy to apply to the specified
                asset.

        Returns:
            AssetOut: The AssetOut built from the spec.
        """
        if spec.deps:
            raise DagsterInvalidDefinitionError(
                "Currently, cannot build AssetOut from spec with deps"
            )
        return AssetOut(
            spec=spec,
            dagster_type=dagster_type,
            is_required=is_required,
            io_manager_key=io_manager_key,
            backfill_policy=backfill_policy,
        )

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return (
            self.automation_condition.as_auto_materialize_policy()
            if self.automation_condition
            else None
        )

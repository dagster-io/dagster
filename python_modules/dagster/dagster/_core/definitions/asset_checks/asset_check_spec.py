from collections.abc import Iterable, Mapping
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, Optional, Union

from dagster_shared.record import (
    IHaveNew,
    ImportFrom,
    LegacyNamedTupleMixin,
    record_custom,
    replace,
)
from dagster_shared.serdes import whitelist_for_serdes
from typing_extensions import TypeAlias

from dagster._annotations import PublicAttr, public
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, CoercibleToAssetKey

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.asset_dep import AssetDep, CoercibleToAssetDep
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationCondition,
    )
    from dagster._core.definitions.source_asset import SourceAsset


@public
@whitelist_for_serdes
class AssetCheckSeverity(Enum):
    """Severity level for an AssetCheckResult.

    - WARN: a potential issue with the asset
    - ERROR: a definite issue with the asset

    Severity does not impact execution of the asset or downstream assets.
    """

    WARN = "WARN"
    ERROR = "ERROR"


LazyAutomationCondition: TypeAlias = Annotated[
    "AutomationCondition",  # Ideally this would be AutomationCondition[AssetCheckKey] if record was updated to handle it
    ImportFrom("dagster._core.definitions.declarative_automation.automation_condition"),
]

LazyAssetDep: TypeAlias = Annotated[
    "AssetDep", ImportFrom("dagster._core.definitions.assets.definition.asset_dep")
]


@public
@record_custom
class AssetCheckSpec(IHaveNew, LegacyNamedTupleMixin):
    name: PublicAttr[str]
    asset_key: PublicAttr[AssetKey]
    description: PublicAttr[Optional[str]]
    additional_deps: PublicAttr[Iterable[LazyAssetDep]]
    blocking: PublicAttr[bool]
    metadata: PublicAttr[Mapping[str, Any]]
    automation_condition: PublicAttr[Optional[LazyAutomationCondition]]

    """Defines information about an asset check, except how to execute it.

    AssetCheckSpec is often used as an argument to decorators that decorator a function that can
    execute multiple checks - e.g. `@asset`, and `@multi_asset`. It defines one of the checks that
    will be executed inside that function.

    Args:
        name (str): Name of the check.
        asset (Union[AssetKey, Sequence[str], str, AssetsDefinition, SourceAsset]): The asset that
            the check applies to.
        description (Optional[str]): Description for the check.
        additional_deps (Optional[Iterable[AssetDep]]): Additional dependencies for the check. The
            check relies on these assets in some way, but the result of the check only applies to
            the asset specified by `asset`. For example, the check may test that `asset` has
            matching data with an asset in `additional_deps`. This field holds both `additional_deps`
            and `additional_ins` passed to @asset_check.
        blocking (bool): When enabled, if the check fails with severity `AssetCheckSeverity.ERROR`,
            then downstream assets won't execute. If this AssetCheckSpec is used in a multi-asset,
            that multi-asset is responsible for enforcing that downstream assets within the
            same step do not execute after a blocking asset check fails.
        metadata (Optional[Mapping[str, Any]]):  A dict of static metadata for this asset check.
    """

    def __new__(
        cls,
        name: str,
        *,
        asset: Union[CoercibleToAssetKey, "AssetsDefinition", "SourceAsset"],
        description: Optional[str] = None,
        additional_deps: Optional[Iterable["CoercibleToAssetDep"]] = None,
        blocking: bool = False,
        metadata: Optional[Mapping[str, Any]] = None,
        automation_condition: Optional["AutomationCondition[AssetCheckKey]"] = None,
    ):
        from dagster._core.definitions.assets.definition.asset_dep import (
            coerce_to_deps_and_check_duplicates,
        )

        asset_key = AssetKey.from_coercible_or_definition(asset)

        additional_asset_deps = coerce_to_deps_and_check_duplicates(
            additional_deps, AssetCheckKey(asset_key, name)
        )

        for dep in additional_asset_deps:
            if dep.asset_key == asset_key:
                raise ValueError(
                    f"Asset check {name} for asset {asset_key.to_string()} cannot have an additional "
                    f"dependency on asset {asset_key.to_string()}."
                )

        return super().__new__(
            cls,
            name=name,
            asset_key=asset_key,
            description=description,
            additional_deps=additional_asset_deps,
            blocking=blocking,
            metadata=metadata or {},
            automation_condition=automation_condition,
        )

    def get_python_identifier(self) -> str:
        """Returns a string uniquely identifying the asset check, that uses only the characters
        allowed in a Python identifier.
        """
        return f"{self.asset_key.to_python_identifier()}_{self.name}".replace(".", "_")

    @property
    def key(self) -> AssetCheckKey:
        return AssetCheckKey(self.asset_key, self.name)

    def replace_key(self, key: AssetCheckKey) -> "AssetCheckSpec":
        return replace(self, asset_key=key.asset_key, name=key.name)

    def with_metadata(self, metadata: Mapping[str, Any]) -> "AssetCheckSpec":
        return replace(self, metadata=metadata)

from collections.abc import Iterable, Mapping
from enum import Enum
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Union

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, CoercibleToAssetKey

if TYPE_CHECKING:
    from dagster._core.definitions.asset_dep import AssetDep, CoercibleToAssetDep
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationCondition,
    )
    from dagster._core.definitions.source_asset import SourceAsset


@whitelist_for_serdes
class AssetCheckSeverity(Enum):
    """Severity level for an AssetCheckResult.

    - WARN: a potential issue with the asset
    - ERROR: a definite issue with the asset

    Severity does not impact execution of the asset or downstream assets.
    """

    WARN = "WARN"
    ERROR = "ERROR"


class AssetCheckSpec(
    NamedTuple(
        "_AssetCheckSpec",
        [
            ("name", PublicAttr[str]),
            ("asset_key", PublicAttr[AssetKey]),
            ("description", PublicAttr[Optional[str]]),
            ("additional_deps", PublicAttr[Iterable["AssetDep"]]),
            (
                "blocking",  # intentionally not public, see https://github.com/dagster-io/dagster/issues/20659
                bool,
            ),
            ("metadata", PublicAttr[Optional[Mapping[str, Any]]]),
            ("automation_condition", Optional["AutomationCondition[AssetCheckKey]"]),
        ],
    )
):
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
        from dagster._core.definitions.asset_dep import coerce_to_deps_and_check_duplicates
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationCondition,
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
            name=check.str_param(name, "name"),
            asset_key=asset_key,
            description=check.opt_str_param(description, "description"),
            additional_deps=additional_asset_deps,
            blocking=check.bool_param(blocking, "blocking"),
            metadata=check.opt_mapping_param(metadata, "metadata", key_type=str),
            automation_condition=check.opt_inst_param(
                automation_condition, "automation_condition", AutomationCondition
            ),
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
        return self._replace(asset_key=key.asset_key, name=key.name)

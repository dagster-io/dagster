from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable, Mapping, NamedTuple, Optional, Union

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.asset_key import (
    AssetKey,
    CoercibleToAssetKey,
    CoercibleToAssetKeyPrefix,
)
from dagster._serdes.serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.definitions.asset_dep import AssetDep, CoercibleToAssetDep
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.source_asset import SourceAsset


@experimental
@whitelist_for_serdes
class AssetCheckSeverity(Enum):
    """Severity level for an AssetCheckResult.

    - WARN: a potential issue with the asset
    - ERROR: a definite issue with the asset

    Severity does not impact execution of the asset or downstream assets.
    """

    WARN = "WARN"
    ERROR = "ERROR"


@experimental(emit_runtime_warning=False)
@whitelist_for_serdes(old_storage_names={"AssetCheckHandle"})
class AssetCheckKey(NamedTuple):
    """Check names are expected to be unique per-asset. Thus, this combination of asset key and
    check name uniquely identifies an asset check within a deployment.
    """

    asset_key: PublicAttr[AssetKey]
    name: PublicAttr[str]

    @staticmethod
    def from_graphql_input(graphql_input: Mapping[str, Any]) -> "AssetCheckKey":
        return AssetCheckKey(
            asset_key=AssetKey.from_graphql_input(graphql_input["assetKey"]),
            name=graphql_input["name"],
        )

    def with_asset_key_prefix(self, prefix: CoercibleToAssetKeyPrefix) -> "AssetCheckKey":
        return self._replace(asset_key=self.asset_key.with_prefix(prefix))


@experimental
class AssetCheckSpec(
    NamedTuple(
        "_AssetCheckSpec",
        [
            ("name", PublicAttr[str]),
            ("asset_key", PublicAttr[AssetKey]),
            ("description", PublicAttr[Optional[str]]),
            ("additional_deps", PublicAttr[Optional[Iterable["AssetDep"]]]),
            ("blocking", PublicAttr[bool]),
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
        blocking (bool): When enabled, runs that include this check and any downstream assets that
            depend on `asset` will wait for this check to complete before starting the downstream
            assets. If the check fails with severity `AssetCheckSeverity.ERROR`, then the downstream
            assets won't execute.
    """

    def __new__(
        cls,
        name: str,
        *,
        asset: Union[CoercibleToAssetKey, "AssetsDefinition", "SourceAsset"],
        description: Optional[str] = None,
        additional_deps: Optional[Iterable["CoercibleToAssetDep"]] = None,
        blocking: bool = False,
    ):
        from dagster._core.definitions.asset_dep import coerce_to_deps_and_check_duplicates

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
        )

    def get_python_identifier(self) -> str:
        """Returns a string uniquely identifying the asset check, that uses only the characters
        allowed in a Python identifier.
        """
        return f"{self.asset_key.to_python_identifier()}_{self.name}"

    @property
    def key(self) -> AssetCheckKey:
        return AssetCheckKey(self.asset_key, self.name)

    def with_asset_key_prefix(self, prefix: CoercibleToAssetKeyPrefix) -> "AssetCheckSpec":
        return self._replace(asset_key=self.asset_key.with_prefix(prefix))

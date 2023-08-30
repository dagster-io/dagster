from enum import Enum
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._serdes.serdes import whitelist_for_serdes


@experimental
@whitelist_for_serdes
class AssetCheckSeverity(Enum):
    """Severity level for an asset check.

    Severities:

    - WARN: If the check fails, don't fail the step.
    - ERROR: If the check fails, fail the step and, within the run, skip materialization of any
      assets that are downstream of the asset being checked.
    """

    WARN = "WARN"
    ERROR = "ERROR"


@experimental
@whitelist_for_serdes
class AssetCheckHandle(NamedTuple):
    """Check names are expected to be unique per-asset. Thus, this combination of asset key and
    check name uniquely identifies an asset check within a deployment.
    """

    asset_key: PublicAttr[AssetKey]
    name: PublicAttr[str]


@experimental
class AssetCheckSpec(
    NamedTuple(
        "_AssetCheckSpec",
        [
            ("name", PublicAttr[str]),
            ("asset_key", PublicAttr[AssetKey]),
            ("description", PublicAttr[Optional[str]]),
            ("severity", PublicAttr[AssetCheckSeverity]),
        ],
    )
):
    """Defines information about an check, except how to execute it.

    AssetCheckSpec is often used as an argument to decorators that decorator a function that can
    execute multiple checks - e.g. `@asset`, and `@multi_asset`. It defines one of the checks that
    will be executed inside that function.

    Args:
        name (str): Name of the check.
        asset_key (AssetKey): The key of the asset that the check applies to.
        description (Optional[str]): Description for the check.
        severity (AssetCheckSeverity): Severity of the check. Defaults to `WARN`
    """

    def __new__(
        cls,
        name: str,
        *,
        asset_key: CoercibleToAssetKey,
        description: Optional[str] = None,
        severity: AssetCheckSeverity = AssetCheckSeverity.WARN,
    ):
        return super().__new__(
            cls,
            name=check.str_param(name, "name"),
            asset_key=AssetKey.from_coercible(asset_key),
            description=check.opt_str_param(description, "description"),
            severity=check.inst_param(severity, "severity", AssetCheckSeverity),
        )

    def get_python_identifier(self) -> str:
        """Returns a string uniquely identifying the asset check, that uses only the characters
        allowed in a Python identifier.
        """
        return f"{self.asset_key.to_python_identifier()}_{self.name}"

    @property
    def handle(self) -> AssetCheckHandle:
        return AssetCheckHandle(self.asset_key, self.name)

from typing import NamedTuple, Optional

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey


@experimental
class AssetCheckSpec(
    NamedTuple(
        "_AssetCheckSpec",
        [
            ("name", PublicAttr[str]),
            ("asset_key", PublicAttr[AssetKey]),
            ("description", PublicAttr[Optional[str]]),
        ],
    )
):
    """Defines information about an check, except how to execute it.

    AssetCheckSpec is often used as an argument to decorators that decorator a function that can
    execute multiple checks - e.g. `@asset`, and `@multi_asset`. It defines one of the checks that
    will be executed inside that function.

    Attributes:
        name (str): Name of the check.
        asset_key (AssetKey): The key of the asset that the check applies to.
        description (Optional[str]): Description for the check.
    """

    def __new__(
        cls,
        name: str,
        *,
        asset_key: CoercibleToAssetKey,
        description: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            name=check.str_param(name, "name"),
            asset_key=AssetKey.from_coercible(asset_key),
            description=check.opt_str_param(description, "description"),
        )

    def get_python_identifier(self) -> str:
        """Returns a string uniquely identifying the asset check, that uses only the characters
        allowed in a Python identifier.
        """
        return f"{self.asset_key.to_python_identifier()}_{self.name}"

from typing import Callable, Optional, Sequence

from dagster import AssetSpec, Definitions
from dagster._core.definitions.decorators.asset_decorator import multi_asset


def defs_for_python_callable(
    *, asset_specs: Sequence[AssetSpec], python_callable: Callable, name: Optional[str] = None
) -> Definitions:
    name = name or python_callable.__name__

    @multi_asset(name=name, specs=asset_specs)
    def _an_asset() -> None:
        python_callable()

    return Definitions(assets=[_an_asset])

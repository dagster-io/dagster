from typing import Callable

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoader


def defs_loader(fn: Callable[[], Definitions]) -> DefinitionsLoader:
    """Produces a DefinitionsLoader by decorating a function that returns a Definitions object.

    Returns:
        DefinitionsLoader

    Examples:
        .. code-block:: python
            from dagster import defs_loader, Definitions

            @defs_loader
            def defs() -> Definitions:
                my_assets = build_assets_in_computationally_expensive_way()

                return Definitions(assets=assets)
    """
    return DefinitionsLoader(load_fn=fn)

from pathlib import Path
from typing import Optional

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent


class SingletonComponent(StateBackedComponent):
    """Forthright and by the book - can only be loaded once."""

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        # this should only ever be called once
        sentinel_path = context.component_path.file_path / "sentinel.txt"
        assert not sentinel_path.exists(), "SingletonComponent has already been loaded!"
        sentinel_path.touch()

        return dg.Definitions(assets=[dg.AssetSpec("singleton")])

    async def write_state_to_path(self, state_path: Path) -> None:
        pass

from pathlib import Path
from typing import Optional

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent


class DuplicitousComponent(StateBackedComponent):
    """Extremely sneaky - tracks how many times it has been loaded."""

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        # keeps track of how many times this has been called
        postfix = 0
        while True:
            sentinel_path = context.component_path.file_path / str(postfix)
            if not sentinel_path.exists():
                sentinel_path.touch()
                break
            postfix += 1

        return dg.Definitions(assets=[dg.AssetSpec(f"dup_{postfix}")])

    async def write_state_to_path(self, state_path: Path) -> None:
        pass

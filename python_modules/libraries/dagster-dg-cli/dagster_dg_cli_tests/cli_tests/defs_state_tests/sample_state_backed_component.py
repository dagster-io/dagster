from pathlib import Path
from typing import Optional

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent


class SampleStateBackedComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    fail_write: bool = False

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        with open(state_path) as f:
            state = f.read()

        @dg.asset(name=state)
        def the_asset(): ...

        return dg.Definitions(assets=[the_asset])

    async def write_state_to_path(self, state_path: Path) -> None:
        if self.fail_write:
            raise Exception("Failed to write state")
        else:
            state_path.write_text("hi")

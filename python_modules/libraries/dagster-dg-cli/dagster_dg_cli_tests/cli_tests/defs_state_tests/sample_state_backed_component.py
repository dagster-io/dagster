from pathlib import Path
from typing import Optional

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import DefsStateConfig


class SampleStateBackedComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    fail_write: bool = False
    defs_state_key_id: Optional[str] = None

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig.versioned_state_storage()

    def get_defs_state_key(self) -> str:
        default_key = super().get_defs_state_key()
        if self.defs_state_key_id is None:
            return default_key
        return f"{default_key}[{self.defs_state_key_id}]"

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

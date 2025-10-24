from pathlib import Path
from typing import Optional

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import DefsStateConfig
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType


class SampleStateBackedComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        assert state_path is not None
        with open(state_path) as f:
            state = f.read()
        assert state == "hi"

        @dg.asset(name=state)
        def the_asset(): ...

        return dg.Definitions(assets=[the_asset])

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig(
            key=self.__class__.__name__,
            management_type=DefsStateManagementType.VERSIONED_STATE_STORAGE,
            refresh_if_dev=True,
        )

    async def write_state_to_path(self, state_path: Path) -> None:
        # for the tests that use this, we're going to manually do this outside of the component
        pass

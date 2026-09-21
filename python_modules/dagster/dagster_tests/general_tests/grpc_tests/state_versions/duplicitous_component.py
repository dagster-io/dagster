from pathlib import Path

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import DefsStateConfig
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType


class DuplicitousComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    """Tracks how many times it has been loaded via a sentinel file counter.

    Each load creates a new sentinel file (0, 1, 2, ...) and produces an
    asset named dup_{N}. This lets tests verify that incremental reloads
    are actually re-executing build_defs_from_state.
    """

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Path | None
    ) -> dg.Definitions:
        postfix = 0
        while True:
            sentinel_path = context.component_path.file_path / str(postfix)
            if not sentinel_path.exists():
                sentinel_path.touch()
                break
            postfix += 1

        @dg.asset(name=f"dup_{postfix}")
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
        state_path.write_text("placeholder", encoding="utf-8")

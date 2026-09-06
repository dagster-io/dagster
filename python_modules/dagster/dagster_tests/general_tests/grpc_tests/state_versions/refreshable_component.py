from pathlib import Path

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import DefsStateConfig
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType


class RefreshableComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    """Component whose ``write_state_to_path`` actually writes content.

    Used to exercise ``RefreshComponentState`` end-to-end: refresh_state on the
    server invokes write_state_to_path, which uploads new versioned state.
    """

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Path | None
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()
        content = state_path.read_text()

        @dg.asset(name=f"refreshable_{content}")
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
        # Each invocation writes a unique token so successive refreshes produce
        # distinct state files (and hence distinct rebuilt assets).
        import uuid

        state_path.write_text(uuid.uuid4().hex[:8], encoding="utf-8")

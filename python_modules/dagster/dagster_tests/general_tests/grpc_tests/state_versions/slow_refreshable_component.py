import asyncio
import os
import time
from pathlib import Path

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import DefsStateConfig
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType


class SlowRefreshableComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    """Refreshable component whose write_state_to_path sleeps and records
    [start, end] timestamps to a host-local file so tests can assert that
    concurrent refreshes for the same key serialize.
    """

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Path | None
    ) -> dg.Definitions:
        return dg.Definitions()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig(
            key=self.__class__.__name__,
            management_type=DefsStateManagementType.VERSIONED_STATE_STORAGE,
            refresh_if_dev=True,
        )

    async def write_state_to_path(self, state_path: Path) -> None:
        import uuid

        # The test sets SLOW_REFRESH_TIMESTAMPS_FILE so it can read back the
        # [start, end] intervals and assert that concurrent same-key refreshes
        # serialize.
        timestamps_file = Path(os.environ["SLOW_REFRESH_TIMESTAMPS_FILE"])
        start = time.monotonic()
        await asyncio.sleep(1.0)
        state_path.write_text(uuid.uuid4().hex[:8], encoding="utf-8")
        end = time.monotonic()
        with timestamps_file.open("a", encoding="utf-8") as f:
            f.write(f"{start},{end}\n")

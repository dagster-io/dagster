"""Regression test for https://github.com/dagster-io/dagster/issues/34403.

`_store_local_filesystem_state` must remove the local state marker file before
rebuilding state. The marker is a *file* (`<state dir>/state`), so the previous
`shutil.rmtree(state_path, ignore_errors=True)` raised `NotADirectoryError`
which was swallowed, leaving the stale marker in place for the whole rebuild.
Concurrent readers use the marker's existence to decide whether to consume the
local state directory, so they observed a half-built state instead of falling
back to "no state".
"""

import asyncio
import json
from pathlib import Path
from typing import ClassVar

import dagster as dg
import pytest
from dagster.components.component import state_backed_component
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)


class MarkerObservingComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.local_filesystem()

    observed: ClassVar[dict] = {}

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig.from_args(self.defs_state, default_key=self.__class__.__name__)

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Path | None
    ) -> dg.Definitions:
        return dg.Definitions()

    async def write_state_to_path(self, state_path: Path) -> None:
        self.observed["marker_exists_at_write"] = state_path.exists()
        self.observed["marker_content_at_write"] = (
            state_path.read_text(encoding="utf-8") if state_path.exists() else None
        )
        state_path.write_text(json.dumps({"value": "fresh"}), encoding="utf-8")


def test_local_filesystem_state_marker_cleared_before_rebuild(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = "MarkerObservingComponent"
    state_dir = tmp_path / ".local_defs_state" / key
    state_dir.mkdir(parents=True)
    marker = state_dir / "state"
    stale = json.dumps({"value": "stale"})
    marker.write_text(stale, encoding="utf-8")

    monkeypatch.setattr(state_backed_component, "get_local_state_path", lambda _key, _root: marker)

    component = MarkerObservingComponent()
    asyncio.run(component._store_local_filesystem_state(key, None, tmp_path))  # noqa: SLF001

    # During the rebuild the stale marker must be gone, so concurrent readers
    # fall back to "no state" instead of consuming a half-built state directory.
    assert component.observed["marker_exists_at_write"] is False
    assert component.observed["marker_content_at_write"] is None
    # The rebuild still writes the fresh marker.
    assert json.loads(marker.read_text(encoding="utf-8")) == {"value": "fresh"}

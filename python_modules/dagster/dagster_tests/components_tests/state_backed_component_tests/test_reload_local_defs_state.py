"""Regression tests for https://github.com/dagster-io/dagster/issues/34434.

Clicking "Reload definitions" in the UI respawns the code server, but the new
process's load used to serve any existing ``defs/.local_defs_state`` snapshot
as-is, so runs could silently keep executing with component definitions that
predate source updates. This module exercises the reload-triggered load (the
respawned code server carries ``DAGSTER_REFRESH_LOCAL_DEFS_STATE_ON_LOAD=1``):

- a reload-triggered load must regenerate the local defs state (the same
  ``refresh_state`` code path as ``dg utils refresh-defs-state``), and
- when it cannot (refresh failure, or an explicit ``refresh_if_dev: false``
  opt-out) it must warn instead of silently serving the stale snapshot.
"""

import asyncio
import itertools
import json
from pathlib import Path
from typing import ClassVar

import dagster as dg
import pytest
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster.components.utils.project_paths import get_local_state_path

# Environment set on code servers spawned in response to a user-initiated code
# location reload ("Reload definitions" in the UI).
RELOAD_ENV = {"DAGSTER_REFRESH_LOCAL_DEFS_STATE_ON_LOAD": "1"}

STATE_KEY = "ReloadStateComponent"

# Monotonic so regenerated state is always distinguishable from the previously
# served snapshot.
_STATE_WRITE_COUNT = itertools.count(1)


class ReloadStateComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.local_filesystem()

    # Test hook: when True, write_state_to_path raises (simulating a failed
    # refresh, e.g. an external system that is unreachable during the reload).
    fail_state_refresh: ClassVar[bool] = False

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig.from_args(self.defs_state, default_key=STATE_KEY)

    def write_state_to_path(self, state_path: Path) -> None:
        if ReloadStateComponent.fail_state_refresh:
            raise RuntimeError("state refresh failed")
        state_path.write_text(
            json.dumps({"value": f"bar_{next(_STATE_WRITE_COUNT)}"}), encoding="utf-8"
        )

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Path | None
    ) -> dg.Definitions:
        if state_path is None:
            value = "initial"
        else:
            with open(state_path, encoding="utf-8") as f:
                value = json.load(f)["value"]

        @dg.asset(
            name=f"the_asset_{context.component_path.file_path.stem}",
            metadata={"state_value": value},
        )
        def the_asset():
            return dg.MaterializeResult(metadata={"foo": value})

        return dg.Definitions(assets=[the_asset])

    def _get_state_refresh_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        project_root = context.project_root

        @dg.op
        def refresh_state_op():
            asyncio.run(self.refresh_state(project_root))

        @dg.job(name=f"state_refresh_job_{context.component_path.file_path.stem}")
        def state_refresh_job():
            refresh_state_op()

        return dg.Definitions(jobs=[state_refresh_job])

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions.merge(
            super().build_defs(context),
            self._get_state_refresh_defs(context),
        )


def _scaffold(sandbox, **defs_state_attrs):
    return sandbox.scaffold_component(
        component_cls=ReloadStateComponent,
        defs_yaml_contents={
            "type": (
                "dagster_tests.components_tests.state_backed_component_tests."
                "test_reload_local_defs_state.ReloadStateComponent"
            ),
            "attributes": {
                "defs_state": {
                    "management_type": "LOCAL_FILESYSTEM",
                    **defs_state_attrs,
                }
            },
        },
        defs_path="foo",
    )


def _load_state_value(component_path, sandbox):
    with (
        scoped_definitions_load_context(),
        sandbox.load_component_and_build_defs(defs_path=component_path) as (_, defs),
    ):
        specs = defs.resolve_all_asset_specs()
        return specs[0].metadata["state_value"], defs


def _populate_snapshot_state(component_path, sandbox):
    """Simulate `dg utils refresh-defs-state`: writes the state snapshot."""
    _, defs = _load_state_value(component_path, sandbox)
    defs.get_job_def("state_refresh_job_foo").execute_in_process()
    with open(get_local_state_path(STATE_KEY, sandbox.project_root), encoding="utf-8") as f:
        return f.read()


def test_reload_definitions_regenerates_local_defs_state() -> None:
    """A reload-triggered load must rebuild `.local_defs_state` from current sources.

    Reproduces the issue sequence at the loader level: snapshot written
    (`dg utils refresh-defs-state`) -> sources change -> Reload definitions ->
    the reloaded code location must not serve the old snapshot.
    """
    with instance_for_test(), create_defs_folder_sandbox() as sandbox:
        component_path = _scaffold(sandbox)

        # No state yet: builds from source.
        value, _ = _load_state_value(component_path, sandbox)
        assert value == "initial"

        # Snapshot written (as `dg utils refresh-defs-state` would).
        snapshot_state = _populate_snapshot_state(component_path, sandbox)
        stale_value, _ = _load_state_value(component_path, sandbox)
        assert stale_value.startswith("bar_")

        # Plain (non-reload) load keeps serving the snapshot untouched —
        # the baked-state contract for normal boots is unchanged.
        value, _ = _load_state_value(component_path, sandbox)
        assert value == stale_value

        # Sources change, user clicks "Reload definitions": the respawned code
        # server loads with the reload flag set. The state must be regenerated.
        with environ(RELOAD_ENV):
            fresh_value, _ = _load_state_value(component_path, sandbox)

        assert fresh_value.startswith("bar_")
        assert fresh_value != stale_value, (
            "reload-triggered load served the stale .local_defs_state snapshot"
        )
        with open(get_local_state_path(STATE_KEY, sandbox.project_root), encoding="utf-8") as f:
            regenerated_state = f.read()
        assert regenerated_state != snapshot_state, ".local_defs_state was not rewritten on reload"


def test_reload_refresh_failure_warns_and_serves_existing_snapshot() -> None:
    """A failed refresh during reload must warn and fall back — never fail the load."""
    from dagster.components.component.state_backed_component import StaleLocalDefsStateWarning

    with instance_for_test(), create_defs_folder_sandbox() as sandbox:
        ReloadStateComponent.fail_state_refresh = False
        try:
            component_path = _scaffold(sandbox)
            _populate_snapshot_state(component_path, sandbox)
            stale_value, _ = _load_state_value(component_path, sandbox)
            assert stale_value.startswith("bar_")

            # Refresh now fails (e.g. external system unreachable).
            ReloadStateComponent.fail_state_refresh = True

            with (
                environ(RELOAD_ENV),
                pytest.warns(StaleLocalDefsStateWarning, match="dg utils refresh-defs-state"),
            ):
                value, _ = _load_state_value(component_path, sandbox)

            # Falls back to the existing snapshot instead of erroring out.
            assert value == stale_value
        finally:
            ReloadStateComponent.fail_state_refresh = False


def test_reload_with_refresh_opt_out_warns_without_refreshing() -> None:
    """refresh_if_dev: false opts out of the refresh — but the reload must warn."""
    from dagster.components.component.state_backed_component import StaleLocalDefsStateWarning

    with instance_for_test(), create_defs_folder_sandbox() as sandbox:
        component_path = _scaffold(sandbox, **{"refresh_if_dev": False})
        _populate_snapshot_state(component_path, sandbox)
        stale_value, _ = _load_state_value(component_path, sandbox)
        assert stale_value.startswith("bar_")

        with environ(RELOAD_ENV), pytest.warns(StaleLocalDefsStateWarning, match="refresh_if_dev"):
            value, _ = _load_state_value(component_path, sandbox)

        assert value == stale_value

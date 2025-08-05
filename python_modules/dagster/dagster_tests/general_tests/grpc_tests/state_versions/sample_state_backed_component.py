from pathlib import Path
from typing import Optional

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent


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

    def write_state_to_path(self, state_path: Path) -> None:
        # for the tests that use this, we're going to manually do this outside of the component
        pass

import inspect
import os
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable

from dagster._core.instance_for_test import instance_for_test
from dagster_graphql.test.utils import define_out_of_process_context, materialize_assets

_STATE_BACKED_DEFINITIONS_TEST_LOG_FILE_VAR = "DAGSTER_STATE_BACKED_DEFINITIONS_TEST_LOG_FILE"


def test_state_backed_defs_loader(monkeypatch) -> None:
    with NamedTemporaryFile(delete=False) as f:
        log_file_path = f.name
    try:
        monkeypatch.setenv(_STATE_BACKED_DEFINITIONS_TEST_LOG_FILE_VAR, log_file_path)
        with (
            instance_for_test(synchronous_run_coordinator=True) as instance,
            _temp_script(_state_backed_defs) as repo_path,
        ):
            with define_out_of_process_context(repo_path, None, instance) as context:
                assert _get_num_calls(log_file_path) == 1
                materialize_assets(context)
                assert _get_num_calls(log_file_path) == 1
    finally:
        os.unlink(log_file_path)


def _get_num_calls(log_file_path: str) -> int:
    lines = Path(log_file_path).read_text().strip().split("\n")
    return len(lines)


@contextmanager
def _temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile(suffix=".py") as file:
        file.write(source.encode())
        file.flush()
        yield file.name


# This is written to a temporary file for the test. It is important that this is written to a
# standalone file and not wrapped in @lazy_definitions, because we are specifically testing the
# effects of executing this at import time.
def _state_backed_defs() -> None:
    import os

    from dagster._core.definitions.decorators.asset_decorator import asset
    from dagster._core.definitions.definitions_class import Definitions
    from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
    from dagster._record import record
    from dagster_shared.serdes import whitelist_for_serdes

    @whitelist_for_serdes
    @record
    class ExampleDefState:
        a_string: str

    class ExampleStateBackedDefinitionsLoader(StateBackedDefinitionsLoader[ExampleDefState]):
        @property
        def defs_key(self) -> str:
            return "test_key"

        def fetch_state(self) -> ExampleDefState:
            log_file = os.environ["DAGSTER_STATE_BACKED_DEFINITIONS_TEST_LOG_FILE"]
            with open(log_file, "a") as f:
                f.write("fetch_state\n")
            return ExampleDefState(a_string="foo")

        def defs_from_state(self, state: ExampleDefState) -> Definitions:
            @asset(key=state.a_string)
            def foo_asset(_):
                return 1

            return Definitions(assets=[foo_asset])

    assets = ExampleStateBackedDefinitionsLoader().build_defs().assets
    defs = Definitions(assets=assets)  # noqa: F841

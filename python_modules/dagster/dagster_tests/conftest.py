import os
import subprocess
import sys

import pytest

import dagster._seven as seven

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

# Suggested workaround in https://bugs.python.org/issue37380 for subprocesses
# failing to open sporadically on windows after other subprocesses were closed.
# Fixed in later versions of Python but never back-ported, see the bug for details.
if seven.IS_WINDOWS and sys.version_info[0] == 3 and sys.version_info[1] == 6:
    subprocess._cleanup = lambda: None  # type: ignore # pylint: disable=protected-access


# https://github.com/dagster-io/dagster/pull/10343
@pytest.fixture(autouse=True)
def mock_tqdm(monkeypatch):
    class MockTqdm:
        def __init__(self, iterable=None, **_kwargs):
            self._iterable = iterable

        def __iter__(self):
            for obj in self._iterable:
                yield obj

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return

        def update(self, n=1):
            pass

    # tqdm (may) sporadically crash during tests, so mock it out
    monkeypatch.setattr("dagster._core.storage.event_log.sqlite.sqlite_event_log.tqdm", MockTqdm)
    monkeypatch.setattr("dagster._core.storage.event_log.migration.tqdm", MockTqdm)
    monkeypatch.setattr("dagster._core.storage.runs.migration.tqdm", MockTqdm)
    monkeypatch.setattr("dagster._core.storage.schedules.migration.tqdm", MockTqdm)
    monkeypatch.setattr("dagster._cli.debug.tqdm", MockTqdm)
    monkeypatch.setattr("dagster._cli.run.tqdm", MockTqdm)

    yield

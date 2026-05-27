"""Pytest plugin providing the ``@pytest.mark.quarantined`` mark.

Quarantining lets you pull a chronically flaky test out of the suite it
currently runs in without deleting it. The same test can then be picked up by
a dedicated "flakes" meta-suite that aggregates quarantined tests from many
constituent suites.

Behavior:
    - When ``RUN_QUARANTINED`` is unset (the normal case), any test carrying
      ``@pytest.mark.quarantined`` is skipped, so it vanishes from whatever
      suite it lives in.
    - When ``RUN_QUARANTINED`` is set to a truthy value (``1``, ``true``,
      ``yes``; case-insensitive), the inverse applies: every test *not*
      carrying the mark is deselected, so the invocation runs only quarantined
      tests.

The plugin is registered by the repo-root ``conftest.py`` (via ``pytest_plugins``)
rather than a ``pytest11`` entry point, so it loads for internal pytest runs that
install dagster from source but does not auto-load for downstream users who
``pip install dagster`` and run their own suite.
"""

import os

import pytest

ENV_VAR = "RUN_QUARANTINED"
MARK_NAME = "quarantined"
_TRUTHY = frozenset({"1", "true", "yes"})


def _run_quarantined_mode() -> bool:
    return os.environ.get(ENV_VAR, "").strip().lower() in _TRUTHY


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        f"{MARK_NAME}: mark test as quarantined; skipped unless "
        f"{ENV_VAR}=1, in which case only quarantined tests run.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_quarantined = _run_quarantined_mode()
    if run_quarantined:
        selected: list[pytest.Item] = []
        deselected: list[pytest.Item] = []
        for item in items:
            if item.get_closest_marker(MARK_NAME) is not None:
                selected.append(item)
            else:
                deselected.append(item)
        if deselected:
            config.hook.pytest_deselected(items=deselected)
            items[:] = selected
    else:
        skip_mark = pytest.mark.skip(reason=f"quarantined (set {ENV_VAR}=1 to run)")
        for item in items:
            if item.get_closest_marker(MARK_NAME) is not None:
                item.add_marker(skip_mark)

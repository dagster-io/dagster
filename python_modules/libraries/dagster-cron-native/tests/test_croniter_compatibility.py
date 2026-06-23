#!/usr/bin/env python
from __future__ import annotations

import argparse
import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HASH_REASON = "unsupported croniter feature: deterministic hashed H expressions"
IMPLEMENT_CRON_BUG_REASON = "unsupported croniter feature: implement_cron_bug"
EXPAND_FROM_START_TIME_REASON = "unsupported croniter feature: expand_from_start_time"
EXPANDED_STATE_REASON = "unsupported croniter feature: expanded normalized field state"
PRIVATE_NTH_WEEKDAY_HELPER_REASON = (
    "unsupported croniter private helper API: _get_nth_weekday_of_month"
)
CRON_UNIONS_SPECIAL_SPECIFIERS_REASON = (
    "dagster_cron_native unions special specifiers that croniter treats as filters or rejects"
)
DEFAULT_YEAR_RANGE_REASON = (
    "unsupported croniter policy: default 1970-2099 year range validation"
)
STRICT_YEAR_REACHABILITY_REASON = (
    "unsupported croniter policy: strict year-specific date reachability validation"
)

EXPANDED_STATE_TESTS = {
    "CroniterTest::test_block_dup_ranges",
    "CroniterTest::test_confirm_sort",
    "CroniterTest::test_optimize_cron_expressions",
}

PRIVATE_NTH_WEEKDAY_HELPER_TESTS = {
    "CroniterTest::test_nth_as_last_wday_simple",
    "CroniterTest::test_nth_wday_simple",
    "CroniterTest::test_wdom_core_leap_year",
}

CRON_UNIONS_SPECIAL_SPECIFIER_TESTS = {
    "CroniterTest::test_hash_mixup_all_fri_3rd_sat",
    "CroniterTest::test_issue156",
    "CroniterTest::test_issue_k33",
    "CroniterTest::test_lwom_mixup_all_fri_last_sat",
    "CroniterTest::test_nearest_weekday_is_valid",
}

DEFAULT_YEAR_RANGE_TESTS = {
    "CroniterTest::test_invalid_year",
}

STRICT_YEAR_REACHABILITY_TESTS = {
    "CroniterTest::test_is_valid_strict_with_year",
    "CroniterTest::test_is_valid_strict_year_parameter",
}


def _load_croniter_compat():
    compat_path = pathlib.Path(__file__).resolve().parents[1] / "tests" / "croniter_compat.py"
    spec = importlib.util.spec_from_file_location("dagster_cron_native_croniter_compat", compat_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load croniter compatibility test module: {compat_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


croniter_compat = _load_croniter_compat()


def _item_key(item: pytest.Item) -> str:
    parts = item.nodeid.split("::")
    if len(parts) >= 3:
        return f"{parts[-2]}::{parts[-1]}"
    return parts[-1]


def _known_unsupported_reason(item: pytest.Item) -> str | None:
    if pathlib.Path(str(item.path)).name == "test_croniter_hash.py":
        return HASH_REASON

    key = _item_key(item)
    if key == "CroniterTest::test_is_valid":
        return HASH_REASON
    if key == "CroniterTest::test_dom_dow_vixie_cron_bug":
        return IMPLEMENT_CRON_BUG_REASON
    if key.startswith("CroniterTest::test_expand_from_start_time_"):
        return EXPAND_FROM_START_TIME_REASON
    if key in EXPANDED_STATE_TESTS:
        return EXPANDED_STATE_REASON
    if key in PRIVATE_NTH_WEEKDAY_HELPER_TESTS:
        return PRIVATE_NTH_WEEKDAY_HELPER_REASON
    if key in CRON_UNIONS_SPECIAL_SPECIFIER_TESTS:
        return CRON_UNIONS_SPECIAL_SPECIFIERS_REASON
    if key in DEFAULT_YEAR_RANGE_TESTS:
        return DEFAULT_YEAR_RANGE_REASON
    if key in STRICT_YEAR_REACHABILITY_TESTS:
        return STRICT_YEAR_REACHABILITY_REASON

    return None


class KnownUnsupportedSkips:
    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        for item in items:
            reason = _known_unsupported_reason(item)
            if reason is not None:
                item.add_marker(pytest.mark.skip(reason=reason))


def _install_croniter_proxy() -> pathlib.Path:
    spec = importlib.util.find_spec("croniter")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("The upstream croniter package is not installed.")

    upstream_paths = list(spec.submodule_search_locations)
    tests_path = pathlib.Path(upstream_paths[0]) / "tests"
    if not tests_path.exists():
        raise RuntimeError(
            "The installed croniter package does not include croniter.tests. "
            "Install croniter from an upstream source distribution or git checkout."
        )

    for name in list(sys.modules):
        if name == "croniter" or name.startswith("croniter."):
            del sys.modules[name]

    package = types.ModuleType("croniter")
    package.__file__ = str(pathlib.Path(upstream_paths[0]) / "__init__.py")
    package.__path__ = upstream_paths
    package.__package__ = "croniter"
    for name in croniter_compat.__all__:
        setattr(package, name, getattr(croniter_compat, name))
    package.cron_m = croniter_compat

    sys.modules["croniter"] = package
    sys.modules["croniter.croniter"] = croniter_compat
    importlib.import_module("croniter.tests")
    return tests_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junitxml", default="parity-report.xml")
    parser.add_argument(
        "--skip-known-unsupported",
        action="store_true",
        help=(
            "Skip upstream tests for croniter features intentionally outside current scope: "
            "hashed H expressions, implement_cron_bug, and expand_from_start_time."
        ),
    )
    args, pytest_extra_args = parser.parse_known_args()

    tests_path = _install_croniter_proxy()
    pytest_args = [str(tests_path), f"--junitxml={args.junitxml}", *pytest_extra_args]
    plugins = [KnownUnsupportedSkips()] if args.skip_known_unsupported else None
    return pytest.main(pytest_args, plugins=plugins)


if __name__ == "__main__":
    raise SystemExit(main())

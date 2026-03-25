import logging
import os
from collections.abc import Callable, Sequence
from pathlib import Path

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.utils import oss_path


def get_python_package_step_skip_reason(
    directory: str | Path,
    name: str | None = None,
    force_run_fn: Callable[[BuildkiteContext], bool] | None = None,
    skip_run_fn: Callable[[BuildkiteContext], str | None] | None = None,
    *,
    ctx: BuildkiteContext,
) -> str | None:
    """Provides a message if this package's steps should be skipped on this run,
    and no message if the package's steps should be run.
    """
    if name is None:
        name = os.path.basename(directory)

    if ctx.config.no_skip:
        logging.info(f"Building {name} because NO_SKIP set")
        return None
    if force_run_fn and force_run_fn(ctx):
        return None
    if skip_run_fn and skip_run_fn(ctx):
        return skip_run_fn(ctx)

    # Take account of feature_branch changes _after_ skip_run_fn so that skip_run_fn
    # takes precedent. This way, integration tests can run on branch but won't be
    # forced to run on every master commit.
    if not ctx.is_feature_branch:
        logging.info(f"Building {name} we're not on a feature branch")
        return None

    # Check if this package itself has changed (including test-only changes).
    if ctx.has_package_test_changes(name):
        logging.info(f"Building {name} because it has changed")
        return None

    # Check if any of this package's in-repo dependencies have changed
    # (non-test changes only — a test-only change in a dependency shouldn't
    # force downstream packages to re-test).
    if ctx.has_package_dependency_changes(name):
        logging.info(f"Building {name} because a dependency has changed")
        return None

    return "Package unaffected by these changes"


def get_general_python_step_skip_reason(
    ctx: BuildkiteContext, other_paths: Sequence[str] | None = None
) -> str | None:
    if ctx.config.no_skip:
        return None
    elif not ctx.is_feature_branch:
        return None
    elif ctx.has_python_changes():
        return None
    elif other_paths and any(
        oss_path(path) in changed_path.parents
        for path in other_paths
        for changed_path in ctx.changed_files
    ):
        return None
    return "No python changes"

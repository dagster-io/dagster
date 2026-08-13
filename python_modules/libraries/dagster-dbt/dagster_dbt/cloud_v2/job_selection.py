"""dbt-style selection DSL for filtering which dbt Cloud jobs get mirrored.

Users often only want *some* Cloud jobs surfaced in Dagster — e.g. only
production deploy jobs, or everything except CI jobs. This module provides a
small selection DSL that mirrors dbt's ``--select`` / ``--exclude`` semantics
adapted to what a Cloud job actually has: name, id, and job_type.

Syntax
------

A selection string is a space-separated list of selectors. A job matches the
selection if ANY selector matches it (union / OR semantics, like dbt).

Selector forms:

- ``type:<value>`` — matches ``job.job_type`` exactly (e.g. ``type:ci``,
  ``type:deploy``, ``type:merge``, ``type:scheduled``, ``type:other``).
- ``name:<glob>`` — fnmatch glob against ``job.name`` (case-sensitive).
- ``id:<int>`` — exact ``job.id`` match.
- ``<glob>`` — bare token = shorthand for ``name:<glob>``.
- ``*`` (or empty selector) — matches every job.

The include list defaults to "everything"; the exclude list defaults to
"nothing." Exclude is applied AFTER include.
"""

import fnmatch
from collections.abc import Iterable

from dagster_dbt.cloud_v2.types import DbtCloudJob


def _match_single_selector(cloud_job: DbtCloudJob, selector: str) -> bool:
    """Match a single selector token against one Cloud job."""
    selector = selector.strip()
    if not selector or selector == "*":
        return True

    if ":" in selector:
        kind, _, value = selector.partition(":")
        kind = kind.strip()
        value = value.strip()
        if kind == "type":
            return (cloud_job.job_type or "") == value
        if kind == "name":
            return fnmatch.fnmatchcase(cloud_job.name or "", value)
        if kind == "id":
            try:
                return cloud_job.id == int(value)
            except ValueError:
                return False
        # Unknown selector kind: no match (safer than silently matching all).
        return False

    # Bare token = name glob shorthand.
    return fnmatch.fnmatchcase(cloud_job.name or "", selector)


def matches_selection(cloud_job: DbtCloudJob, selection: str | None) -> bool:
    """Match ``cloud_job`` against a whole selection string.

    Returns True if ``cloud_job`` matches ANY selector in the space-separated
    ``selection`` string. ``None`` or empty string means "match everything."
    """
    if not selection or not selection.strip():
        return True
    tokens = selection.split()
    return any(_match_single_selector(cloud_job, tok) for tok in tokens)


def apply_selection(
    cloud_jobs: Iterable[DbtCloudJob],
    include: str | None,
    exclude: str | None,
) -> list[DbtCloudJob]:
    """Filter ``cloud_jobs`` by ``include`` then ``exclude`` (both selection strings).

    - ``include=None`` or empty: include every job.
    - ``exclude=None`` or empty: exclude nothing.
    - Exclude wins: a job matching both include and exclude is dropped.
    """
    result: list[DbtCloudJob] = []
    for cloud_job in cloud_jobs:
        if not matches_selection(cloud_job, include):
            continue
        if exclude and matches_selection(cloud_job, exclude):
            continue
        result.append(cloud_job)
    return result

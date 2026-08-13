"""Tests for the dbt-style ``mirror_jobs_select`` / ``mirror_jobs_exclude`` DSL.

Users often only want *some* of their dbt Cloud jobs mirrored — e.g. only prod
deploy jobs, or everything except CI jobs. The DSL is a small subset of dbt's
``--select`` semantics adapted to what a Cloud job actually has: name, id, and
job_type. These tests exercise every selector form + the include/exclude
composition rules that the component and sensor both rely on.
"""

from dagster_dbt.cloud_v2.job_selection import (
    _match_single_selector,
    apply_selection,
    matches_selection,
)
from dagster_dbt.cloud_v2.types import DbtCloudJob


def _job(
    id: int = 1,
    name: str | None = "Prod Build",
    job_type: str | None = "deploy",
) -> DbtCloudJob:
    return DbtCloudJob(
        id=id,
        account_id=1,
        project_id=1,
        environment_id=1,
        name=name,
        job_type=job_type,
    )


def test_bare_selector_glob_matches_name():
    """A bare token (no ``kind:``) is shorthand for ``name:<glob>`` — dbt-like."""
    job = _job(name="Prod Build")
    assert _match_single_selector(job, "Prod*")
    assert not _match_single_selector(job, "Nightly*")


def test_name_selector_uses_fnmatch_glob():
    """``name:<glob>`` uses fnmatch (case-sensitive) so users get standard
    ``*`` / ``?`` / ``[abc]`` glob semantics.
    """
    job = _job(name="Prod_Deploy_v2")
    assert _match_single_selector(job, "name:Prod_*")
    assert _match_single_selector(job, "name:*_v2")
    assert _match_single_selector(job, "name:Prod_Deploy_v?")
    assert _match_single_selector(job, "name:*")
    assert not _match_single_selector(job, "name:prod_*")  # case-sensitive


def test_type_selector_exact_match():
    """``type:<value>`` matches ``job_type`` exactly. Used for ``type:ci`` /
    ``type:deploy`` / etc.
    """
    ci_job = _job(job_type="ci")
    assert _match_single_selector(ci_job, "type:ci")
    assert not _match_single_selector(ci_job, "type:deploy")
    # Job with no type never matches a type selector.
    assert not _match_single_selector(_job(job_type=None), "type:ci")


def test_id_selector_int_match():
    """``id:<int>`` matches exact job id. Useful for pinning to a specific job even
    when its name changes upstream in dbt Cloud.
    """
    job = _job(id=12345)
    assert _match_single_selector(job, "id:12345")
    assert not _match_single_selector(job, "id:99999")


def test_id_selector_non_int_value_is_no_match():
    """A malformed ``id:<not-a-number>`` selector does NOT match anything (safer
    than raising or silently matching all).
    """
    assert not _match_single_selector(_job(id=1), "id:not-a-number")


def test_unknown_selector_kind_is_no_match():
    """Unknown selector kinds (e.g. ``tag:foo`` — dbt Cloud jobs don't have arbitrary
    tags) match nothing, so a typo can't silently include jobs the user didn't want.
    """
    assert not _match_single_selector(_job(), "tag:whatever")
    assert not _match_single_selector(_job(), "resource_type:model")


def test_star_and_empty_selector_match_everything():
    """A bare ``*`` or empty string matches any job — used as an explicit "all"."""
    assert _match_single_selector(_job(), "*")
    assert _match_single_selector(_job(), "")
    assert _match_single_selector(_job(), "  ")


def test_matches_selection_space_separated_is_union():
    """Space-separated selectors are OR'd (union), same as dbt's `--select`
    semantics — a job matches if ANY selector matches.
    """
    deploy_job = _job(job_type="deploy")
    ci_job = _job(job_type="ci")
    other_job = _job(job_type="other")
    selection = "type:deploy type:ci"
    assert matches_selection(deploy_job, selection)
    assert matches_selection(ci_job, selection)
    assert not matches_selection(other_job, selection)


def test_matches_selection_none_matches_everything():
    """Empty selection = match everything.

    A ``None`` or empty selection string is the "match everything" default. This is
    what lets ``mirror_jobs_select=None`` mean "mirror every user-defined job."
    """
    assert matches_selection(_job(), None)
    assert matches_selection(_job(), "")
    assert matches_selection(_job(), "   ")


def test_apply_selection_include_only_filters_positively():
    """When only ``include`` is set, jobs matching it are kept; the rest dropped."""
    jobs = [
        _job(id=1, name="Prod Build", job_type="deploy"),
        _job(id=2, name="CI Build", job_type="ci"),
        _job(id=3, name="Nightly", job_type="scheduled"),
    ]
    result = apply_selection(jobs, include="type:deploy", exclude=None)
    assert [j.id for j in result] == [1]


def test_apply_selection_exclude_only_filters_negatively():
    """When only ``exclude`` is set, all jobs are kept EXCEPT those matching exclude."""
    jobs = [
        _job(id=1, name="Prod Build", job_type="deploy"),
        _job(id=2, name="CI Build", job_type="ci"),
        _job(id=3, name="Nightly", job_type="scheduled"),
    ]
    result = apply_selection(jobs, include=None, exclude="type:ci")
    assert [j.id for j in result] == [1, 3]


def test_apply_selection_exclude_wins_over_include():
    """A job matching BOTH include and exclude is dropped — exclusion wins.

    Rationale: dbt's own ``--select ... --exclude ...`` has the same semantics —
    exclude is a hard subtraction, not a preference.
    """
    jobs = [
        _job(id=1, name="Prod Build", job_type="deploy"),
        _job(id=2, name="Prod Deploy", job_type="deploy"),
    ]
    result = apply_selection(jobs, include="type:deploy", exclude="name:Prod?Deploy")
    assert [j.id for j in result] == [1]


def test_apply_selection_include_and_exclude_together():
    """End-to-end composition: `include=type:deploy type:merge` + `exclude=name:*_staging`
    keeps prod deploy/merge, drops the staging one.
    """
    jobs = [
        _job(id=1, name="Prod Deploy", job_type="deploy"),
        _job(id=2, name="Prod Merge", job_type="merge"),
        _job(id=3, name="Prod Deploy_staging", job_type="deploy"),
        _job(id=4, name="Nightly", job_type="scheduled"),
    ]
    result = apply_selection(jobs, include="type:deploy type:merge", exclude="name:*_staging")
    assert [j.id for j in result] == [1, 2]


def test_apply_selection_id_selector_works_end_to_end():
    """`id:<int>` gets picked up by the same include/exclude machinery — useful for
    pinning to a specific job even when its name might change in dbt Cloud.
    """
    jobs = [_job(id=1), _job(id=2), _job(id=3)]
    result = apply_selection(jobs, include="id:1 id:3", exclude=None)
    assert [j.id for j in result] == [1, 3]


def test_apply_selection_empty_input_returns_empty():
    """No jobs in = no jobs out (trivial but worth pinning so no crashes on
    workspaces with zero user-defined jobs).
    """
    assert apply_selection([], include="type:deploy", exclude="type:ci") == []

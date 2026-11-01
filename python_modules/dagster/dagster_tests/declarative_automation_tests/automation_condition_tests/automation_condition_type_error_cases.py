"""Type-level test cases for the automation condition APIs; the counterpart of
test_type_errors.py, which runs real type checkers over a copy of this file.

This is real, checked-in code (rather than a string embedded in the test) so that
editors, refactoring tools, and ruff see it. The deliberately-erroneous lines are
masked from repo-wide type checking by trailing `# type: ignore` markers, which the
test strips before invoking the checkers, so that it can assert the errors occur.
Each masked line carries `# assert-type-error-<checker>` comments declaring the
expected error. The scheme is self-enforcing: a missing marker fails the repo-wide
type check, and a marker without a matching error fails the test.

This module is never imported; it only ever type-checked.
"""

import dagster as dg


@dg.asset
def my_asset() -> None: ...


# --- negative cases: asset-scoped conditions cannot be applied to a job directly ---

job_bare_eager = dg.define_asset_job(
    "job_bare_eager",
    selection=[my_asset],
    # assert-type-error-ty: 'Expected `AutomationCondition\[AssetJobKey\] \| None`'
    # assert-type-error-pyright: 'cannot be assigned to parameter "automation_condition" of type "AutomationCondition\[AssetJobKey\] \| None"'
    automation_condition=dg.AutomationCondition.eager(),  # type: ignore
)

job_bare_missing = dg.define_asset_job(
    "job_bare_missing",
    selection=[my_asset],
    # assert-type-error-ty: 'Expected `AutomationCondition\[AssetJobKey\] \| None`'
    # assert-type-error-pyright: 'cannot be assigned to parameter "automation_condition" of type "AutomationCondition\[AssetJobKey\] \| None"'
    automation_condition=dg.AutomationCondition.missing(),  # type: ignore
)

job_bare_on_cron = dg.define_asset_job(
    "job_bare_on_cron",
    selection=[my_asset],
    # assert-type-error-ty: 'Expected `AutomationCondition\[AssetJobKey\] \| None`'
    # assert-type-error-pyright: 'cannot be assigned to parameter "automation_condition" of type "AutomationCondition\[AssetJobKey\] \| None"'
    automation_condition=dg.AutomationCondition.on_cron("@daily"),  # type: ignore
)

# every factory must carry an explicit key type: an unparameterized return type means
# "AutomationCondition[Any]", which silently passes this check
job_bare_in_progress = dg.define_asset_job(
    "job_bare_in_progress",
    selection=[my_asset],
    # assert-type-error-ty: 'Expected `AutomationCondition\[AssetJobKey\] \| None`'
    # assert-type-error-pyright: 'cannot be assigned to parameter "automation_condition" of type "AutomationCondition\[AssetJobKey\] \| None"'
    automation_condition=dg.AutomationCondition.in_progress(),  # type: ignore
)

job_bare_any_deps_updated = dg.define_asset_job(
    "job_bare_any_deps_updated",
    selection=[my_asset],
    # assert-type-error-ty: 'Expected `AutomationCondition\[AssetJobKey\] \| None`'
    # assert-type-error-pyright: 'cannot be assigned to parameter "automation_condition" of type "AutomationCondition\[AssetJobKey\] \| None"'
    automation_condition=dg.AutomationCondition.any_deps_updated(),  # type: ignore
)


# --- negative cases: job-scoped and asset-scoped conditions cannot be combined with a
# boolean operator (both sides of `&`/`|` are evaluated against the same target key);
# cross-scope composition goes through any/all_job_root_assets_match instead ---

job_scoped = dg.AutomationCondition.any_job_root_assets_match(dg.AutomationCondition.missing())

# assert-type-error-ty: 'Operator `&` is not supported'
# assert-type-error-pyright: 'Operator "&" not supported'
bad_and = job_scoped & dg.AutomationCondition.eager()  # type: ignore

# assert-type-error-ty: 'Operator `\|` is not supported'
# assert-type-error-pyright: 'Operator "\|" not supported'
bad_or = dg.AutomationCondition.eager() | job_scoped  # type: ignore


# --- negative case: a job-scoped condition cannot be applied to an asset ---


@dg.asset(
    # assert-type-error-ty: 'found `JobRootAssetsAutomationCondition`'
    # assert-type-error-pyright: 'Argument of type "JobRootAssetsAutomationCondition" cannot be assigned'
    automation_condition=dg.AutomationCondition.any_job_root_assets_match(  # type: ignore
        dg.AutomationCondition.eager()
    )
)
def asset_with_job_condition() -> None: ...


# --- positive cases: everything below must typecheck with NO errors ---

# wrapping an asset-scoped condition makes it job-scoped
job_wrapped = dg.define_asset_job(
    "job_wrapped",
    selection=[my_asset],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)

# compositions of job-scoped conditions are job-scoped
job_composed = dg.define_asset_job(
    "job_composed",
    selection=[my_asset],
    automation_condition=(
        dg.AutomationCondition.any_job_root_assets_match(dg.AutomationCondition.missing())
        & dg.AutomationCondition.cron_tick_passed("@daily")
    ),
)


# asset-scoped conditions still apply to assets...
@dg.asset(automation_condition=dg.AutomationCondition.eager())
def asset_with_condition() -> None: ...


# ...including check-aggregating conditions
@dg.asset(
    automation_condition=dg.AutomationCondition.any_checks_match(dg.AutomationCondition.missing())
)
def asset_with_checks_condition() -> None: ...


# ...and to asset checks
@dg.asset_check(asset=my_asset, automation_condition=dg.AutomationCondition.on_cron("@daily"))
def check_with_condition() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


# entity matchers accept asset-scoped conditions
asset_matches_condition = dg.AutomationCondition.asset_matches(
    "my_asset", dg.AutomationCondition.missing()
)

# deps matchers accept asset-scoped conditions
deps_condition = dg.AutomationCondition.any_deps_match(dg.AutomationCondition.missing())

# conditions of different (compatible) scopes can be composed; this is the composition
# from the AutomationCondition class docstring
new_code_version = dg.AutomationCondition.code_version_changed().since(
    dg.AutomationCondition.newly_requested()
)
mixed_scope = dg.AutomationCondition.eager() & ~dg.AutomationCondition.code_version_changed()


# a condition stored once can be reused on both assets and checks
SHARED_POLICY = dg.AutomationCondition.eager() & ~dg.AutomationCondition.in_progress()


@dg.asset(automation_condition=SHARED_POLICY)
def asset_with_shared_policy() -> None: ...


@dg.asset_check(asset=my_asset, automation_condition=SHARED_POLICY)
def check_with_shared_policy() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


# scope-agnostic conditions (no reference to asset state) type-check at job scope; a bare
# one is rejected at runtime by JobDefinition, which requires anchoring to the job's root
# assets, but that rule cannot be expressed statically
job_bare_cron = dg.define_asset_job(
    "job_bare_cron",
    selection=[my_asset],
    automation_condition=dg.AutomationCondition.cron_tick_passed("@daily"),
)

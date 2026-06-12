import logging
import re
import shlex
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias, cast

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    ResourceRequests,
    StepBuilderMutator,
)
from buildkite_shared.step_builders.group_step_builder import (
    GroupLeafStepConfiguration,
    GroupStepBuilder,
)
from buildkite_shared.step_builders.slug import slugify_label
from buildkite_shared.step_builders.step_builder import (
    StepConfiguration,
    TopLevelStepConfiguration,
    is_command_step,
)
from buildkite_shared.tox import ToxFactor, ToxImage, build_tox_step
from buildkite_shared.utils import oss_path

PytestExtraCommandsFunction: TypeAlias = Callable[
    [AvailablePythonVersion, ToxFactor | None], list[str]
]
PytestDependenciesFunction: TypeAlias = Callable[
    [AvailablePythonVersion, ToxFactor | None], list[str]
]
UnsupportedVersionsFunction: TypeAlias = Callable[[ToxFactor | None], list[AvailablePythonVersion]]

# https://github.com/buildkite/emojis#emoji-reference
_PACKAGE_TYPE_TO_EMOJI_MAP: dict[str, str] = {
    "core": ":dagster:",
    "example": ":large_blue_diamond:",
    "extension": ":electric_plug:",
    "infrastructure": ":gear:",
    "unknown": ":grey_question:",
}

_CORE_PACKAGES = [
    oss_path("python_modules/dagster"),
    oss_path("python_modules/dagit"),
    oss_path("python_modules/dagster-graphql"),
    oss_path("js_modules"),
]

_INFRASTRUCTURE_PACKAGES = [
    oss_path(".buildkite/dagster-buildkite"),
    oss_path("python_modules/automation"),
    oss_path("python_modules/dagster-test"),
]


def infer_package_type(directory: str | Path) -> str:
    """Infer a package type from an OSS-conventional directory layout.

    Returns "core", "example", "extension", "infrastructure", or "unknown".
    Internal packages that don't sit under any of these roots get "unknown",
    which is fine — internal call sites typically pass `label_emojis` to bypass
    the package-type emoji lookup entirely.
    """
    directory = Path(directory)
    if directory in _CORE_PACKAGES:
        return "core"
    if oss_path("examples") in directory.parents or directory == oss_path("examples"):
        return "example"
    if oss_path("python_modules/libraries") in directory.parents:
        return "extension"
    if directory in _INFRASTRUCTURE_PACKAGES or oss_path("integration_tests") in (
        directory,
        *directory.parents,
    ):
        return "infrastructure"
    return "unknown"


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
        name = Path(directory).name

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


@dataclass
class PackageSpec:
    """Spec for testing a Dagster Python package using tox.

    A PackageSpec describes one package's CI configuration. `build_steps(ctx)`
    expands it into one or more `CommandStep`s (and an optional wrapping
    GroupStep) by taking the cross-product of supported python versions,
    `pytest_tox_factors`, and `splits`.

    There are two ways to control which python versions get steps:

      * Default: the python versions returned by
        `AvailablePythonVersion.get_pytest_defaults(ctx)`, minus
        `unsupported_python_versions`. This is the OSS pattern.
      * Explicit: set `python_versions` to a fixed list. This is the
        internal pattern, where most packages run on exactly one
        python version (the "cloud" version).

    Image selection:
      * `image="test"` (default): `.on_test_image(python_version, env=env_vars)`.
      * `image="integration"`: `.on_integration_image(env=env_vars, ecr_account_ids=ecr_account_ids)`.
      * `image="integration_slim"`: `.on_integration_slim_image(env=env_vars)`.

    Group wrapping: `is_group=None` (default) wraps in a GroupStep only when
    there are 2+ resulting steps. `is_group=True/False` forces the behavior.

    Internal-only knobs (default no-op for OSS):
      * `mutator`: callback that receives the `CommandStepBuilder` before
        `.build()`.
      * `command_wrapper`: callable that wraps the rendered tox command (e.g.
        for buildevents/Honeycomb instrumentation).
      * `extra_install_commands`: prepended to the rendered commands list
        before `pytest_extra_cmds`. Used for things like `uv venv` setup.
      * `skippable=False`: never skip this package, even if change-detection
        says nothing changed.
    """

    directory: str | Path
    name: str | None = None

    # Labeling. If `label_emojis` is set it wins. Otherwise the emoji is
    # derived from `package_type` via the package-type emoji map (OSS pattern).
    package_type: str | None = None
    label_emojis: list[str] | None = None

    # Tox config
    pytest_tox_factors: list[ToxFactor] | None = None
    splits: int = 1
    tox_file: str | None = None

    # Python versions. If `python_versions` is set, it's used directly
    # (internal pattern). Otherwise the default pytest set is used, minus
    # `unsupported_python_versions` (OSS pattern).
    unsupported_python_versions: (
        list[AvailablePythonVersion] | UnsupportedVersionsFunction | None
    ) = None
    python_versions: list[AvailablePythonVersion] | None = None

    # Per-step config
    timeout_in_minutes: int | None = None
    queue: BuildkiteQueue | None = None
    resources: ResourceRequests | None = None
    env_vars: list[str] | None = None

    # Pre/post commands
    pytest_extra_cmds: list[str] | PytestExtraCommandsFunction | None = None
    pytest_step_dependencies: list[str] | PytestDependenciesFunction | None = None
    extra_install_commands: list[str] | None = None
    # Commands that run AFTER `cd <directory>` but BEFORE the tox invocation.
    # Use this for commands that depend on cwd (e.g. `export X=$(pwd)/foo`);
    # `pytest_extra_cmds` runs BEFORE cd.
    post_cd_extra_cmds: list[str] | PytestExtraCommandsFunction | None = None

    # Skip control
    force_run_fn: Callable[[BuildkiteContext], bool] | None = None
    skip_run_fn: Callable[[BuildkiteContext], str | None] | None = None
    skippable: bool = True
    run_pytest: bool = True

    # Image / docker
    image: ToxImage = "test"
    with_docker: bool = True
    ecr_passthru: bool = False
    ecr_account_ids: list[str | None] | None = None

    # Group wrapping
    is_group: bool | None = None

    # Internal-only escape hatches
    mutator: StepBuilderMutator | None = None
    command_wrapper: Callable[[str], str] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            self.name = Path(self.directory).name
        if not self.package_type:
            self.package_type = infer_package_type(self.directory)
        self._should_skip: bool | None = None
        self._skip_reason: str | None = None

    def get_skip_reason(self, ctx: BuildkiteContext) -> str | None:
        if not self.skippable:
            return None
        if self._should_skip is not None:
            return self._skip_reason
        # Pass directory only — self.name is a display label; the change-detection
        # lookup uses the directory basename (matches OSS PackageSpec behavior).
        self._skip_reason = get_python_package_step_skip_reason(
            self.directory,
            force_run_fn=self.force_run_fn,
            skip_run_fn=self.skip_run_fn,
            ctx=ctx,
        )
        self._should_skip = self._skip_reason is not None
        return self._skip_reason

    def _resolve_emoji(self) -> str:
        if self.label_emojis:
            return self.label_emojis[0]
        return _PACKAGE_TYPE_TO_EMOJI_MAP.get(self.package_type or "unknown", ":grey_question:")

    def _section_header(self, tox_env: str) -> str:
        # Internal-style (explicit label_emojis): plain text, unquoted.
        # OSS-style: ANSI-colored "--- :emoji: Running tox env: <env>", quoted.
        if self.label_emojis is not None:
            return f"--- Running tox env {tox_env}"
        emoji = self._resolve_emoji()
        # \033[0;32m is green; matches make_buildkite_section_header().
        return shlex.quote(f"--- \\033[0;32m{emoji} Running tox env: {tox_env}\\033[0m")

    def _pytest_python_versions(
        self, ctx: BuildkiteContext, factor: ToxFactor | None
    ) -> list[AvailablePythonVersion]:
        if self.python_versions is not None:
            return self.python_versions
        default_python_versions = AvailablePythonVersion.get_pytest_defaults(ctx)
        if callable(self.unsupported_python_versions):
            unsupported = self.unsupported_python_versions(factor)
        else:
            unsupported = self.unsupported_python_versions or []
        supported = [v for v in AvailablePythonVersion.get_all() if v not in unsupported]
        pytest_versions = [
            AvailablePythonVersion(v)
            for v in sorted(
                set(e.value for e in default_python_versions) - set(e.value for e in unsupported)
            )
        ]
        # Fall back to highest supported when no defaults match.
        return pytest_versions or [supported[-1]]

    def build_steps(self, ctx: BuildkiteContext) -> list[TopLevelStepConfiguration]:
        base_name = self.name or Path(self.directory).name
        steps: list[GroupLeafStepConfiguration] = []

        if self.run_pytest:
            tox_factors: Sequence[ToxFactor | None] = self.pytest_tox_factors or [None]
            for factor in tox_factors:
                for py_version in self._pytest_python_versions(ctx, factor):
                    self._append_steps_for_cell(
                        ctx=ctx,
                        base_name=base_name,
                        factor=factor,
                        py_version=py_version,
                        out=steps,
                    )

        # OSS-style: group label gets the package-type emoji. Internal-style
        # (`label_emojis` set explicitly): leaves carry the emoji, group label
        # doesn't get one — matches the historic internal `build_tox_steps`
        # behavior which never decorated the group label.
        group_emojis: list[str] | None = (
            None if self.label_emojis is not None else [self._resolve_emoji()]
        )
        force_group = self.is_group
        if force_group is True or (force_group is None and len(steps) >= 2):
            if not steps:
                return []
            return [GroupStepBuilder(slugify_label(base_name), group_emojis, steps=steps).build()]
        if force_group is False:
            # Return the leaves untouched. GroupLeafStepConfiguration is a
            # subset of TopLevelStepConfiguration but ty (and pyright) want
            # an explicit cast.
            return cast("list[TopLevelStepConfiguration]", list(steps))
        if len(steps) == 1:
            only_step = steps[0]
            if not is_command_step(only_step):
                raise ValueError("Expected only step to be a CommandStep")
            return cast("list[TopLevelStepConfiguration]", [only_step])
        return []

    def _append_steps_for_cell(
        self,
        *,
        ctx: BuildkiteContext,
        base_name: str,
        factor: ToxFactor | None,
        py_version: AvailablePythonVersion,
        out: list[GroupLeafStepConfiguration],
    ) -> None:
        version_factor = AvailablePythonVersion.to_tox_factor(py_version)
        if factor is None:
            tox_env = version_factor
            splits = self.splits
        else:
            tox_env = f"{version_factor}-{factor.factor}"
            splits = factor.splits

        if isinstance(self.pytest_extra_cmds, list):
            base_extra_pre = list(self.pytest_extra_cmds)
        elif callable(self.pytest_extra_cmds):
            base_extra_pre = self.pytest_extra_cmds(py_version, factor)
        else:
            base_extra_pre = []
        extra_pre = list(self.extra_install_commands or []) + base_extra_pre

        if isinstance(self.post_cd_extra_cmds, list):
            extra_post_cd: list[str] | None = list(self.post_cd_extra_cmds)
        elif callable(self.post_cd_extra_cmds):
            extra_post_cd = self.post_cd_extra_cmds(py_version, factor)
        else:
            extra_post_cd = None

        skip_reason = self.get_skip_reason(ctx)
        dependencies: list[str] | None
        if skip_reason:
            dependencies = None
        elif isinstance(self.pytest_step_dependencies, list):
            dependencies = list(self.pytest_step_dependencies) or None
        elif callable(self.pytest_step_dependencies):
            dependencies = self.pytest_step_dependencies(py_version, factor) or None
        else:
            dependencies = None

        factor_pytest_args = list(factor.pytest_args) if factor and factor.pytest_args else []
        label_suffix = f" {factor.label_suffix}" if factor and factor.label_suffix else ""
        resolved_image = factor.image if factor and factor.image else self.image

        # Per-factor durations file under a single `.test_durations/` directory
        # at the package root. pytest-split reads the file in normal mode and
        # writes it via --store-durations in refresh mode. The nested layout
        # keeps multi-factor packages from cluttering their root with one
        # `.test_durations-<factor>` file per tox factor. The unfactored case
        # uses the literal name `default` so the layout is uniform (directory
        # everywhere, no mix of file-or-directory). The id includes
        # label_suffix so two ToxFactors sharing a tox env but selecting
        # different test subsets (e.g. OSS dagster-dbt's `<deps>-core-main` x
        # [rest, test_resource, test_asset_checks, cli]) don't clobber each
        # other in refresh mode.
        if factor:
            durations_id = factor.factor
            if factor.label_suffix:
                durations_id = f"{durations_id}-{factor.label_suffix}"
        else:
            durations_id = "default"
        durations_file = f".test_durations/{durations_id}"

        # Refresh mode: for factors that fan out, collapse to a single
        # un-sharded run that writes a fresh durations file and uploads it
        # as an artifact. Non-split factors fall through to the normal
        # emit path — the caller's downstream filter
        # (`steps/refresh_durations.py:keep_refresh_steps_only`) drops them
        # by absence of `--store-durations` in the command. We don't return
        # an empty list here because some callers (e.g. OSS
        # `build_helm_steps`) assert on `len(pkg_steps) == 1`.
        if ctx.config.refresh_durations and splits > 1:
            # Refresh mode runs the full set of split tox suites unconditionally —
            # change-detection isn't meaningful when collecting timing data
            # against the current source tree, not validating a diff. Force the
            # step to emit by suppressing skip_reason locally; we don't change
            # `get_python_package_step_skip_reason` itself so external callers
            # (release-pipeline gating, app-cloud gating) keep their semantics.
            self._append_refresh_step(
                tox_env=tox_env,
                base_name=base_name,
                label_suffix=label_suffix,
                durations_file=durations_file,
                factor_pytest_args=factor_pytest_args,
                resolved_image=resolved_image,
                py_version=py_version,
                extra_pre=extra_pre,
                extra_post_cd=extra_post_cd,
                dependencies=dependencies,
                skip_reason=None,
                factor=factor,
                out=out,
            )
            return

        # Splitting uses the pytest-split plugin. To use `splits > 1` with a
        # package, `pytest-split` must be declared in that package's test
        # dependencies (e.g. the `test`/`tests` extra in its pyproject.toml).
        # Factors can opt out of duration-based balancing via `use_durations=False`
        # — pytest-split then falls back to count-based grouping. Useful when the
        # recorded `.test_durations` data is known to mislead (heavy fixtures,
        # near-zero recorded times for many tests, etc).
        use_durations = factor.use_durations if factor else True
        for split_index in range(1, splits + 1):
            if splits > 1:
                split_label = f"{base_name}{label_suffix} ({split_index}/{splits})"
                split_arg = f"--splits {splits} --group {split_index}"
                if use_durations:
                    split_arg = f"{split_arg} --durations-path {durations_file}"
                pytest_args: list[str] | None = [split_arg, *factor_pytest_args]
            else:
                split_label = f"{base_name}{label_suffix}"
                pytest_args = factor_pytest_args or None
            key = slugify_label(f"{split_label} {_tox_env_to_label_suffix(tox_env)}")
            out.append(
                build_tox_step(
                    self.directory,
                    tox_env,
                    key=key,
                    label_emojis=self.label_emojis or [self._resolve_emoji()],
                    timeout_in_minutes=self.timeout_in_minutes,
                    tox_file=self.tox_file,
                    extra_commands_pre=extra_pre,
                    extra_commands_post_cd=extra_post_cd,
                    env=self.env_vars,
                    image=resolved_image,
                    python_version=py_version if resolved_image == "test" else None,
                    ecr_account_ids=self.ecr_account_ids,
                    queue=(factor.queue if factor and factor.queue else self.queue),
                    depends_on=dependencies,
                    skip_reason=skip_reason,
                    pytest_args=pytest_args,
                    section_header=self._section_header(tox_env),
                    concurrency=factor.concurrency if factor else None,
                    concurrency_group=(factor.concurrency_group if factor else None),
                    resources=(
                        factor.resources
                        if factor and factor.resources is not None
                        else self.resources
                    ),
                    soft_fail=factor.soft_fail if factor else False,
                    with_docker=self.with_docker,
                    ecr_passthru=self.ecr_passthru,
                    command_wrapper=self.command_wrapper,
                    mutator=self.mutator,
                )
            )

    def _append_refresh_step(
        self,
        *,
        tox_env: str,
        base_name: str,
        label_suffix: str,
        durations_file: str,
        factor_pytest_args: list[str],
        resolved_image: ToxImage,
        py_version: AvailablePythonVersion,
        extra_pre: list[str],
        extra_post_cd: list[str] | None,
        dependencies: list[str] | None,
        skip_reason: str | None,
        factor: ToxFactor | None,
        out: list[GroupLeafStepConfiguration],
    ) -> None:
        split_label = f"{base_name}{label_suffix}"
        key = slugify_label(f"{split_label} {_tox_env_to_label_suffix(tox_env)}")
        pytest_args = [
            f"--store-durations --durations-path {durations_file}",
            *factor_pytest_args,
        ]
        # The tox command runs after `cd {directory}` so cwd is the package
        # directory. We `cd` back to the build checkout root before the upload
        # so the artifact is stored with its full repo-relative path —
        # otherwise multiple packages sharing a factor name (e.g. `-default`)
        # would all upload to the same basename and overwrite each other in
        # BK's artifact store. pytest-split's --store-durations is a
        # `pytest_sessionfinish` hook, so only a clean tox exit produces the
        # file; the upload runs unconditionally (see _refresh_wrapper) and
        # `buildkite-agent` exits non-zero when the file is missing, which is
        # the signal we want — the create-test-durations-pr step then sees no
        # artifact for that suite.
        artifact_path = f"{self.directory}/{durations_file}"
        upload_cmd = f'buildkite-agent artifact upload "{artifact_path}"'
        original_wrapper = self.command_wrapper

        def _refresh_wrapper(cmd: str) -> str:
            # Disable `set -e` around the block so a failing tox doesn't abort
            # before the upload runs (BK's `bash -e -c` would otherwise exit
            # at the failing subshell). Preserve the inner exit code via
            # $status so `soft_fail` still surfaces real test failures in BK
            # UI; the upload's own exit code is intentionally ignored.
            # `mkdir -p .test_durations` ensures the parent of `durations_file`
            # exists before pytest-split's --store-durations writes — pytest-
            # split uses a plain `open(path, "w")` and won't create parents.
            inner = original_wrapper(cmd) if original_wrapper else cmd
            return (
                f"mkdir -p .test_durations; set +e; {inner}; status=$?;"
                f' cd "$BUILDKITE_BUILD_CHECKOUT_PATH"; {upload_cmd}; exit $status'
            )

        out.append(
            build_tox_step(
                self.directory,
                tox_env,
                key=key,
                label_emojis=self.label_emojis or [self._resolve_emoji()],
                timeout_in_minutes=self.timeout_in_minutes,
                tox_file=self.tox_file,
                extra_commands_pre=extra_pre,
                extra_commands_post_cd=extra_post_cd,
                env=self.env_vars,
                image=resolved_image,
                python_version=py_version if resolved_image == "test" else None,
                ecr_account_ids=self.ecr_account_ids,
                queue=(factor.queue if factor and factor.queue else self.queue),
                depends_on=dependencies,
                skip_reason=skip_reason,
                pytest_args=pytest_args,
                section_header=self._section_header(tox_env),
                concurrency=factor.concurrency if factor else None,
                concurrency_group=(factor.concurrency_group if factor else None),
                resources=(
                    factor.resources if factor and factor.resources is not None else self.resources
                ),
                soft_fail=True,
                with_docker=self.with_docker,
                ecr_passthru=self.ecr_passthru,
                command_wrapper=_refresh_wrapper,
                mutator=self.mutator,
            )
        )


def build_steps_from_package_specs(
    package_specs: Sequence[PackageSpec],
    ctx: BuildkiteContext,
    *,
    package_type_order: Sequence[str] | None = None,
) -> list[StepConfiguration]:
    """Build steps for a list of PackageSpecs, sorted by package_type then name."""
    order = list(
        package_type_order or ["core", "extension", "example", "infrastructure", "unknown"]
    )

    def _sort_key(p: PackageSpec) -> str:
        pt = p.package_type or "unknown"
        idx = order.index(pt) if pt in order else len(order)
        return f"{idx} {p.name}"

    steps: list[StepConfiguration] = []
    for pkg in sorted(package_specs, key=_sort_key):
        steps += pkg.build_steps(ctx)
    return steps


def _tox_env_to_label_suffix(tox_env: str) -> str:
    py_version, _, factor = tox_env.partition("-")
    m = re.match(r"py(\d+)", py_version)
    if not m:
        return ""
    version_number = m[1]
    number_str = f"{version_number[0]}.{version_number[1:]}"
    if factor == "":
        return number_str
    return f"{factor} {number_str}"


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

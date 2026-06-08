"""CLI command group for monorepo sync operations."""

import json
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path

import click
from rich.console import Console

from automation.dagster_dev.monorepo_sync.audit import (
    CompletenessResult,
    CorrectnessResult,
    audit_inbound_completeness,
    audit_inbound_correctness,
    audit_outbound_completeness,
    audit_outbound_correctness,
    denormalize_file_path,
    format_commit_info_short,
    format_mismatch,
    normalize_internal_files,
)
from automation.dagster_dev.monorepo_sync.config import SYNC_CONFIGS, SyncConfig, get_sync_config
from automation.dagster_dev.monorepo_sync.git_helpers import (
    extract_label_values,
    get_changed_files,
    git,
)

SYNC_NAMES = ["dagster-inbound", "dagster-outbound", "skills-inbound", "skills-outbound"]
SYNC_CHOICES = [*SYNC_NAMES, "all"]
CHECK_CHOICES = ["completeness", "correctness", "all"]
FORMAT_CHOICES = ["text", "json"]


def _detect_internal_repo() -> Path:
    """Walk up from CWD looking for the internal repo root."""
    candidate = Path.cwd()
    for _ in range(20):
        if (candidate / "dagster-oss").is_dir() and (candidate / "copy.bara.sky").is_file():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    raise click.ClickException(
        "Could not detect internal repo root. Use --internal-repo to specify it."
    )


def _run_checks(
    configs: list[SyncConfig],
    checks: list[str],
    public_repo: Path,
    internal_repo: Path,
) -> list[CompletenessResult | CorrectnessResult]:
    """Run the requested checks for the given configs."""
    results: list[CompletenessResult | CorrectnessResult] = []

    for config in configs:
        if "completeness" in checks:
            if config.direction == "inbound":
                results.append(
                    audit_inbound_completeness(
                        public_repo=public_repo,
                        internal_repo=internal_repo,
                        config=config,
                    )
                )
            else:
                results.append(
                    audit_outbound_completeness(
                        public_repo=public_repo,
                        internal_repo=internal_repo,
                        config=config,
                    )
                )

        if "correctness" in checks:
            if config.direction == "inbound":
                results.append(
                    audit_inbound_correctness(
                        public_repo=public_repo,
                        internal_repo=internal_repo,
                        config=config,
                    )
                )
            else:
                results.append(
                    audit_outbound_correctness(
                        public_repo=public_repo,
                        internal_repo=internal_repo,
                        config=config,
                    )
                )

    return results


# ########################
# ##### TEXT OUTPUT
# ########################


def _has_completeness_errors(result: CompletenessResult) -> bool:
    return bool(result.missing)


def _has_correctness_errors(result: CorrectnessResult) -> bool:
    return any(not m.known_incorrect for m in result.mismatches)


def _print_completeness_summary(console: Console, result: CompletenessResult) -> None:
    label = f"{result.direction.upper()} completeness: {result.source_repo_name} -> {result.dest_repo_name}"
    passing = result.synced_count
    total = result.synced_count + len(result.missing)

    if not result.missing:
        console.print(
            f"  [green]\u2713[/green] [bold]{label}[/bold] [green]({passing}/{total} commits)[/green]"
        )
    else:
        console.print(
            f"  [red]\u2717[/red] [bold]{label}[/bold] [red]({passing}/{total} commits)[/red]"
        )


def _print_correctness_summary(console: Console, result: CorrectnessResult) -> None:
    label = f"{result.direction.upper()} correctness: {result.source_repo_name} -> {result.dest_repo_name}"
    unknown = [m for m in result.mismatches if not m.known_incorrect]
    passing = result.synced_count - len(unknown)
    total = result.synced_count

    if not unknown:
        console.print(
            f"  [green]\u2713[/green] [bold]{label}[/bold] [green]({passing}/{total} commits)[/green]"
        )
    else:
        console.print(
            f"  [red]\u2717[/red] [bold]{label}[/bold] [red]({passing}/{total} commits)[/red]"
        )


def _print_completeness_errors(console: Console, result: CompletenessResult) -> None:
    label = f"{result.direction.upper()} completeness: {result.source_repo_name} -> {result.dest_repo_name}"
    console.print(f"\n[bold]{label}[/bold] ({len(result.missing)} commits missing)")
    for commit in result.missing[:10]:
        console.print(f"  {format_commit_info_short(commit)}")
        console.print(f"  https://github.com/{result.source_repo_name}/commit/{commit.hash}")
    if len(result.missing) > 10:
        console.print(f"  ... and {len(result.missing)} total")


def _print_correctness_errors(console: Console, result: CorrectnessResult) -> None:
    label = f"{result.direction.upper()} correctness: {result.source_repo_name} -> {result.dest_repo_name}"
    unknown = [m for m in result.mismatches if not m.known_incorrect]

    console.print(f"\n[bold]{label}[/bold] ({len(unknown)} commits mismatched)")

    for m in unknown:
        console.print(format_mismatch(m, result.source_repo_name, result.dest_repo_name))


def _get_origin_master_info(repo_path: Path) -> tuple[str, str]:
    """Return (short_hash, timestamp) for origin/master."""
    raw = git(["log", "-1", "--format=%h\t%ci", "origin/master"], cwd=repo_path).strip()
    short_hash, timestamp = raw.split("\t", 1)
    return short_hash, timestamp


def _print_text(
    results: list[CompletenessResult | CorrectnessResult],
    repo_paths: dict[str, Path],
) -> None:
    console = Console()

    # Repo info
    console.print("Repositories:")
    for repo_name, repo_path in repo_paths.items():
        short_hash, timestamp = _get_origin_master_info(repo_path)
        console.print(f"  [bold]{repo_name}[/bold] (origin/master: {short_hash}, {timestamp})")
        console.print(f"    {repo_path}")

    # Summary lines
    console.print("\nTests:")
    for result in results:
        if isinstance(result, CompletenessResult):
            _print_completeness_summary(console, result)
        elif isinstance(result, CorrectnessResult):
            _print_correctness_summary(console, result)

    # Error details
    error_results = [
        r
        for r in results
        if (isinstance(r, CompletenessResult) and _has_completeness_errors(r))
        or (isinstance(r, CorrectnessResult) and _has_correctness_errors(r))
    ]
    if error_results:
        console.print("\n===== Errors")
        for result in error_results:
            if isinstance(result, CompletenessResult):
                _print_completeness_errors(console, result)
            elif isinstance(result, CorrectnessResult):
                _print_correctness_errors(console, result)


# ########################
# ##### JSON OUTPUT
# ########################


def _to_json(results: list[CompletenessResult | CorrectnessResult]) -> str:
    return json.dumps(
        {"results": [asdict(r) for r in results]},
        indent=2,
    )


# ########################
# ##### CLI
# ########################


@click.group(name="monorepo-sync")
def monorepo_sync():
    """Monorepo sync tools (copybara sync between internal and public repos)."""
    pass


@monorepo_sync.command()
@click.option(
    "-s",
    "--sync",
    "sync_name",
    type=click.Choice(SYNC_CHOICES, case_sensitive=False),
    default="all",
    help="Which sync pair to audit.",
)
@click.option(
    "-p",
    "--property",
    "check_name",
    type=click.Choice(CHECK_CHOICES, case_sensitive=False),
    default="all",
    help="Which property to audit (completeness, correctness, or all).",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
    default="text",
    help="Output format.",
)
@click.option(
    "--dagster-repo",
    "dagster_repo_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to dagster-io/dagster clone. Required for dagster-* syncs.",
)
@click.option(
    "--skills-repo",
    "skills_repo_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to dagster-io/skills clone. Required for skills-* syncs.",
)
@click.option(
    "--internal-repo",
    "internal_repo_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to internal repo. If omitted, auto-detects from CWD.",
)
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Exit with code 1 if any errors are detected.",
)
def audit(
    sync_name: str,
    check_name: str,
    output_format: str,
    dagster_repo_path: str | None,
    skills_repo_path: str | None,
    internal_repo_path: str | None,
    check: bool,
):
    """Audit completeness and correctness of copybara syncs.

    Checks that commits are synced between internal and public repos, and
    that synced commits touch the same set of files as their partners.

    Examples:
        dagster-dev monorepo-sync audit --dagster-repo /path/to/dagster --skills-repo /path/to/skills

        dagster-dev monorepo-sync audit --dagster-repo /path/to/dagster -s dagster-outbound -p correctness

        dagster-dev monorepo-sync audit --dagster-repo /path/to/dagster -f json
    """
    internal_repo = Path(internal_repo_path) if internal_repo_path else _detect_internal_repo()

    checks = ["completeness", "correctness"] if check_name == "all" else [check_name]

    if sync_name == "all":
        configs_to_run = list(SYNC_CONFIGS)
    else:
        configs_to_run = [get_sync_config(sync_name)]

    # Validate that required repo paths are provided
    slugs_needed = {c.public_repo_slug for c in configs_to_run}
    slug_to_repo: dict[str, Path] = {}
    if "dagster" in slugs_needed:
        if not dagster_repo_path:
            raise click.ClickException("--dagster-repo is required for dagster-* syncs.")
        slug_to_repo["dagster"] = Path(dagster_repo_path)
    if "skills" in slugs_needed:
        if not skills_repo_path:
            raise click.ClickException("--skills-repo is required for skills-* syncs.")
        slug_to_repo["skills"] = Path(skills_repo_path)

    # Build repo_name -> Path mapping for display
    repo_paths: dict[str, Path] = {"dagster-io/internal": internal_repo}
    for slug, public_repo in slug_to_repo.items():
        slug_configs = [c for c in configs_to_run if c.public_repo_slug == slug]
        # Get the public repo name from any config with this slug
        for c in slug_configs:
            repo_name = c.source_repo_name if c.direction == "inbound" else c.dest_repo_name
            repo_paths[repo_name] = public_repo
            break

    all_results: list[CompletenessResult | CorrectnessResult] = []
    for slug, public_repo in slug_to_repo.items():
        slug_configs = [c for c in configs_to_run if c.public_repo_slug == slug]
        all_results.extend(_run_checks(slug_configs, checks, public_repo, internal_repo))

    if output_format == "json":
        click.echo(_to_json(all_results))
    else:
        _print_text(all_results, repo_paths)

    if check:
        has_errors = any(
            (
                _has_completeness_errors(r)
                if isinstance(r, CompletenessResult)
                else _has_correctness_errors(r)
            )
            for r in all_results
        )
        if has_errors:
            raise SystemExit(1)


def _compute_extra_files(
    *,
    source_repo: Path,
    dest_repo: Path,
    source_hash: str,
    dest_hash: str,
    config: SyncConfig,
) -> list[str]:
    """Compute extra dest-repo file paths for a synced commit pair.

    Returns a sorted list of actual dest-repo paths that are present in the dest
    commit but not in the source commit. If the source commit cannot be read
    (e.g. force-pushed away, shallow clone missing history), emits a warning
    and returns an empty list — the dest commit is skipped, but any unintended
    file reverts in it will not be caught. Raises if the dest commit cannot be
    read, since dest_hash comes from a walk of dest_repo and missing it is a bug.
    """
    source_files = get_changed_files(source_repo, source_hash)
    if source_files is None:
        click.echo(
            f"WARNING: source commit {source_hash[:10]} not found in {source_repo}. "
            f"Skipping correctness check for dest commit {dest_hash[:10]}; "
            f"any unintended file reverts in it will not be caught.",
            err=True,
        )
        return []
    dest_files = get_changed_files(dest_repo, dest_hash)
    if dest_files is None:
        raise click.ClickException(
            f"dest commit {dest_hash[:10]} not found in {dest_repo}. "
            f"This is unexpected (dest_hash comes from this repo's own commit walk)."
        )

    if config.direction == "inbound":
        dest_normalized = normalize_internal_files(
            dest_files, config.internal_path_prefix, config.file_renames
        )
        extra_normalized = dest_normalized - source_files
    else:
        source_normalized = normalize_internal_files(
            source_files, config.internal_path_prefix, config.file_renames
        )
        extra_normalized = dest_files - source_normalized

    if not extra_normalized:
        return []

    return [denormalize_file_path(f, config.direction, config) for f in sorted(extra_normalized)]


def _amend_head(dest_repo: Path, extra_files: list[str]) -> None:
    """Revert extra files from HEAD and amend the commit."""
    for f in extra_files:
        try:
            git(["cat-file", "-e", f"HEAD^:{f}"], cwd=dest_repo)
            git(["checkout", "HEAD^", "--", f], cwd=dest_repo)
        except subprocess.CalledProcessError:
            git(["rm", "-f", f], cwd=dest_repo)

    git(["commit", "--amend", "--no-edit"], cwd=dest_repo)


def _fix_commits_in_range(
    *,
    source_repo: Path,
    dest_repo: Path,
    start_commit: str,
    config: SyncConfig,
) -> int:
    """Fix correctness mismatches from start_commit to HEAD in dest_repo.

    For each synced commit in the range, identifies files present in the dest but
    not in the source and amends the commit to remove them. When the range spans
    multiple commits, subsequent commits are rebased on top of each amendment.

    Returns the number of commits that were amended.
    """
    start_commit = git(["rev-parse", start_commit], cwd=dest_repo).strip()
    head = git(["rev-parse", "HEAD"], cwd=dest_repo).strip()

    # Collect all commits from start_commit to HEAD (inclusive), oldest first
    if start_commit == head:
        commits = [start_commit]
    else:
        raw = git(["rev-list", "--reverse", f"{start_commit}..HEAD"], cwd=dest_repo).strip()
        commits = [start_commit] + [h for h in raw.splitlines() if h.strip()]

    # Build synced mapping (dest_hash -> source_hash) before rewriting history
    synced = extract_label_values(dest_repo, config.synced_label)
    dest_to_source = {v: k for k, v in synced.items()}

    # Pre-compute which commits need fixing using original hashes
    commit_fixes: dict[str, list[str]] = {}
    for c in commits:
        source_hash = dest_to_source.get(c)
        if not source_hash:
            continue
        extra = _compute_extra_files(
            source_repo=source_repo,
            dest_repo=dest_repo,
            source_hash=source_hash,
            dest_hash=c,
            config=config,
        )
        if extra:
            commit_fixes[c] = extra

    if not commit_fixes:
        click.echo(f"No extra files found in {len(commits)} commit(s). Nothing to fix.")
        return 0

    click.echo(f"Found {len(commit_fixes)} commit(s) to fix in range of {len(commits)}.")

    if len(commits) == 1:
        # Single commit at HEAD -- simple amend
        click.echo(f"\n  {start_commit[:10]}: fixing {len(commit_fixes[start_commit])} file(s)")
        for f in commit_fixes[start_commit]:
            click.echo(f"    {f}")
        _amend_head(dest_repo, commit_fixes[start_commit])
        new_hash = git(["rev-parse", "HEAD"], cwd=dest_repo).strip()
        click.echo(f"    amended: {start_commit[:10]} -> {new_hash[:10]}")
    else:
        # Multiple commits -- cherry-pick rebase
        try:
            branch = git(["symbolic-ref", "--short", "HEAD"], cwd=dest_repo).strip()
        except subprocess.CalledProcessError:
            branch = None

        parent = git(["rev-parse", f"{start_commit}^"], cwd=dest_repo).strip()
        git(["checkout", "--detach", parent], cwd=dest_repo)

        for orig_hash in commits:
            git(["cherry-pick", orig_hash], cwd=dest_repo)

            # Recompute extras against the cherry-picked HEAD rather than using
            # the precomputed table. The precompute was taken against the ORIGINAL
            # commits in dest_repo, but after amending an earlier commit the
            # tree state of later cherry-picked commits can shift in ways the
            # precompute can't anticipate. The precompute above still serves as
            # an early-exit guard for the "nothing to fix anywhere" case.
            source_hash = dest_to_source.get(orig_hash)
            if not source_hash:
                continue
            cherry_picked_hash = git(["rev-parse", "HEAD"], cwd=dest_repo).strip()
            extra = _compute_extra_files(
                source_repo=source_repo,
                dest_repo=dest_repo,
                source_hash=source_hash,
                dest_hash=cherry_picked_hash,
                config=config,
            )
            if extra:
                click.echo(f"\n  {orig_hash[:10]}: fixing {len(extra)} file(s)")
                for f in extra:
                    click.echo(f"    {f}")
                _amend_head(dest_repo, extra)
                new_hash = git(["rev-parse", "HEAD"], cwd=dest_repo).strip()
                click.echo(f"    amended: {orig_hash[:10]} -> {new_hash[:10]}")

        # Update the branch ref to the new tip
        new_tip = git(["rev-parse", "HEAD"], cwd=dest_repo).strip()
        if branch:
            git(["branch", "-f", branch, new_tip], cwd=dest_repo)
            git(["checkout", branch], cwd=dest_repo)

    return len(commit_fixes)


@monorepo_sync.command(name="fix-commit")
@click.option(
    "-s",
    "--sync",
    "sync_name",
    type=click.Choice(SYNC_NAMES, case_sensitive=False),
    required=True,
    help="Which sync pair this commit belongs to.",
)
@click.option(
    "--dagster-repo",
    "dagster_repo_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to dagster-io/dagster clone.",
)
@click.option(
    "--skills-repo",
    "skills_repo_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to dagster-io/skills clone.",
)
@click.option(
    "--internal-repo",
    "internal_repo_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to internal repo. If omitted, auto-detects from CWD.",
)
@click.argument("commit_hash")
def fix_commit(
    sync_name: str,
    dagster_repo_path: str | None,
    skills_repo_path: str | None,
    internal_repo_path: str | None,
    commit_hash: str,
):
    """Fix correctness mismatches by amending dest commits to remove extra files.

    Processes all commits from COMMIT_HASH to HEAD. For each synced commit in that
    range, identifies files present in the dest but not in the source, and amends
    the commit to remove them. Subsequent commits are rebased on top of each
    amendment.

    Examples:
        dagster-dev monorepo-sync fix-commit -s dagster-outbound --dagster-repo /path/to/dagster abc123
    """
    config = get_sync_config(sync_name)
    internal_repo = Path(internal_repo_path) if internal_repo_path else _detect_internal_repo()

    slug = config.public_repo_slug
    if slug == "dagster":
        if not dagster_repo_path:
            raise click.ClickException("--dagster-repo is required for dagster-* syncs.")
        public_repo = Path(dagster_repo_path)
    elif slug == "skills":
        if not skills_repo_path:
            raise click.ClickException("--skills-repo is required for skills-* syncs.")
        public_repo = Path(skills_repo_path)
    else:
        raise click.ClickException(f"Unknown public repo slug: {slug}")

    if config.direction == "inbound":
        dest_repo = internal_repo
        source_repo = public_repo
    else:
        dest_repo = public_repo
        source_repo = internal_repo

    fixed = _fix_commits_in_range(
        source_repo=source_repo,
        dest_repo=dest_repo,
        start_commit=commit_hash,
        config=config,
    )
    if fixed:
        click.echo("\nDone.")
    else:
        click.echo("Nothing to fix.")


# ########################
# ##### RUN COMMAND
# ########################


def _adapt_copybara_config(config_path: Path, url_map: dict[str, str]) -> str:
    """Read a copy.bara.sky config and substitute URLs."""
    content = config_path.read_text(encoding="utf-8")
    for old_url, new_url in url_map.items():
        if old_url not in content:
            raise click.ClickException(
                f"Expected URL {old_url!r} not found in {config_path}. "
                f"The copybara config may have changed."
            )
        content = content.replace(old_url, new_url)
    return content


@monorepo_sync.command(name="run")
@click.option(
    "-s",
    "--sync",
    "sync_name",
    type=click.Choice(SYNC_NAMES, case_sensitive=False),
    required=True,
    help="Which sync pair to run.",
)
@click.option(
    "--copybara-config",
    "copybara_config_path",
    type=click.Path(exists=True),
    default="copy.bara.sky",
    help="Path to the copy.bara.sky file.",
)
@click.option(
    "--dest-repo-url",
    default=None,
    help="Override the destination repo URL (default: from SyncConfig).",
)
@click.option(
    "--git-committer-email",
    default="devtools@dagsterlabs.com",
    help="Committer email for copybara.",
)
@click.option(
    "--git-committer-name",
    default="Dagster Devtools",
    help="Committer name for copybara.",
)
@click.option(
    "--last-rev",
    default=None,
    help="Passthrough: copybara --last-rev.",
)
@click.option(
    "--iterative-limit-changes",
    default=None,
    type=int,
    help="Passthrough: copybara --iterative-limit-changes.",
)
def run_sync(
    sync_name: str,
    copybara_config_path: str,
    dest_repo_url: str | None,
    git_committer_email: str,
    git_committer_name: str,
    last_rev: str | None,
    iterative_limit_changes: int | None,
):
    """Run a copybara sync with automatic fix-commit for correctness mismatches.

    Clones the destination repo locally, runs copybara against the local clone,
    inspects new commits for extra files, amends any mismatched commits, and
    pushes the result to the remote destination.

    Examples:
        dagster-dev monorepo-sync run -s dagster-outbound

        dagster-dev monorepo-sync run -s dagster-inbound --last-rev abc123 --iterative-limit-changes 1
    """
    config = get_sync_config(sync_name)
    effective_dest_url = dest_repo_url or config.dest_repo_url

    if not effective_dest_url or not config.copybara_workflow:
        raise click.ClickException(
            f"Sync config {sync_name!r} is missing copybara_workflow or dest_repo_url."
        )

    source_repo = Path.cwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        dest_clone = Path(tmpdir) / "dest"

        # Clone the destination repo. Single-branch limits history to master; we used to also
        # pass --filter=tree:0 for speed, but copybara serves git-fetches from this clone via a
        # file:// remote and git's upload-pack does not lazy-fetch missing trees, so a treeless
        # clone produces "fatal: bad tree object" partway through the copybara fetch.
        click.echo(f"Cloning {effective_dest_url} ...")
        git(
            [
                "clone",
                "--single-branch",
                "--branch",
                "master",
                effective_dest_url,
                str(dest_clone),
            ]
        )

        # Allow copybara to push to the checked-out branch
        git(["config", "receive.denyCurrentBranch", "updateInstead"], cwd=dest_clone)

        pre_head = git(["rev-parse", "HEAD"], cwd=dest_clone).strip()

        # Rewrite the copybara config to push to the local clone
        adapted = _adapt_copybara_config(
            Path(copybara_config_path),
            {effective_dest_url: f"file://{dest_clone}"},
        )
        adapted_config = Path(tmpdir) / "copy.bara.sky"
        adapted_config.write_text(adapted)

        # Build copybara command
        cmd = [
            "copybara",
            str(adapted_config),
            config.copybara_workflow,
            f"--git-committer-email={git_committer_email}",
            f"--git-committer-name={git_committer_name}",
        ]
        if last_rev:
            cmd.append(f"--last-rev={last_rev}")
        if iterative_limit_changes is not None:
            cmd.append(f"--iterative-limit-changes={iterative_limit_changes}")

        click.echo(f"Running copybara {config.copybara_workflow} ...")
        result = subprocess.run(cmd, check=False)

        if result.returncode == 4:
            click.echo("No changes to sync (copybara exit 4).")
            return
        if result.returncode != 0:
            raise click.ClickException(f"Copybara failed with exit code {result.returncode}.")

        post_head = git(["rev-parse", "HEAD"], cwd=dest_clone).strip()

        if pre_head == post_head:
            click.echo("No new commits after copybara.")
            return

        # Identify the first new commit (child of pre_head)
        first_new = (
            git(
                ["rev-list", "--reverse", "--ancestry-path", f"{pre_head}..{post_head}"],
                cwd=dest_clone,
            )
            .strip()
            .splitlines()[0]
        )

        new_count = int(
            git(["rev-list", "--count", f"{pre_head}..{post_head}"], cwd=dest_clone).strip()
        )
        click.echo(f"Copybara synced {new_count} commit(s). Checking for correctness ...")

        # Determine source/dest for fix-commit
        # For outbound: source=internal (cwd), dest=public (clone)
        # For inbound: source=public (cwd), dest=internal (clone)
        fixed = _fix_commits_in_range(
            source_repo=source_repo,
            dest_repo=dest_clone,
            start_commit=first_new,
            config=config,
        )

        if fixed:
            click.echo(f"Fixed {fixed} commit(s).")

        # Push to the real remote. A non-fast-forward error here means the
        # destination's master advanced between our initial clone and now —
        # rerunning the sync against fresh state should resolve it, since
        # copybara is incremental.
        click.echo(f"Pushing to {effective_dest_url} ...")
        try:
            git(["push", "origin", "master"], cwd=dest_clone)
        except subprocess.CalledProcessError as e:
            raise click.ClickException(
                f"Push to {effective_dest_url} failed (exit {e.returncode}). "
                f"The destination's master likely advanced during sync "
                f"(concurrent commits from another pipeline run, or a direct push). "
                f"Rerun this command; copybara will pick up any new commits from "
                f"both sides and the next push should succeed against fresh state."
            ) from e
        click.echo("Done.")

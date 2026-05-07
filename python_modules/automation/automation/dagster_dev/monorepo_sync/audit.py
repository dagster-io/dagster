"""Core audit logic for monorepo sync completeness and correctness."""

from dataclasses import dataclass, field
from pathlib import Path

from automation.dagster_dev.monorepo_sync.config import SyncConfig
from automation.dagster_dev.monorepo_sync.git_helpers import (
    commits_with_label,
    extract_label_values,
    get_changed_files,
    get_commit_info,
    git_log_hashes,
)


@dataclass
class CommitInfo:
    hash: str
    committer_date: str = ""
    author: str = ""
    title: str = ""


@dataclass
class CompletenessResult:
    check: str  # "completeness"
    direction: str  # "inbound" or "outbound"
    source_repo_name: str
    dest_repo_name: str
    synced_count: int
    missing: list[CommitInfo] = field(default_factory=list)


@dataclass
class CorrectnessMismatch:
    source: CommitInfo
    dest: CommitInfo
    extra_in_source: list[str] = field(default_factory=list)
    extra_in_dest: list[str] = field(default_factory=list)
    known_incorrect: bool = False


@dataclass
class CorrectnessResult:
    check: str  # "correctness"
    direction: str  # "inbound" or "outbound"
    source_repo_name: str
    dest_repo_name: str
    synced_count: int
    mismatches: list[CorrectnessMismatch] = field(default_factory=list)


# ########################
# ##### COMPLETENESS
# ########################


def audit_inbound_completeness(
    *,
    public_repo: Path,
    internal_repo: Path,
    config: SyncConfig,
) -> CompletenessResult:
    """Check that all public commits (not originated from internal) have been synced.

    Inbound = public repo -> internal repo.
    """
    synced = extract_label_values(internal_repo, config.synced_label)
    if not synced:
        return CompletenessResult(
            check="completeness",
            direction="inbound",
            source_repo_name=config.source_repo_name,
            dest_repo_name=config.dest_repo_name,
            synced_count=0,
        )

    oldest_synced = next(reversed(synced))
    candidates = git_log_hashes(public_repo, since_commit=oldest_synced)
    originated_from_internal = commits_with_label(public_repo, config.originated_label)

    missing_hashes = [
        h for h in candidates if h not in synced and h not in originated_from_internal
    ]

    missing = [_make_commit_info(public_repo, h) for h in missing_hashes]

    return CompletenessResult(
        check="completeness",
        direction="inbound",
        source_repo_name=config.source_repo_name,
        dest_repo_name=config.dest_repo_name,
        synced_count=len(synced),
        missing=missing,
    )


def audit_outbound_completeness(
    *,
    public_repo: Path,
    internal_repo: Path,
    config: SyncConfig,
) -> CompletenessResult:
    """Check that all internal commits touching a path have been synced to public.

    Outbound = internal repo -> public repo.
    """
    synced = extract_label_values(public_repo, config.synced_label)
    if not synced:
        return CompletenessResult(
            check="completeness",
            direction="outbound",
            source_repo_name=config.source_repo_name,
            dest_repo_name=config.dest_repo_name,
            synced_count=0,
        )

    oldest_synced = next(reversed(synced))
    candidates = git_log_hashes(
        internal_repo, path=config.internal_path, since_commit=oldest_synced
    )
    originated_from_public = commits_with_label(internal_repo, config.originated_label)

    missing_hashes = [h for h in candidates if h not in synced and h not in originated_from_public]

    missing = [_make_commit_info(internal_repo, h) for h in missing_hashes]

    return CompletenessResult(
        check="completeness",
        direction="outbound",
        source_repo_name=config.source_repo_name,
        dest_repo_name=config.dest_repo_name,
        synced_count=len(synced),
        missing=missing,
    )


# ########################
# ##### CORRECTNESS
# ########################


def audit_inbound_correctness(
    *,
    public_repo: Path,
    internal_repo: Path,
    config: SyncConfig,
) -> CorrectnessResult:
    """Check that each synced inbound commit touches the same files as its source.

    Inbound = public repo -> internal repo.
    `synced_label` values in the internal repo map public_hash -> internal_hash.
    """
    synced = extract_label_values(internal_repo, config.synced_label)
    known_set = set(config.known_incorrect)
    mismatches: list[tuple[str, CorrectnessMismatch]] = []  # (sort_date, mismatch)

    for public_hash, internal_hash in synced.items():
        is_known = internal_hash in known_set

        public_files = get_changed_files(public_repo, public_hash)
        if public_files is None:
            continue
        internal_files = get_changed_files(internal_repo, internal_hash)
        if internal_files is None:
            continue

        internal_normalized = _normalize_internal_files(
            internal_files, config.internal_path_prefix, config.file_renames
        )

        extra_in_internal = internal_normalized - public_files
        extra_in_public = public_files - internal_normalized

        if extra_in_internal or extra_in_public:
            mismatch = CorrectnessMismatch(
                source=_make_commit_info(public_repo, public_hash),
                dest=_make_commit_info(internal_repo, internal_hash),
                extra_in_source=sorted(extra_in_public),
                extra_in_dest=sorted(extra_in_internal),
                known_incorrect=is_known,
            )
            mismatches.append((mismatch.dest.committer_date, mismatch))

    mismatches.sort(key=lambda m: m[0], reverse=True)

    return CorrectnessResult(
        check="correctness",
        direction="inbound",
        source_repo_name=config.source_repo_name,
        dest_repo_name=config.dest_repo_name,
        synced_count=len(synced),
        mismatches=[m[1] for m in mismatches],
    )


def audit_outbound_correctness(
    *,
    public_repo: Path,
    internal_repo: Path,
    config: SyncConfig,
) -> CorrectnessResult:
    """Check that each synced outbound commit touches the same files as its source.

    Outbound = internal repo -> public repo.
    `synced_label` values in the public repo map internal_hash -> public_hash.
    """
    synced = extract_label_values(public_repo, config.synced_label)
    known_set = set(config.known_incorrect)
    mismatches: list[tuple[str, CorrectnessMismatch]] = []  # (sort_date, mismatch)

    for internal_hash, public_hash in synced.items():
        is_known = public_hash in known_set

        internal_files = get_changed_files(internal_repo, internal_hash)
        if internal_files is None:
            continue
        public_files = get_changed_files(public_repo, public_hash)
        if public_files is None:
            continue

        internal_normalized = _normalize_internal_files(
            internal_files, config.internal_path_prefix, config.file_renames
        )

        extra_in_internal = internal_normalized - public_files
        extra_in_public = public_files - internal_normalized

        if extra_in_internal or extra_in_public:
            mismatch = CorrectnessMismatch(
                source=_make_commit_info(internal_repo, internal_hash),
                dest=_make_commit_info(public_repo, public_hash),
                extra_in_source=sorted(extra_in_internal),
                extra_in_dest=sorted(extra_in_public),
                known_incorrect=is_known,
            )
            mismatches.append((mismatch.dest.committer_date, mismatch))

    mismatches.sort(key=lambda m: m[0], reverse=True)

    return CorrectnessResult(
        check="correctness",
        direction="outbound",
        source_repo_name=config.source_repo_name,
        dest_repo_name=config.dest_repo_name,
        synced_count=len(synced),
        mismatches=[m[1] for m in mismatches],
    )


# ########################
# ##### FORMATTING
# ########################


def format_commit_info_short(c: CommitInfo) -> str:
    """One-line summary: truncated hash, date, author, title."""
    date_str = c.committer_date[:16] if c.committer_date else "?"
    return f"{c.hash[:10]} {date_str}  {c.author}  {c.title}"


def format_mismatch(
    m: CorrectnessMismatch,
    source_repo_name: str | None = None,
    dest_repo_name: str | None = None,
) -> str:
    """Multi-line plain-text block for a single correctness mismatch.

    If repo names are provided, includes GitHub commit links.
    """
    source_date = m.source.committer_date[:16] if m.source.committer_date else "?"
    dest_date = m.dest.committer_date[:16] if m.dest.committer_date else "?"
    lines = [
        f"  Source: {m.source.hash}",
        f"    {source_date}  {m.source.author}  {m.source.title}",
    ]
    if source_repo_name:
        lines.append(f"    https://github.com/{source_repo_name}/commit/{m.source.hash}")
    lines.extend(
        [
            f"  Dest:   {m.dest.hash}",
            f"    {dest_date}  {m.dest.author}  {m.dest.title}",
        ]
    )
    if dest_repo_name:
        lines.append(f"    https://github.com/{dest_repo_name}/commit/{m.dest.hash}")
    if m.extra_in_source:
        lines.append(f"  Files in source but NOT in dest ({len(m.extra_in_source)}):")
        for f in m.extra_in_source:
            lines.append(f"    - {f}")
    if m.extra_in_dest:
        lines.append(f"  Files in dest but NOT in source ({len(m.extra_in_dest)}):")
        for f in m.extra_in_dest:
            lines.append(f"    + {f}")
    return "\n".join(lines)


def format_completeness_failure(result: CompletenessResult) -> str:
    """Plain-text failure message for a completeness check."""
    lines = [
        f"{result.direction.capitalize()} sync incomplete:"
        f" {len(result.missing)} commits in {result.source_repo_name}"
        f" not synced to {result.dest_repo_name}."
        f" Synced count: {result.synced_count}",
        "Missing commits:",
    ]
    for c in result.missing[:10]:
        lines.append(f"  {format_commit_info_short(c)}")
    if len(result.missing) > 10:
        lines.append(f"  ... and {len(result.missing)} total")
    return "\n".join(lines)


def format_correctness_failure(
    result: CorrectnessResult,
    mismatches: list[CorrectnessMismatch],
) -> str:
    """Plain-text failure message for a correctness check."""
    lines = [
        f"{result.direction.capitalize()} sync correctness check failed:"
        f" {len(mismatches)} commit(s) synced from {result.source_repo_name}"
        f" to {result.dest_repo_name} have file mismatches.",
        "This means copybara included unintended file changes in the sync commit,",
        "likely reverting work due to a race condition. If the reversion has already",
        "been fixed, add the destination commit hash to the known_incorrect list in",
        "dagster-oss/python_modules/automation/automation/dagster_dev/monorepo_sync/config.py.",
        "",
    ]
    for m in mismatches:
        lines.append(format_mismatch(m))
        lines.append("")
    return "\n".join(lines)


# ########################
# ##### HELPERS
# ########################


def _make_commit_info(repo_path: Path, commit_hash: str) -> CommitInfo:
    date, author, title = get_commit_info(repo_path, commit_hash)
    return CommitInfo(hash=commit_hash, committer_date=date, author=author, title=title)


def _normalize_internal_files(
    files: set[str],
    prefix: str,
    file_renames: dict[str, str],
) -> set[str]:
    """Normalize internal file paths to match public repo paths.

    1. Strips the internal path prefix (e.g. "dagster-oss/") from each file.
    2. Applies known copybara file renames (e.g. yarn.oss.lock -> yarn.lock).
    3. Discards files that don't have the prefix (internal-only files are expected).
    """
    result = set()
    reverse_renames = {v: k for k, v in file_renames.items()}
    for f in files:
        if not f.startswith(prefix):
            continue
        relative = f[len(prefix) :]
        if relative in file_renames:
            relative = file_renames[relative]
        elif relative in reverse_renames:
            relative = reverse_renames[relative]
        result.add(relative)
    return result

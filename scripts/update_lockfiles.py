#!/usr/bin/env python3
"""Generate/update uv.lock for every package with a tox.ini.

Walks dagster-oss/ for tox.ini files and runs `uv lock` in the sibling directory
(which must contain a pyproject.toml). With --check, runs `uv lock --check` to
verify staleness without modifying any lockfiles. Designed to be run from
anywhere; locates the dagster-oss root by walking up from this script's location.

Examples:
    # Update every package's lock against the current pypi state
    python dagster-oss/scripts/update_lockfiles.py

    # Check staleness in CI without writing
    python dagster-oss/scripts/update_lockfiles.py --check

    # Just one or two packages by path or name
    python dagster-oss/scripts/update_lockfiles.py python_modules/libraries/dagster-slack
    python dagster-oss/scripts/update_lockfiles.py dagster-slack dagster-dbt

    # Serial (useful when uv's network/CPU contention is a problem)
    python dagster-oss/scripts/update_lockfiles.py --jobs 1
"""

import argparse
import concurrent.futures
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

DAGSTER_OSS_ROOT = Path(__file__).resolve().parents[1]

# Packages skipped from default discovery because they currently have no
# locally-satisfiable resolution. Operators can still target them explicitly
# (e.g. `update_lockfiles.py docs_snippets`) — the skip only applies to the
# no-arg/full-tree default. Each entry should have a one-line reason. Keep
# this list empty in the happy path; only add entries when a package is
# known to be unfixable and the team has accepted that.
KNOWN_UNLOCKABLE: dict[str, str] = {}

DEFAULT_EXCLUDE_NEWER = "48h"
DEFAULT_PYTHON = "3.10"


@dataclass
class Result:
    package: Path
    ok: bool
    duration: float
    detail: str  # short summary line printed inline
    stderr: str  # full stderr for failure inspection


def find_packages() -> tuple[list[Path], list[Path], list[tuple[Path, str]]]:
    """Return (lockable_dirs, tox_without_pyproject, known_unlockable).

    A directory is lockable if it contains both `tox.ini` and `pyproject.toml`
    and is NOT in KNOWN_UNLOCKABLE. `tox.ini` files without a sibling
    pyproject.toml are surfaced separately (typically yarn/docker wrappers).
    Directories listed in KNOWN_UNLOCKABLE are also surfaced separately along
    with the reason they're skipped.
    """
    lockable: list[Path] = []
    orphan_tox: list[Path] = []
    skipped: list[tuple[Path, str]] = []
    for tox in DAGSTER_OSS_ROOT.rglob("tox.ini"):
        if any(part in {".tox", ".venv", "node_modules", "__pycache__"} for part in tox.parts):
            continue
        pyproject = tox.parent / "pyproject.toml"
        if not pyproject.exists():
            orphan_tox.append(tox)
            continue
        rel = str(tox.parent.relative_to(DAGSTER_OSS_ROOT))
        if rel in KNOWN_UNLOCKABLE:
            skipped.append((tox.parent, KNOWN_UNLOCKABLE[rel]))
        else:
            lockable.append(tox.parent)
    return sorted(lockable), sorted(orphan_tox), sorted(skipped, key=lambda x: x[0])


def resolve_targets(args: list[str]) -> tuple[list[Path], list[Path], list[tuple[Path, str]]]:
    all_pkgs, orphan_tox, skipped = find_packages()
    if not args:
        return all_pkgs, orphan_tox, skipped

    # When explicit targets are given, allow KNOWN_UNLOCKABLE packages through too
    all_lookup_pool = list(all_pkgs) + [p for p, _ in skipped]
    by_name = {p.name: p for p in all_lookup_pool}
    by_rel = {str(p.relative_to(DAGSTER_OSS_ROOT)): p for p in all_lookup_pool}
    resolved: list[Path] = []
    missing: list[str] = []
    for arg in args:
        candidate = Path(arg)
        if candidate.is_absolute() and candidate.is_dir():
            resolved.append(candidate.resolve())
            continue
        if arg in by_rel:
            resolved.append(by_rel[arg])
            continue
        if arg in by_name:
            resolved.append(by_name[arg])
            continue
        candidate_rel = DAGSTER_OSS_ROOT / arg
        if candidate_rel.is_dir() and (candidate_rel / "pyproject.toml").exists():
            resolved.append(candidate_rel.resolve())
            continue
        missing.append(arg)
    if missing:
        sys.exit(f"unknown package(s): {', '.join(missing)}")
    return resolved, [], []  # when targets are explicit we don't warn about orphans/skips


def _has_own_requires_python(pkg: Path) -> bool:
    """Return True if the package's pyproject.toml declares `requires-python`."""
    pyproject = pkg / "pyproject.toml"
    if not pyproject.exists():
        return False
    return any(
        line.lstrip().startswith("requires-python")
        for line in pyproject.read_text(encoding="utf-8").splitlines()
    )


def run_uv(
    pkg: Path,
    check: bool,
    uv_bin: str,
    exclude_newer: str | None,
    python: str | None,
) -> Result:
    """Invoke `uv lock` for one package.

    `--python` is only passed when the package's pyproject lacks a
    `requires-python` declaration. If pyproject has its own bound, uv
    should honor that; passing `--python` could clash with it.
    """
    cmd = [uv_bin, "lock"]
    if check:
        cmd.append("--check")
    if exclude_newer:
        cmd.extend(["--exclude-newer", exclude_newer])
    if python and not _has_own_requires_python(pkg):
        cmd.extend(["--python", python])
    start = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=pkg,
        capture_output=True,
        text=True,
        check=False,
    )
    duration = time.monotonic() - start
    ok = proc.returncode == 0
    # uv lock emits the human summary on stderr; first non-empty line is the gist
    detail_lines = [ln.strip() for ln in proc.stderr.splitlines() if ln.strip()]
    detail = detail_lines[-1] if detail_lines else ""
    return Result(package=pkg, ok=ok, duration=duration, detail=detail, stderr=proc.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Optional package names or paths. Defaults to every dagster-oss package with [dependency-groups].",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run `uv lock --check` instead of `uv lock` (verifies up-to-date without writing).",
    )
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=8,
        help="Parallel jobs (default: 8). Use 1 for serial.",
    )
    parser.add_argument(
        "--uv",
        default=None,
        help="Path to the uv binary (default: search PATH).",
    )
    parser.add_argument(
        "--exclude-newer",
        default=DEFAULT_EXCLUDE_NEWER,
        metavar="CUTOFF",
        help=(
            f"Forwarded verbatim to `uv lock --exclude-newer`. uv accepts a "
            f"relative duration (e.g. `48h`, `7d`), an absolute date "
            f"(`YYYY-MM-DD`), or an RFC 3339 timestamp. Pass `none` to omit "
            f"the flag. Default: {DEFAULT_EXCLUDE_NEWER}."
        ),
    )
    parser.add_argument(
        "--python",
        default=DEFAULT_PYTHON,
        metavar="VERSION",
        help=(
            f"Forwarded to `uv lock --python`. Sets the Python version uv "
            f"resolves against, which becomes the lockfile's "
            f"`requires-python` floor when the package's pyproject.toml "
            f"doesn't declare one. Pass `none` to omit (uv falls back to "
            f"the host interpreter). Default: {DEFAULT_PYTHON}."
        ),
    )
    args = parser.parse_args()
    exclude_newer = None if args.exclude_newer.lower() == "none" else args.exclude_newer
    python = None if args.python.lower() == "none" else args.python

    uv_bin = args.uv or shutil.which("uv")
    if not uv_bin:
        sys.exit("uv not found on PATH; pass --uv /path/to/uv")

    pkgs, orphan_tox, skipped_known = resolve_targets(args.targets)
    if orphan_tox:
        print(
            f"Skipping {len(orphan_tox)} tox.ini file(s) with no sibling pyproject.toml (can't be locked):"
        )
        for tox in orphan_tox:
            print(f"  {tox.relative_to(DAGSTER_OSS_ROOT)}")
        print()
    if skipped_known:
        print(
            f"Skipping {len(skipped_known)} known-unlockable package(s) (pass explicitly to retry):"
        )
        for pkg, reason in skipped_known:
            print(f"  {pkg.relative_to(DAGSTER_OSS_ROOT)} — {reason}")
        print()
    if not pkgs:
        print("no packages found")
        return 0

    action = "Checking" if args.check else "Updating"
    print(f"{action} {len(pkgs)} lockfile(s) with {args.jobs} job(s)...", flush=True)

    results: list[Result] = []
    if args.jobs == 1:
        for pkg in pkgs:
            r = run_uv(pkg, args.check, uv_bin, exclude_newer, python)
            results.append(r)
            print_inline(r)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            future_to_pkg = {
                pool.submit(run_uv, pkg, args.check, uv_bin, exclude_newer, python): pkg
                for pkg in pkgs
            }
            for future in concurrent.futures.as_completed(future_to_pkg):
                r = future.result()
                results.append(r)
                print_inline(r)

    failures = [r for r in results if not r.ok]
    total = sum(r.duration for r in results)
    print()
    print(
        f"Done: {len(results) - len(failures)} ok, {len(failures)} failed (total wall-clock not shown; cumulative work {total:.1f}s)"
    )
    if failures:
        print()
        print("Failures:")
        for r in failures:
            print(f"  {r.package.relative_to(DAGSTER_OSS_ROOT)}")
            for line in r.stderr.splitlines()[-15:]:
                print(f"    {line}")
        return 1
    return 0


def print_inline(r: Result) -> None:
    status = "OK" if r.ok else "FAIL"
    rel = r.package.relative_to(DAGSTER_OSS_ROOT)
    print(f"  [{status}] {rel} ({r.duration:.1f}s) {r.detail}", flush=True)


if __name__ == "__main__":
    sys.exit(main())

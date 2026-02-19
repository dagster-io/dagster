"""Caching system for AI code review analysis."""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    """Repository analysis cache entry."""

    commit_hash: str
    branch_name: str
    pr_number: str | None
    analysis_timestamp: float

    # Cached analysis data
    diff_summary: dict[str, Any]
    smart_analysis: dict[str, Any] | None


class CacheManager:
    """Manages persistent cache for repository analysis."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize cache manager."""
        if cache_dir is None:
            # Default to .git directory
            git_dir = Path(".git")
            if not git_dir.exists():
                raise ValueError("Not in a git repository - cannot create cache")
            cache_dir = git_dir / "claude_analysis_cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "repository_analysis.json"

    def _get_current_commit_hash(self) -> str:
        """Get current commit hash."""
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def _get_current_branch(self) -> str:
        """Get current branch name."""
        import subprocess

        result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def get_cache_key(self, commit_hash: str, branch_name: str) -> str:
        """Generate cache key from commit and branch."""
        return f"{branch_name}:{commit_hash[:12]}"

    def is_cache_valid(self, entry: CacheEntry, max_age_seconds: int = 3600) -> bool:
        """Check if cache entry is still valid."""
        current_time = time.time()
        age = current_time - entry.analysis_timestamp

        return (
            entry.commit_hash == self._get_current_commit_hash()
            and entry.branch_name == self._get_current_branch()
            and age < max_age_seconds
        )

    def get_cached_analysis(self) -> CacheEntry | None:
        """Get cached analysis for current repository state."""
        if not self.cache_file.exists():
            return None

        try:
            cache_data = json.loads(self.cache_file.read_text())
            entry = CacheEntry(**cache_data)

            if self.is_cache_valid(entry):
                return entry
            else:
                # Cache is stale
                return None

        except (json.JSONDecodeError, TypeError, ValueError):
            # Corrupted cache file
            return None

    def store_analysis(
        self,
        diff_summary: dict[str, Any],
        smart_analysis: dict[str, Any] | None = None,
        pr_number: str | None = None,
    ) -> None:
        """Store analysis results in cache."""
        entry = CacheEntry(
            commit_hash=self._get_current_commit_hash(),
            branch_name=self._get_current_branch(),
            pr_number=pr_number,
            analysis_timestamp=time.time(),
            diff_summary=diff_summary,
            smart_analysis=smart_analysis,
        )

        # Write to cache file
        self.cache_file.write_text(json.dumps(asdict(entry), indent=2))

    def clear_cache(self) -> bool:
        """Clear all cached data."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            return True
        except OSError:
            return False

    def get_cache_status(self) -> dict[str, Any]:
        """Get information about cache state."""
        if not self.cache_file.exists():
            return {"exists": False, "size_bytes": 0, "entries": 0}

        try:
            stat = self.cache_file.stat()
            cache_data = json.loads(self.cache_file.read_text())
            entry = CacheEntry(**cache_data)

            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "entries": 1,
                "last_analysis": entry.analysis_timestamp,
                "cached_commit": entry.commit_hash[:12],
                "cached_branch": entry.branch_name,
                "is_valid": self.is_cache_valid(entry),
            }
        except (json.JSONDecodeError, TypeError, ValueError):
            return {
                "exists": True,
                "size_bytes": self.cache_file.stat().st_size,
                "entries": 0,
                "error": "Corrupted cache file",
            }

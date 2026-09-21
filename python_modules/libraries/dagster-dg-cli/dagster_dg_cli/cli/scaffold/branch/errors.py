"""User-facing errors for scaffold branch helpers."""


class ScaffoldBranchError(Exception):
    """Base class for scaffold branch errors that should be shown to CLI users."""


class GitCommandError(ScaffoldBranchError):
    """Raised when a git command fails."""


class GitRepositoryError(ScaffoldBranchError):
    """Raised when the current git repository state is invalid for the operation."""

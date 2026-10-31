import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest
from dagster_shared.utils.fs import _clear_read_only_and_retry, _on_error, rmtree

# ########################
# ##### TESTS
# ########################


def test_rmtree_removes_tree_containing_read_only_files(tmp_path: Path) -> None:
    project = _build_tree(tmp_path)
    nested_read_only = project / ".git" / "objects" / "ab" / "cdef"
    # check the mode bits rather than os.access, which reports writable for root regardless
    assert stat.S_IMODE(nested_read_only.stat().st_mode) == 0o400

    rmtree(project)

    assert not project.exists()
    assert tmp_path.exists()


def test_rmtree_retries_transient_permission_errors(tmp_path: Path) -> None:
    project = _build_tree(tmp_path)
    real_unlink = os.unlink
    calls: list[str] = []

    def flaky_unlink(path, *args, **kwargs):
        # emulate the sharing violation Windows raises while another process holds the file open
        if os.fspath(path).endswith("dbt_project.yml"):
            calls.append(os.fspath(path))
            if len(calls) < 3:
                raise PermissionError(32, "The process cannot access the file")
        return real_unlink(path, *args, **kwargs)

    with patch("os.unlink", side_effect=flaky_unlink):
        rmtree(project)

    assert not project.exists()
    assert len(calls) == 3
    # rmtree's own first attempt is relative to a directory fd; every retry the handler drives
    # must instead use the full path, since the handler has no fd to resolve a name against
    assert all(Path(call).is_absolute() for call in calls[1:])


def test_rmtree_raises_when_permission_error_persists(tmp_path: Path) -> None:
    project = _build_tree(tmp_path)

    def always_denied(path, *args, **kwargs):
        raise PermissionError(5, "Access is denied")

    with patch("os.unlink", side_effect=always_denied):
        with pytest.raises(PermissionError):
            rmtree(project)

    # the failure must surface rather than leave the caller believing the tree is gone
    assert project.exists()


def test_rmtree_does_not_retry_non_removal_operations(tmp_path: Path) -> None:
    """Rmtree routes failures from every stage of its walk through the same hook, and re-reports
    a failure the hook raises with func set to the stage in progress. Retrying a non-removal
    call such as scandir would succeed and make an unfixed failure look handled, letting the
    delete resume when it should have stopped.
    """
    project = _build_tree(tmp_path)
    exc = PermissionError(13, "Permission denied")
    calls: list[str] = []

    def record(path):
        calls.append(path)

    with pytest.raises(PermissionError):
        _clear_read_only_and_retry(record, str(project), exc)

    assert calls == []


def test_on_error_adapter_handles_legacy_exc_info(tmp_path: Path) -> None:
    """``rmtree`` uses the ``onerror`` hook below Python 3.12, which passes an exc_info triple
    rather than the exception itself. Covered directly so the branch is exercised on any
    interpreter.
    """
    target = tmp_path / "read_only"
    target.write_bytes(b"x")
    os.chmod(target, stat.S_IRUSR)
    exc = PermissionError(5, "Access is denied")

    _on_error(os.unlink, str(target), (PermissionError, exc, None))

    assert not target.exists()

    with pytest.raises(ValueError):
        _on_error(os.unlink, str(target), (ValueError, ValueError("unrelated"), None))


# ########################
# ##### HELPERS
# ########################


def _build_tree(root: Path) -> Path:
    """Builds a tree shaped like a dbt project snapshot holding a git checkout, whose object and
    pack files git writes read-only.
    """
    objects = root / "project" / ".git" / "objects" / "ab"
    objects.mkdir(parents=True)

    read_only_file = objects / "cdef"
    read_only_file.write_bytes(b"object")
    os.chmod(read_only_file, stat.S_IRUSR)

    (root / "project" / "dbt_project.yml").write_text("name: jaffle_shop", encoding="utf-8")

    return root / "project"

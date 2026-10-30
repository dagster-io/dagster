"""The temporary project copy used for large dbt selections."""

import io
import json
import shutil
from pathlib import Path
from unittest import mock

import pytest
from dagster_dbt.asset_utils import _copy_dbt_project_for_ephemeral_selector
from dagster_dbt.core.dbt_cli_invocation import DbtCliInvocation
from dagster_dbt.core.dbt_event_iterator import DbtEventIterator
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.errors import DagsterDbtCliRuntimeError
from packaging import version


def _write_project(project_dir: Path) -> DbtProject:
    project_dir.mkdir()
    (project_dir / "dbt_project.yml").write_text(
        "\n".join(
            [
                "name: proj",
                "profile: proj",
                "target-path: custom_target",
                "log-path: custom_logs",
                "",
            ]
        )
    )
    (project_dir / "models").mkdir()
    (project_dir / "models" / "m.sql").write_text("select 1 as id")
    # A source directory that happens to be named logs must survive the copy.
    (project_dir / "models" / "logs").mkdir()
    (project_dir / "models" / "logs" / "note.txt").write_text("keep")
    (project_dir / "models" / "__pycache__").mkdir()
    (project_dir / "models" / "__pycache__" / "m.pyc").write_bytes(b"pyc")

    for relative in (
        "custom_target/manifest.json",
        "custom_logs/dbt.log",
        "target/manifest.json",
        "logs/dbt.log",
        "dagster_target/manifest.json",
        ".git/config",
        ".venv/pyvenv.cfg",
        "venv/bin/activate",
        "__pycache__/mod.pyc",
        "dbt_packages/some_pkg/dbt_project.yml",
    ):
        path = project_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")

    return DbtProject(project_dir=project_dir, target_path="dagster_target")


def test_ephemeral_copy_skips_build_dirs_and_keeps_packages(tmp_path: Path) -> None:
    project = _write_project(tmp_path / "proj")
    temp_dir = _copy_dbt_project_for_ephemeral_selector(Path(project.project_dir), project)
    try:
        assert (temp_dir / "models" / "m.sql").read_text() == "select 1 as id"
        assert (temp_dir / "models" / "logs" / "note.txt").read_text() == "keep"
        assert (temp_dir / "dbt_packages" / "some_pkg" / "dbt_project.yml").exists()
        assert (temp_dir / "dbt_project.yml").exists()

        for skipped in (
            "custom_target",
            "custom_logs",
            "target",
            "logs",
            "dagster_target",
            ".git",
            ".venv",
            "venv",
            "__pycache__",
        ):
            assert not (temp_dir / skipped).exists(), skipped
        assert not (temp_dir / "models" / "__pycache__").exists()
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def test_ephemeral_copy_keeps_sources_beside_nested_output_dirs(tmp_path: Path) -> None:
    """`build/target` must not drop sources that live in `build/models`."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "dbt_project.yml").write_text(
        "\n".join(
            [
                "name: proj",
                "profile: proj",
                "target-path: build/target",
                "log-path: build/logs",
                "",
            ]
        )
    )
    (project_dir / "build" / "models").mkdir(parents=True)
    (project_dir / "build" / "models" / "m.sql").write_text("select 1 as id")
    (project_dir / "build" / "target").mkdir()
    (project_dir / "build" / "target" / "manifest.json").write_text("x")
    (project_dir / "build" / "logs").mkdir()
    (project_dir / "build" / "logs" / "dbt.log").write_text("x")
    (project_dir / "artifacts" / "dagster_target").mkdir(parents=True)
    (project_dir / "artifacts" / "dagster_target" / "manifest.json").write_text("x")
    (project_dir / "artifacts" / "sources").mkdir()
    (project_dir / "artifacts" / "sources" / "seed.csv").write_text("id\n1\n")
    (project_dir / "target").mkdir()
    (project_dir / "target" / "manifest.json").write_text("x")
    (project_dir / "logs").mkdir()
    (project_dir / "logs" / "dbt.log").write_text("x")

    project = DbtProject(project_dir=project_dir, target_path="artifacts/dagster_target")
    temp_dir = _copy_dbt_project_for_ephemeral_selector(Path(project.project_dir), project)
    try:
        assert (temp_dir / "build" / "models" / "m.sql").read_text() == "select 1 as id"
        assert (temp_dir / "artifacts" / "sources" / "seed.csv").read_text() == "id\n1\n"
        assert (temp_dir / "dbt_project.yml").exists()
        for skipped in (
            "build/target",
            "build/logs",
            "artifacts/dagster_target",
            "target",
            "logs",
        ):
            assert not (temp_dir / skipped).exists(), skipped
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def _fake_invocation(
    temp_dir: Path,
    stdout: io.BytesIO,
    *,
    returncode: int = 0,
    poll_result: int | None = 0,
    raise_on_error: bool = True,
) -> DbtCliInvocation:
    process = mock.Mock()
    process.stdout = stdout
    process.wait.return_value = returncode
    process.poll.return_value = poll_result
    process.returncode = returncode
    process.args = ["dbt", "run"]
    return DbtCliInvocation(
        process=process,
        manifest={},
        dagster_dbt_translator=DagsterDbtTranslator(),
        project_dir=temp_dir,
        target_path=temp_dir.parent / "artifacts",
        raise_on_error=raise_on_error,
        cli_version=version.parse("1.8.0"),
        temp_project_dir=temp_dir,
    )


def test_wait_removes_temp_project(tmp_path: Path) -> None:
    temp_dir = tmp_path / "copy"
    temp_dir.mkdir()
    invocation = _fake_invocation(temp_dir, io.BytesIO(b""))

    assert invocation.wait() is invocation

    assert not temp_dir.exists()


def test_failed_wait_removes_temp_project(tmp_path: Path) -> None:
    temp_dir = tmp_path / "copy"
    temp_dir.mkdir()
    invocation = _fake_invocation(temp_dir, io.BytesIO(b""), returncode=1)

    with pytest.raises(DagsterDbtCliRuntimeError):
        invocation.wait()

    assert not temp_dir.exists()


def test_failed_stream_next_removes_temp_project(tmp_path: Path) -> None:
    """next() on a failed stream() still deletes the temporary project."""
    temp_dir = tmp_path / "copy"
    temp_dir.mkdir()
    invocation = _fake_invocation(temp_dir, io.BytesIO(b""), returncode=1)

    stream = invocation.stream()
    with pytest.raises(DagsterDbtCliRuntimeError):
        next(stream)

    assert not temp_dir.exists()


def test_stream_removes_temp_project_when_consumed(tmp_path: Path) -> None:
    temp_dir = tmp_path / "copy"
    temp_dir.mkdir()
    invocation = _fake_invocation(temp_dir, io.BytesIO(b""))

    assert list(invocation.stream()) == []

    assert not temp_dir.exists()


def test_raw_stream_closed_early_removes_temp_project(tmp_path: Path) -> None:
    temp_dir = tmp_path / "copy"
    temp_dir.mkdir()
    payload = json.dumps(
        {"data": {}, "info": {"level": "info", "name": "MainReportVersion", "msg": "hi"}}
    )
    invocation = _fake_invocation(
        temp_dir,
        io.BytesIO(f"{payload}\n{payload}\n".encode()),
        poll_result=None,
    )

    stream = invocation.stream_raw_events()
    next(stream)
    assert temp_dir.exists()

    stream.close()

    assert not temp_dir.exists()
    invocation.process.terminate.assert_called_once()


def test_event_iterator_closed_early_removes_temp_project(tmp_path: Path) -> None:
    temp_dir = tmp_path / "copy"
    temp_dir.mkdir()
    invocation = _fake_invocation(temp_dir, io.BytesIO(b""))

    def events():
        yield "one"
        yield "two"

    iterator = DbtEventIterator(events(), invocation, cleanup_on_close=True)
    gen = iter(iterator)
    assert next(gen) == "one"
    assert temp_dir.exists()

    gen.close()

    assert not temp_dir.exists()


def test_outer_iterator_keeps_temp_project_until_it_finishes(tmp_path: Path) -> None:
    """Post-processing wrappers run after the inner event stream is exhausted."""
    temp_dir = tmp_path / "copy"
    temp_dir.mkdir()
    invocation = _fake_invocation(temp_dir, io.BytesIO(b""))
    seen: dict[str, bool] = {}

    def inner_events():
        yield "event"

    inner = DbtEventIterator(inner_events(), invocation, cleanup_on_close=True)

    def outer_events():
        yield from inner
        seen["exists_after_inner"] = temp_dir.exists()
        yield "post"

    outer = inner._with_events(outer_events())  # noqa: SLF001

    assert list(outer) == ["event", "post"]
    assert seen["exists_after_inner"] is True
    assert not temp_dir.exists()

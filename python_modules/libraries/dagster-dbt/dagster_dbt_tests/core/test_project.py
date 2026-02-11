import multiprocessing
from pathlib import Path

import msgpack
import pytest
from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_dbt.dbt_project import DagsterDbtProjectPreparer, DbtProject

from dagster_dbt_tests.dbt_projects import test_jaffle_shop_path


@pytest.fixture(scope="session")
def shared_project_dir():
    with copy_directory(test_jaffle_shop_path) as project_dir:
        yield project_dir


@pytest.fixture(scope="function")
def project_dir(shared_project_dir):
    manifest_path = DbtProject(shared_project_dir).manifest_path
    if manifest_path.exists():
        manifest_path.unlink()
    yield shared_project_dir


def test_local_dev(project_dir) -> None:
    my_project = DbtProject(project_dir)
    assert not my_project.manifest_path.exists()
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        my_project = DbtProject(project_dir)
        my_project.prepare_if_dev()
        assert my_project.manifest_path.exists()


def _init(project_dir):
    my_project = DbtProject(project_dir)
    my_project.prepare_if_dev()
    assert my_project.manifest_path.exists()
    assert validate_manifest(my_project.manifest_path)
    return


def test_concurrent_processes(project_dir):
    my_project = DbtProject(project_dir)
    assert not my_project.manifest_path.exists()
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        procs = [multiprocessing.Process(target=_init, args=(project_dir,)) for _ in range(4)]
        for proc in procs:
            proc.start()

        for proc in procs:
            proc.join(timeout=30)
            assert proc.exitcode == 0

        assert my_project.manifest_path.exists()


def test_invalidate_seeds_in_partial_parse(project_dir) -> None:
    """Test that seed entries are removed from partial_parse.msgpack after preparation.

    Seeds contain root_path which is an absolute path from build time. When state
    is generated in one environment (CI/CD) and used in another (deployed container),
    the root_path points to the wrong location and seed loading fails.

    By removing seed entries from the cache, dbt will re-parse them at runtime with
    the correct current project path. Models keep their cached data for fast loading.
    """
    my_project = DbtProject(project_dir)
    partial_parse_path = my_project.project_dir / my_project.target_path / "partial_parse.msgpack"

    # Prepare the project which generates partial_parse.msgpack
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        my_project.prepare_if_dev()

    assert partial_parse_path.exists(), "partial_parse.msgpack should exist after preparation"

    # Read the partial_parse and verify seeds were removed
    with open(partial_parse_path, "rb") as f:
        data = msgpack.unpack(f, raw=False, strict_map_key=False)

    # Check that no seed nodes remain
    seed_node_ids = [k for k in data.get("nodes", {}).keys() if k.startswith("seed.")]
    assert len(seed_node_ids) == 0, f"Expected no seed nodes, but found: {seed_node_ids}"

    # Check that no seed files remain (CSVs)
    seed_file_ids = [k for k in data.get("files", {}).keys() if k.lower().endswith(".csv")]
    assert len(seed_file_ids) == 0, f"Expected no seed files, but found: {seed_file_ids}"

    # Check that model nodes are preserved
    model_node_ids = [k for k in data.get("nodes", {}).keys() if k.startswith("model.")]
    assert len(model_node_ids) > 0, "Model nodes should be preserved"

    # Check that model files are preserved
    model_file_ids = [k for k in data.get("files", {}).keys() if ".sql" in k.lower()]
    assert len(model_file_ids) > 0, "Model files should be preserved"


def test_invalidate_seeds_handles_missing_partial_parse() -> None:
    """Test that _invalidate_seeds_in_partial_parse handles missing file gracefully."""
    with copy_directory(test_jaffle_shop_path) as project_dir:
        my_project = DbtProject(project_dir)
        partial_parse_path = (
            my_project.project_dir / my_project.target_path / "partial_parse.msgpack"
        )

        # Ensure partial_parse doesn't exist
        if partial_parse_path.exists():
            partial_parse_path.unlink()

        # Should not raise an error
        preparer = DagsterDbtProjectPreparer()
        preparer._invalidate_seeds_in_partial_parse(my_project)  # noqa: SLF001


def test_seed_command_succeeds_after_invalidation() -> None:
    """Test that dbt seed command works after seed entries are invalidated.

    This is the end-to-end validation that removing seed entries from
    partial_parse.msgpack allows dbt to correctly re-parse and load seeds.
    """
    from dagster_dbt import DbtCliResource

    with copy_directory(test_jaffle_shop_path) as project_dir:
        my_project = DbtProject(project_dir)

        # Prepare the project (which invalidates seeds in partial_parse)
        with environ({"DAGSTER_IS_DEV_CLI": "1"}):
            my_project.prepare_if_dev()

        # Run dbt seed - this should succeed because dbt will re-parse
        # the seed files with correct paths
        dbt = DbtCliResource(project_dir=my_project)
        result = dbt.cli(["seed"]).wait()

        assert result.is_successful(), "dbt seed failed"

def test_target_path_as_string() -> None:
    """Test that target_path can be provided as a string and is correctly converted to Path."""
    with copy_directory(test_jaffle_shop_path) as project_dir:
        target_path_str = "custom_target"
        my_project = DbtProject(project_dir, target_path=target_path_str)
        assert my_project.target_path == Path(target_path_str)
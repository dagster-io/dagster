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


def test_update_seed_paths_in_partial_parse(project_dir) -> None:
    """Test that seed root_path entries are updated in partial_parse.msgpack after preparation.

    Seeds contain root_path which is an absolute path from build time. When state
    is generated in one environment (CI/CD) and used in another (deployed container),
    the root_path points to the wrong location and seed loading fails.

    By updating root_path for seed entries to the current project directory, seeds
    remain in the manifest (and visible in dagster-dev) while using the correct path.
    jaffle_shop has 3 seed CSVs: raw_customers, raw_orders, raw_payments.
    """
    my_project = DbtProject(project_dir)
    partial_parse_path = my_project.project_dir / my_project.target_path / "partial_parse.msgpack"

    # Prepare the project which generates partial_parse.msgpack
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        my_project.prepare_if_dev()

    assert partial_parse_path.exists(), "partial_parse.msgpack should exist after preparation"

    # Read the partial_parse and verify seeds are present with updated root_path
    with open(partial_parse_path, "rb") as f:
        data = msgpack.unpack(f, raw=False, strict_map_key=False)

    current_project_dir = str(my_project.project_dir.resolve())

    # Check that seed nodes are still present and have the correct root_path
    seed_nodes = {k: v for k, v in data.get("nodes", {}).items() if k.startswith("seed.")}
    assert len(seed_nodes) > 0, (
        "jaffle_shop dbt project should have seed nodes in partial_parse after prepare_if_dev()"
    )
    for seed_id, node in seed_nodes.items():
        assert node.get("root_path") == current_project_dir, (
            f"Seed node {seed_id} has incorrect root_path: {node.get('root_path')!r}, "
            f"expected: {current_project_dir!r}"
        )

    # Check that seed file entries (CSVs) are still present and have the correct root_path
    seed_files = {k: v for k, v in data.get("files", {}).items() if k.lower().endswith(".csv")}
    assert len(seed_files) > 0, (
        "jaffle_shop dbt project should have seed file entries in partial_parse after prepare_if_dev()"
    )
    for file_id, file_entry in seed_files.items():
        assert file_entry.get("root_path") == current_project_dir, (
            f"Seed file {file_id} has incorrect root_path: {file_entry.get('root_path')!r}, "
            f"expected: {current_project_dir!r}"
        )

    # Check that model nodes are preserved
    model_node_ids = [k for k in data.get("nodes", {}).keys() if k.startswith("model.")]
    assert len(model_node_ids) > 0, "Model nodes should be preserved"

    # Check that model files are preserved
    model_file_ids = [k for k in data.get("files", {}).keys() if ".sql" in k.lower()]
    assert len(model_file_ids) > 0, "Model files should be preserved"


def test_update_seed_paths_corrects_stale_root_path(project_dir) -> None:
    """Test that _update_seed_paths_in_partial_parse corrects a stale root_path.

    Simulates the cross-environment portability scenario: a partial_parse produced in
    CI (with path /ci/workspace) is shipped to a container (with path /app). The method
    must detect the stale path and overwrite it with the current project directory.
    """
    my_project = DbtProject(project_dir)
    partial_parse_path = my_project.project_dir / my_project.target_path / "partial_parse.msgpack"

    # Generate a real partial_parse first
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        my_project.prepare_if_dev()

    assert partial_parse_path.exists()

    # Inject a stale root_path into all seed nodes and seed file entries
    stale_path = "/stale/ci/workspace/project"
    with open(partial_parse_path, "rb") as f:
        data = msgpack.unpack(f, raw=False, strict_map_key=False)

    seed_node_keys = [k for k in data.get("nodes", {}) if k.startswith("seed.")]
    seed_file_keys = [k for k in data.get("files", {}) if k.lower().endswith(".csv")]

    assert len(seed_node_keys) > 0, "Need seed nodes in partial_parse to run this test"
    assert len(seed_file_keys) > 0, "Need seed file entries in partial_parse to run this test"

    for key in seed_node_keys:
        data["nodes"][key]["root_path"] = stale_path
    for key in seed_file_keys:
        data["files"][key]["root_path"] = stale_path

    with open(partial_parse_path, "wb") as f:
        msgpack.pack(data, f)

    # Now call the method and verify it corrects the stale paths
    preparer = DagsterDbtProjectPreparer()
    preparer._update_seed_paths_in_partial_parse(my_project)  # noqa: SLF001

    with open(partial_parse_path, "rb") as f:
        corrected = msgpack.unpack(f, raw=False, strict_map_key=False)

    current_project_dir = str(my_project.project_dir.resolve())

    for key in seed_node_keys:
        assert corrected["nodes"][key]["root_path"] == current_project_dir, (
            f"Seed node {key} still has stale root_path after correction"
        )
    for key in seed_file_keys:
        assert corrected["files"][key]["root_path"] == current_project_dir, (
            f"Seed file {key} still has stale root_path after correction"
        )


def test_update_seed_paths_handles_missing_partial_parse() -> None:
    """Test that _update_seed_paths_in_partial_parse handles missing file gracefully."""
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
        preparer._update_seed_paths_in_partial_parse(my_project)  # noqa: SLF001


def test_accepts_string_target_path(project_dir) -> None:
    project_dir_path = Path(project_dir)
    string_target_path = str(project_dir_path / "dbt_target")
    my_project = DbtProject(project_dir_path, target_path=string_target_path)
    assert isinstance(my_project.target_path, Path)
    assert my_project.target_path == Path(string_target_path)


def test_seed_command_succeeds_after_path_update() -> None:
    """Test that dbt seed command works after seed root_path entries are updated.

    This is the end-to-end validation that keeping seed entries in partial_parse
    (with corrected root_path) allows dbt to correctly locate and load seeds.
    """
    from dagster_dbt import DbtCliResource

    with copy_directory(test_jaffle_shop_path) as project_dir:
        my_project = DbtProject(project_dir)

        # Prepare the project (which updates seed paths in partial_parse)
        with environ({"DAGSTER_IS_DEV_CLI": "1"}):
            my_project.prepare_if_dev()

        # Run dbt seed - this should succeed because seeds remain in partial_parse
        # with the correct root_path for the current project directory
        dbt = DbtCliResource(project_dir=my_project)
        result = dbt.cli(["seed"]).wait()

        assert result.is_successful(), "dbt seed failed"

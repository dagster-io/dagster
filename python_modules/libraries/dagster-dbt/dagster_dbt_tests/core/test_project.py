import multiprocessing
from pathlib import Path

import msgpack
import pytest
from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_dbt.dbt_project import DagsterDbtProjectPreparer, DbtProject

from dagster_dbt_tests.dbt_projects import test_dbt_unit_tests_path, test_jaffle_shop_path

# A unit test that sources its inputs from CSV fixtures (files under tests/fixtures/).
# Fixtures are .csv files, so a seed-invalidation strategy that keys off the .csv
# extension would incorrectly sweep them up. See
# https://github.com/dagster-io/dagster/issues/33471.
_CSV_FIXTURE_UNIT_TEST_YML = """\
unit_tests:
  - name: test_first_order
    model: customers
    given:
      - input: ref('stg_customers')
        format: csv
        fixture: stg_customers_fixture
      - input: ref('stg_orders')
        format: csv
        fixture: stg_orders_fixture
      - input: ref('stg_payments')
        format: csv
        fixture: stg_payments_fixture
    expect:
      format: csv
      fixture: expected_customers_fixture
"""
_CSV_FIXTURES = {
    "stg_customers_fixture.csv": "customer_id\n1\n",
    "stg_orders_fixture.csv": "customer_id,order_id,order_date\n1,1,2024-01-01\n",
    "stg_payments_fixture.csv": "order_id,amount\n1,10\n",
    "expected_customers_fixture.csv": (
        "customer_id,first_name,last_name,first_order,most_recent_order,"
        "number_of_orders,customer_lifetime_value\n1,a,b,2024-01-01,2024-06-01,1,10\n"
    ),
}


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
    """Test that seed file checksums are invalidated in partial_parse.msgpack after preparation.

    Seeds contain root_path which is an absolute path from build time. When state
    is generated in one environment (CI/CD) and used in another (deployed container),
    the root_path points to the wrong location and seed loading fails.

    Rather than removing seed entries (which would mis-key off the .csv extension and
    sweep up unit-test fixtures, see test_prepare_twice_with_csv_unit_test_fixtures), we
    overwrite the saved checksum of each seed file so dbt re-parses it as a changed file
    on the next invocation, refreshing root_path. Models keep their cached data.
    """
    my_project = DbtProject(project_dir)
    partial_parse_path = my_project.project_dir / my_project.target_path / "partial_parse.msgpack"

    # Prepare the project which generates partial_parse.msgpack
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        my_project.prepare_if_dev()

    assert partial_parse_path.exists(), "partial_parse.msgpack should exist after preparation"

    # Read the partial_parse and verify seed checksums were invalidated
    with open(partial_parse_path, "rb") as f:
        data = msgpack.unpack(f, raw=False, strict_map_key=False)

    seed_files = [v for v in data.get("files", {}).values() if v.get("parse_file_type") == "seed"]
    assert len(seed_files) > 0, "Expected seed files in partial_parse"
    for seed_file in seed_files:
        assert seed_file["checksum"]["checksum"] == "0" * 64, (
            "Seed file checksum should be invalidated to force re-parse"
        )

    # Seed nodes themselves should still be present (only the checksum is invalidated)
    seed_node_ids = [k for k in data.get("nodes", {}).keys() if k.startswith("seed.")]
    assert len(seed_node_ids) > 0, "Seed nodes should be preserved"

    # Non-seed file checksums must be untouched (in particular, unit-test fixtures)
    non_seed_files = [
        v for v in data.get("files", {}).values() if v.get("parse_file_type") != "seed"
    ]
    for non_seed_file in non_seed_files:
        checksum = non_seed_file.get("checksum", {}).get("checksum")
        if checksum is not None:
            assert checksum != "0" * 64, "Non-seed file checksums should not be invalidated"

    # Check that model nodes are preserved
    model_node_ids = [k for k in data.get("nodes", {}).keys() if k.startswith("model.")]
    assert len(model_node_ids) > 0, "Model nodes should be preserved"


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


def test_prepare_twice_with_csv_unit_test_fixtures() -> None:
    """Regression test for https://github.com/dagster-io/dagster/issues/33471.

    Unit-test CSV fixtures end in .csv just like seeds. Invalidating seeds by removing
    every .csv file entry from partial_parse.msgpack (while leaving the fixture objects
    in the saved manifest) caused dbt to re-add the fixtures on the next parse, raising a
    duplicate-resource compile error. Preparing a project with CSV fixtures twice in a row
    must succeed.
    """
    with copy_directory(test_dbt_unit_tests_path) as tmp_dir:
        project_dir = Path(tmp_dir)

        # Convert the project's unit test to source from CSV fixtures.
        (project_dir / "models" / "unit_tests.yml").write_text(_CSV_FIXTURE_UNIT_TEST_YML)
        fixtures_dir = project_dir / "tests" / "fixtures"
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        for name, content in _CSV_FIXTURES.items():
            (fixtures_dir / name).write_text(content)

        my_project = DbtProject(project_dir)
        preparer = DagsterDbtProjectPreparer()

        # First prepare builds partial_parse.msgpack (and invalidates seeds).
        preparer.prepare(my_project)
        assert my_project.manifest_path.exists()

        # Second prepare re-parses against the invalidated partial_parse. Before the fix
        # this raised a duplicate-fixture compile error.
        preparer.prepare(my_project)
        assert my_project.manifest_path.exists()


def test_accepts_string_target_path(project_dir) -> None:
    project_dir_path = Path(project_dir)
    string_target_path = str(project_dir_path / "dbt_target")
    my_project = DbtProject(project_dir_path, target_path=string_target_path)
    assert isinstance(my_project.target_path, Path)
    assert my_project.target_path == Path(string_target_path)


def test_prepare_runs_deps_when_packages_exist() -> None:
    """Test that prepare() runs dbt deps even when dbt_packages dir exists.

    Regression test for https://github.com/dagster-io/dagster/issues/31885.
    """
    with copy_directory(test_jaffle_shop_path) as project_dir:
        my_project = DbtProject(project_dir)

        # Create dependencies.yml
        deps_path = Path(project_dir) / "dependencies.yml"
        deps_path.write_text(
            "packages:\n  - package: dbt-labs/dbt_utils\n    version: ['>=1.1.1', '<2.0.0']\n",
            encoding="utf-8",
        )

        # Pre-create dbt_packages to simulate previous installation
        packages_dir = Path(project_dir) / "dbt_packages"
        packages_dir.mkdir(exist_ok=True)

        # Recreate project so it picks up the new deps file
        my_project = DbtProject(project_dir)

        # Even though dbt_packages exists, prepare() should run deps
        preparer = DagsterDbtProjectPreparer()
        preparer.prepare(my_project)

        # dbt deps should have actually installed packages
        assert any(packages_dir.iterdir()), "dbt deps should have installed packages"
        assert my_project.manifest_path.exists(), "dbt parse should have created manifest"


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

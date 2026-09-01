import json
import shutil
from pathlib import Path

import dagster as dg
import pytest
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from dagster_dbt_tests.dbt_projects import test_fusion_compatible_jaffle_shop_path


@pytest.fixture(name="project", scope="module")
def project_fixture() -> DbtProject:
    project = DbtProject(test_fusion_compatible_jaffle_shop_path)
    project.preparer.prepare(project)
    return project


@pytest.mark.fusion
@pytest.mark.parametrize("fail", [True, False])
def test_basic(project: DbtProject, fail: bool) -> None:
    @dbt_assets(manifest=project.manifest_path, project=project)
    def the_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
        if fail:
            yield from dbt.cli(
                ["build", "--vars", json.dumps({"break_customer_build": "true"})], context=context
            ).stream()
        else:
            yield from dbt.cli(["build"], context=context).stream()

    n_assets = len(list(the_assets.specs))
    n_checks = len(list(the_assets.check_specs))
    assert n_assets == 8
    assert n_checks == 20

    result = dg.materialize(
        [the_assets],
        resources={"dbt": DbtCliResource(project_dir=project.project_dir)},
        raise_on_error=not fail,
    )
    assert result.success == (not fail)

    n_materializations = len(result.get_asset_materialization_events())
    n_check_evaluations = len(result.get_asset_check_evaluations())
    if fail:
        # one asset fails, no materialization
        assert n_materializations == n_assets - 1
        # three checks on that asset, no check evaluations for them
        assert n_check_evaluations == n_checks - 3
    else:
        assert n_materializations == n_assets
        assert n_check_evaluations == n_checks


@pytest.mark.fusion
@pytest.mark.skipif(
    shutil.which("dbtf") is None,
    reason="dbtf executable is required for fusion tests",
)
def test_fusion_no_row_limit_injected(project: DbtProject) -> None:
    """Verify that dbt-fusion's `dbtf` executable receives --limit 0 for materialization commands.

    dbt-fusion silently caps row output to 10 rows by default. This test confirms that Dagster
    injects --limit 0 so the cap is disabled in real runs against a fusion binary.
    """
    dbt = DbtCliResource(project_dir=project.project_dir)

    # Confirm we're actually running against dbt-fusion v2+ via the dbtf executable.
    assert Path(dbt.dbt_executable).stem == "dbtf", (
        f"Expected dbtf executable, got {dbt.dbt_executable}"
    )
    assert dbt._cli_version.major >= 2, (  # noqa: SLF001
        f"Expected fusion v2+, got {dbt._cli_version}. Is dbtf on PATH?"  # noqa: SLF001
    )

    # Run seed with a leading global flag; args should still contain --limit 0 injected by Dagster.
    invocation = dbt.cli(["--debug", "seed"])
    assert "--limit" in invocation.process.args, (
        "Dagster must inject --limit into fusion materialization commands"
    )
    limit_idx = list(invocation.process.args).index("--limit")
    assert invocation.process.args[limit_idx + 1] == "0", (
        f"Expected --limit 0, got --limit {invocation.process.args[limit_idx + 1]}"
    )

    # The seed must succeed with the injected flag (proves fusion accepts --limit 0).
    assert invocation.is_successful(), "dbt seed with --limit 0 must succeed on fusion"

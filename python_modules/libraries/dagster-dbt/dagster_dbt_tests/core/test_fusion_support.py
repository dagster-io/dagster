import json

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
    assert n_checks == 19

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
        # two checks on that asset, no check evaluations for them
        assert n_check_evaluations == n_checks - 2
    else:
        assert n_materializations == n_assets
        assert n_check_evaluations == n_checks

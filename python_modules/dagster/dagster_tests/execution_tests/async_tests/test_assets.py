import anyio
import dagster as dg


@dg.asset
async def upstream_asset():
    await anyio.sleep(0.01)
    return 1


@dg.asset
def downstream_asset(upstream_asset):
    return upstream_asset + 1


@dg.asset
async def further_downstream_asset(downstream_asset):
    await anyio.sleep(0.01)
    return downstream_asset + 1


@dg.asset_check(asset=further_downstream_asset)
async def further_downstream_asset_check():
    await anyio.sleep(0.01)
    return dg.AssetCheckResult(passed=True)


def get_test_job():
    defs = dg.Definitions(
        jobs=[
            dg.define_asset_job(
                name="asset_job",
                selection=[
                    upstream_asset,
                    downstream_asset,
                    further_downstream_asset,
                    further_downstream_asset_check,
                ],
                executor_def=dg.async_executor,
            )
        ],
        assets=[upstream_asset, downstream_asset, further_downstream_asset],
        asset_checks=[further_downstream_asset_check],
    )
    return defs.get_job_def("asset_job")


def test_async_executor_with_assets_build_job():
    with (
        dg.instance_for_test() as instance,
        dg.execute_job(
            dg.reconstructable(get_test_job),
            instance=instance,
        ) as result,
    ):
        assert result.success
        assert result.asset_materializations_for_node("upstream_asset")
        assert result.asset_materializations_for_node("downstream_asset")
        assert result.asset_materializations_for_node("further_downstream_asset")

        check_results = [
            cr
            for cr in result.get_asset_check_evaluations()
            if cr.asset_check_key == further_downstream_asset_check.check_key
        ]
        assert len(check_results) == 1
        assert check_results[0].passed is True

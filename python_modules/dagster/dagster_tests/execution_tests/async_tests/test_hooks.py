import anyio
import dagster as dg


@dg.success_hook
async def log_asset_event(context: dg.HookContext):
    await anyio.sleep(0.01)
    context.log.info("I like big data and I cannot lie")


@dg.asset(hooks={log_asset_event})
async def my_asset():
    await anyio.sleep(0.01)
    return 1


def get_test_job():
    defs = dg.Definitions(
        jobs=[
            dg.define_asset_job(
                name="asset_job",
                selection=[my_asset],
                executor_def=dg.async_executor,
            )
        ],
        assets=[my_asset],
    )
    return defs.get_job_def("asset_job")


def test_asset_with_hooks():
    with (
        dg.instance_for_test() as instance,
        dg.execute_job(
            dg.reconstructable(get_test_job),
            instance=instance,
        ) as result,
    ):
        assert result.success
        assert result.asset_materializations_for_node("my_asset")

        hook_events = [event for event in result.all_events if event.is_hook_event]
        assert len(hook_events) == 1

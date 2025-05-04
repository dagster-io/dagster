from dagster import Definitions, HookContext, define_asset_job, graph_asset, op, success_hook


def test_graph_asset_hooks():
    @success_hook
    def my_hook(context: HookContext):
        context.log.info("my_hook")

    @op
    def fetch_files_from_slack():
        pass

    @op
    def store_files(files) -> None:
        pass

    @graph_asset(hooks={my_hook})
    def my_graph_asset():
        return store_files(fetch_files_from_slack())

    job = define_asset_job(
        name="my_job",
        selection=[my_graph_asset],
    )

    defs = Definitions(
        assets=[my_graph_asset],
        jobs=[job],
    )

    result = defs.get_job_def("my_job").execute_in_process()
    hook_completed = [
        event for event in result.all_events if "HOOK_COMPLETED" == event.event_type_value
    ]
    assert len(hook_completed) == 2
    assert hook_completed[0].step_key == "my_graph_asset.fetch_files_from_slack"
    assert hook_completed[1].step_key == "my_graph_asset.store_files"


test_graph_asset_hooks()

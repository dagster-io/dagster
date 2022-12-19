from dagster import (
    asset,
    IOManager,
    Definitions,
    IOManagerDefinition,
    AssetIn,
    materialize,
    instance_for_test,
    DagsterRunStatus
)

import time

def wait_for_all_runs_to_finish(instance, timeout=10):
    start_time = time.time()
    FINISHED_STATES = [
        DagsterRunStatus.SUCCESS,
        DagsterRunStatus.FAILURE,
        DagsterRunStatus.CANCELED,
    ]
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        not_finished_runs = [
            run for run in instance.get_runs() if run.status not in FINISHED_STATES
        ]

        if len(not_finished_runs) == 0:
            break

@asset
def upstream() -> int:
    return 1


@asset(ins={"upstream": AssetIn(input_manager_key="special_io_manager")})
def downstream(upstream) -> int:
    return upstream + 1


class MyIOManager(IOManager):
    def load_input(self, context):
        assert context.upstream_output is not None

    def handle_output(self, context, obj):
        ...


def test_loading_already_materialized_asset():
    with instance_for_test() as instance:
        # materialize the upstream
        materialize([upstream], instance=instance)
        wait_for_all_runs_to_finish(instance)

        # materialize just the downstream
        materialize(
            [downstream],
            resources={
                "special_io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())
            },
            instance=instance,
        )

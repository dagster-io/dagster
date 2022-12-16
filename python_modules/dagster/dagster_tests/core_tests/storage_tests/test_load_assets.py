from dagster import (
    asset,
    IOManager,
    load_assets_from_current_module,
    Definitions,
    IOManagerDefinition,
    AssetIn,
    materialize,
    instance_for_test,
)


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

        # materialize just the downstream
        materialize(
            [downstream],
            resources={
                "special_io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())
            },
            instance=instance,
        )

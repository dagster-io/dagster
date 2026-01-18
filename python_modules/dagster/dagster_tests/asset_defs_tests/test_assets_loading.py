import dagster as dg


def test_input_manager_override():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @dg.io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 4

    @dg.io_manager
    def my_input_manager():
        return MyInputManager()

    @dg.asset
    def first_asset():
        return 1

    @dg.asset(ins={"upstream": dg.AssetIn(key="first_asset", input_manager_key="my_input_manager")})
    def second_asset(upstream):
        assert upstream == 4

    assert dg.materialize(
        dg.with_resources(
            [first_asset, second_asset],
            resource_defs={"my_input_manager": my_input_manager, "io_manager": my_io_manager},
        )
    ).success

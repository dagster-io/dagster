from dagster import AssetIn, IOManager, asset, io_manager, materialize, with_resources


def test_input_manager_override():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 4

    @io_manager
    def my_input_manager():
        return MyInputManager()

    @asset
    def first_asset():
        return 1

    @asset(ins={"upstream": AssetIn(key="first_asset", input_manager_key="my_input_manager")})
    def second_asset(upstream):
        assert upstream == 4

    assert materialize(
        with_resources(
            [first_asset, second_asset],
            resource_defs={"my_input_manager": my_input_manager, "io_manager": my_io_manager},
        )
    ).success

from dagster import AssetKey, InputDefinition, solid


def test_flex_inputs():
    @solid(input_defs=[InputDefinition("arg_b", metadata={"explicit": True})])
    def partial(_context, arg_a, arg_b):
        return arg_a + arg_b

    assert partial.input_defs[0].name == "arg_b"
    assert partial.input_defs[0].metadata["explicit"]
    assert partial.input_defs[1].name == "arg_a"


def test_merge_type():
    @solid(input_defs=[InputDefinition("arg_b", metadata={"explicit": True})])
    def merged(_context, arg_b: int):
        return arg_b

    assert (
        merged.input_defs[0].dagster_type == InputDefinition("test", dagster_type=int).dagster_type
    )
    assert merged.input_defs[0].metadata["explicit"]


def test_merge_desc():
    @solid(input_defs=[InputDefinition("arg_b", metadata={"explicit": True})])
    def merged(_context, arg_a, arg_b, arg_c):
        """
        Testing

        Args:
            arg_b: described
        """
        return arg_a + arg_b + arg_c

    assert merged.input_defs[0].name == "arg_b"
    assert merged.input_defs[0].description == "described"
    assert merged.input_defs[0].metadata["explicit"]


def test_merge_default_val():
    @solid(input_defs=[InputDefinition("arg_b", dagster_type=int, metadata={"explicit": True})])
    def merged(_context, arg_a: int, arg_b=3, arg_c=0):
        return arg_a + arg_b + arg_c

    assert merged.input_defs[0].name == "arg_b"
    assert merged.input_defs[0].default_value == 3
    assert (
        merged.input_defs[0].dagster_type == InputDefinition("test", dagster_type=int).dagster_type
    )


def test_precedence():
    @solid(
        input_defs=[
            InputDefinition(
                "arg_b",
                dagster_type=str,
                default_value="hi",
                description="legit",
                metadata={"explicit": True},
                root_manager_key="rudy",
                asset_key=AssetKey("table_1"),
                asset_partitions={"0"},
            )
        ]
    )
    def precedence(_context, arg_a: int, arg_b: int, arg_c: int):
        """
        Testing

        Args:
            arg_b: boo
        """
        return arg_a + arg_b + arg_c

    assert precedence.input_defs[0].name == "arg_b"
    assert (
        precedence.input_defs[0].dagster_type
        == InputDefinition("test", dagster_type=str).dagster_type
    )
    assert precedence.input_defs[0].description == "legit"
    assert precedence.input_defs[0].default_value == "hi"
    assert precedence.input_defs[0].metadata["explicit"]
    assert precedence.input_defs[0].root_manager_key == "rudy"
    assert precedence.input_defs[0].get_asset_key(None) is not None
    assert precedence.input_defs[0].get_asset_partitions(None) is not None

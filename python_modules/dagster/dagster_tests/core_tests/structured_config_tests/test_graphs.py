from typing import Dict, Tuple

from dagster import Config, ConfigMapping, graph, op
from dagster._core.definitions import materialize
from dagster._core.definitions.assets import AssetsDefinition


def test_basic_graph() -> None:
    executed: Dict[str, bool] = {}

    class ANewConfigOpConfig(Config):
        a_string: str
        an_int: int

    @op
    def a_struct_config_op(config: ANewConfigOpConfig):
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["a_struct_config_op"] = True

    class AnotherNewConfigOpConfig(Config):
        a_string: str
        an_int: int

    @op
    def another_struct_config_op(config: AnotherNewConfigOpConfig):
        assert config.a_string == "bar"
        assert config.an_int == 3
        executed["another_struct_config_op"] = True

    @graph(
        config=ConfigMapping.from_op_config(
            {
                "a_struct_config_op": ANewConfigOpConfig(a_string="foo", an_int=2),
                "another_struct_config_op": AnotherNewConfigOpConfig(a_string="bar", an_int=3),
            }
        )
    )
    def my_graph() -> None:
        a_struct_config_op()
        another_struct_config_op()

    result = my_graph.execute_in_process()
    assert result.success
    assert executed == {
        "a_struct_config_op": True,
        "another_struct_config_op": True,
    }


def test_graph_based_asset() -> None:
    executed: Dict[str, bool] = {}

    class ANewConfigOpConfig(Config):
        a_string: str
        an_int: int

    @op
    def a_struct_config_op(config: ANewConfigOpConfig) -> str:
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["a_struct_config_op"] = True
        return config.a_string

    @graph(
        config=ConfigMapping.from_op_config(
            {
                "a_struct_config_op": ANewConfigOpConfig(a_string="foo", an_int=2),
            }
        )
    )
    def my_graph() -> Tuple[str, str]:
        return a_struct_config_op()

    my_graph_asset = AssetsDefinition.from_graph(my_graph)

    asset_result = materialize(
        [my_graph_asset],
    )

    assert asset_result.success
    assert executed == {
        "a_struct_config_op": True,
    }

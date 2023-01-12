from dagster import asset
from dagster._core.definitions.materialize import materialize
from dagster._core.types.dagster_type import Nothing


def test_none_asset():
    @asset
    def returns_none() -> None:
        pass

    output_def = returns_none.op.output_def_named("result")
    assert output_def
    assert output_def.dagster_type is Nothing

    result = materialize([returns_none])
    assert result
    assert result.success
    materializations = result.asset_materializations_for_node("returns_none")
    assert not materializations

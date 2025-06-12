from collections.abc import Generator

import dagster as dg
from dagster._core.definitions.computation import Computation, Effect
from dagster._core.definitions.decorators.computation_decorator import (
    ComputationResult,
    computation,
)


def test_simple_class_construction():
    @dg.op
    def the_op(upstream: int):
        return upstream + 1

    computation = Computation(
        node_def=the_op,
        input_mappings={
            "upstream": dg.AssetKey("upstream"),
        },
        output_mappings={
            "result": Effect.materialize(
                dg.AssetSpec(key=dg.AssetKey("the_asset"), group_name="the_group")
            ),
        },
        inactive_outputs=set(),
    )

    assets_def = dg.AssetsDefinition(
        node_def=the_op,
        specs=[dg.AssetSpec(key=dg.AssetKey("the_asset"), group_name="the_group")],
        keys_by_output_name={
            "result": dg.AssetKey("the_asset"),
        },
        keys_by_input_name={
            "upstream": dg.AssetKey("upstream"),
        },
    )

    assert computation.to_assets_def().keys_by_output_name == assets_def.keys_by_output_name
    assert computation.to_assets_def().keys_by_input_name == assets_def.keys_by_input_name

    assert computation.to_assets_def().to_computation() == assets_def.to_computation()


def test_single_decorator():
    @computation(
        effects=[
            Effect.materialize(
                dg.AssetSpec(key=dg.AssetKey("the_asset"), deps=["upstream"]),
            ),
        ]
    )
    def the_thing(upstream: int) -> Generator[dg.MaterializeResult, None, None]:
        yield dg.MaterializeResult(
            metadata={"foo": "bar"},
        )

    assert the_thing


def test_multi_decorator_observe_with_checks():
    @dg.asset
    def upstream_explicit() -> int:
        return 1

    @computation(
        effects=[
            Effect.observe(
                dg.AssetSpec(key=dg.AssetKey("a"), deps=["upstream_explicit"]),
            ),
            Effect.observe(
                dg.AssetSpec(key=dg.AssetKey("b"), deps=["upstream_implicit"]),
            ),
            Effect.observe(
                dg.AssetSpec(key=dg.AssetKey("c"), deps=["a", "b"]),
            ),
            Effect.check(dg.AssetCheckSpec(name="check_a", asset="a")),
            Effect.check(dg.AssetCheckSpec(name="check_upstream", asset="upstream_implicit")),
        ],
    )
    def the_thing(upstream_explicit: int) -> ComputationResult:
        yield dg.ObserveResult(
            asset_key=dg.AssetKey("a"),
            metadata={"foo": "bar"},
            check_results=[dg.AssetCheckResult(asset_key=dg.AssetKey("a"), passed=True)],
        )
        yield dg.ObserveResult(asset_key=dg.AssetKey("b"), metadata={"some_val": 2})
        yield dg.ObserveResult(asset_key=dg.AssetKey("c"), metadata={"some_val": 3})
        yield dg.AssetCheckResult(asset_key=dg.AssetKey("upstream_implicit"), passed=False)

    defs = dg.Definitions(
        assets=[upstream_explicit, the_thing.to_assets_def()],
    )

    job = defs.get_implicit_global_asset_job_def()
    result = job.execute_in_process()

    assert result.success
    assert len(result.get_asset_materialization_events()) == 1  # upstream_explicit
    assert len(result.get_asset_check_evaluations()) == 2  # check_a, check_upstream
    assert len(result.get_asset_observation_events()) == 3  # a, b, c

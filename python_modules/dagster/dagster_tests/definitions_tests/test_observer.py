from typing import Sequence

from dagster import AssetKey, AssetSpec, Definitions, asset
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.observer_definition import (
    ObserverDefinition,
    ObserverEvaluationContext,
    ObserverEvaluationResult,
)
from dagster._core.definitions.sensor_definition import build_sensor_context


def test_simplest_observer() -> None:
    class HardcodedObserver(ObserverDefinition):
        def observe(self, context: ObserverEvaluationContext) -> ObserverEvaluationResult:
            cursor_val = int(context.cursor) + 1 if context.cursor else 1

            return ObserverEvaluationResult(cursor=str(cursor_val), updated=cursor_val % 3 == 0)

    hardcoded_observer = HardcodedObserver()

    @asset(deps=[hardcoded_observer.spec])
    def downstream(): ...

    defs = Definitions(
        assets=[downstream],
        sensors=[hardcoded_observer.sensor()],
    )

    def _evaluate_tick(cursor: str):
        return (
            defs.get_sensor_def("HardcodedObserver")
            .evaluate_tick(build_sensor_context(cursor=cursor))
            .asset_events
        )

    asset_events_1 = _evaluate_tick("1")
    assert asset_events_1 == []

    asset_events_2 = _evaluate_tick("2")
    assert len(asset_events_2) == 1
    assert asset_events_2[0].asset_key == AssetKey(["_dagster_external", "HardcodedObserver"])


def test_single_observer() -> None:
    class S3BucketObserver(ObserverDefinition):
        def __init__(self, s3_bucket: str):
            super().__init__(
                name=f"s3_bucket_{s3_bucket}_observer",
                specs=[AssetSpec(key=AssetKey(["s3", s3_bucket]))],
            )

        def observe(self, context: ObserverEvaluationContext) -> ObserverEvaluationResult:
            cursor_val = int(context.cursor) + 1 if context.cursor else 1

            return ObserverEvaluationResult(cursor=str(cursor_val), updated=cursor_val % 3 == 0)

    xyz_bucket_observer = S3BucketObserver("some_bucket")

    @asset(deps=[xyz_bucket_observer.spec])
    def downstream(): ...

    defs = Definitions(
        assets=[downstream],
        sensors=[xyz_bucket_observer.sensor()],
    )

    assert defs.get_sensor_def("s3_bucket_some_bucket_observer")

    asset_graph = defs.get_asset_graph()
    assert asset_graph.get(AssetKey(["s3", "some_bucket"])).child_keys == {downstream.key}
    assert asset_graph.get(downstream.key).parent_keys == {AssetKey(["s3", "some_bucket"])}


def test_multi_observer() -> None:
    class S3BucketsObserver(ObserverDefinition):
        def __init__(self, name: str, s3_buckets: Sequence[str]):
            super().__init__(
                name=name,
                specs=[AssetSpec(key=AssetKey(["s3", b])) for b in s3_buckets],
            )

        def observe(self, context: ObserverEvaluationContext) -> ObserverEvaluationResult:
            cursor_val = int(context.cursor) + 1 if context.cursor else 1

            return ObserverEvaluationResult(cursor=str(cursor_val), updated=cursor_val % 3 == 0)

    multi_observer = S3BucketsObserver("multi_observer", ["a", "b"])

    @asset(deps=[*multi_observer.specs])
    def downstream(): ...

    defs = Definitions(
        assets=[downstream],
        sensors=[multi_observer.sensor()],
    )

    assert defs.get_sensor_def("multi_observer")

    asset_graph = defs.get_asset_graph()
    assert asset_graph.get(AssetKey(["s3", "a"])).child_keys == {downstream.key}
    assert asset_graph.get(AssetKey(["s3", "b"])).child_keys == {downstream.key}
    assert asset_graph.get(downstream.key).parent_keys == {
        AssetKey(["s3", "a"]),
        AssetKey(["s3", "b"]),
    }


class WebhookObserver(ObserverDefinition):
    def observe(self, context: ObserverEvaluationContext) -> ObserverEvaluationResult:
        cursor_val = int(context.cursor) + 1 if context.cursor else 1

        return ObserverEvaluationResult(cursor=str(cursor_val), updated=cursor_val % 3 == 0)


my_webhook_observer = WebhookObserver()


@asset(deps=[my_webhook_observer.spec], auto_materialize_policy=AutoMaterializePolicy.eager())
def downstream() -> None: ...


@asset(deps=[downstream], auto_materialize_policy=AutoMaterializePolicy.eager())
def downerstream() -> None: ...


defs = Definitions(
    assets=[downstream, downerstream],
    sensors=[my_webhook_observer.sensor()],
)

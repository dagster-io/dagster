from dagster import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.reactive_scheduling.reactive_policy import (
    AssetPartition,
    RequestReaction,
    SchedulingPolicy,
    SchedulingResult,
)


class CustomSchedulingPolicy(SchedulingPolicy):
    # tick_cron = "0 0 * * *"
    tick_cron = "*/1 * * * *"

    def schedule(self) -> SchedulingResult:
        return SchedulingResult(execute=True)

    def react_to_downstream_request(self, asset_partition: AssetPartition) -> RequestReaction:
        return RequestReaction(execute=False)

    def react_to_upstream_request(self, asset_partition: AssetPartition) -> RequestReaction:
        return RequestReaction(execute=False)


class DefersSchedulingPolicy(SchedulingPolicy):
    def react_to_downstream_request(self, asset_partition: AssetPartition) -> RequestReaction:
        return RequestReaction(execute=True)

    def react_to_upstream_request(self, asset_partition: AssetPartition) -> RequestReaction:
        return RequestReaction(execute=True)


@asset(scheduling_policy=DefersSchedulingPolicy())
def an_upstream_asset_234():
    pass


@asset(
    deps=[an_upstream_asset_234],
    scheduling_policy=CustomSchedulingPolicy(sensor_name="policy_sensor"),
)
def an_asset_234():
    pass


defs = Definitions([an_asset_234, an_upstream_asset_234])


# assert isinstance(
#     defs.get_assets_def("an_asset").scheduling_policy_by_key[AssetKey(["an_asset"])],
#     CustomSchedulingPolicy,
# )

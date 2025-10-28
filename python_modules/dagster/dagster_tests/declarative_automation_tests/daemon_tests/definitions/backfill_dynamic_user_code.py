import dagster as dg
import dagster._check as check
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.partitions.snap.snap import PartitionsSnap
from dagster._core.definitions.partitions.subset.key_ranges import KeyRangesPartitionsSubset

dynamic_partitions1 = dg.DynamicPartitionsDefinition(name="dynamic1")


class AlwaysEmitFullKeyRangeSubsetCondition(dg.AutomationCondition):
    """Custom condition that ensures that a KeyRangesPartitionsSubset is always emitted,
    to ensure that we don't have partition_loading_context issues.
    """

    def evaluate(self, context):
        partitions_def = context.asset_graph.get(context.key).partitions_def

        partitions_subset = KeyRangesPartitionsSubset(
            key_ranges=[
                dg.PartitionKeyRange(
                    start=partitions_def.get_first_partition_key(),
                    end=partitions_def.get_last_partition_key(),
                )
            ],
            partitions_snap=PartitionsSnap.from_def(partitions_def),
        )

        return dg.AutomationResult(
            true_subset=check.not_none(
                context.asset_graph_view.get_subset_from_serializable_subset(
                    serializable_subset=SerializableEntitySubset(
                        key=context.key,
                        value=partitions_subset,
                    )
                )
            ),
            context=context,
        )


@dg.asset(
    automation_condition=AlwaysEmitFullKeyRangeSubsetCondition(),
    partitions_def=dynamic_partitions1,
)
def A() -> None: ...


defs = dg.Definitions(
    assets=[A],
    sensors=[
        dg.AutomationConditionSensorDefinition("the_sensor", target="*", use_user_code_server=True)
    ],
)

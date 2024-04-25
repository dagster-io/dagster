from enum import Enum
from typing import Optional, Sequence

import pytest
from dagster._core.definitions.asset_condition.asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
)
from dagster._core.definitions.asset_condition.dep_condition import (
    DepSchedulingCondition,
    DepSelectionType,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsDefinition

from ..scenario_specs import one_asset_depends_on_two, two_partitions_def
from .asset_condition_scenario import AssetConditionScenarioState


class TruePartitions(Enum):
    NONE = "NONE"
    ONE = "ONE"
    ALL = "ALL"

    def asset_partitions(
        self, asset_key: AssetKey, partitions_def: Optional[PartitionsDefinition]
    ) -> Sequence[AssetKeyPartitionKey]:
        if self == TruePartitions.NONE:
            return []

        if partitions_def is None:
            return [AssetKeyPartitionKey(asset_key, None)]

        partition_keys = partitions_def.get_partition_keys()
        if self == TruePartitions.ONE:
            return [AssetKeyPartitionKey(asset_key, partition_keys[1])]
        else:
            return [
                AssetKeyPartitionKey(asset_key, partition_key) for partition_key in partition_keys
            ]


@pytest.mark.parametrize(
    [
        "A_partitioned",
        "B_partitioned",
        "C_partitioned",
        "A_true_partitions",
        "B_true_partitions",
        "expected_result_sizes",
    ],
    [
        # (all, all), (all, any), (any, all), (any, any)
        # ALL PARTITIONED
        (True, True, True, TruePartitions.ALL, TruePartitions.ALL, [2, 2, 2, 2]),
        (True, True, True, TruePartitions.ALL, TruePartitions.ONE, [1, 1, 2, 2]),
        (True, True, True, TruePartitions.ALL, TruePartitions.NONE, [0, 0, 2, 2]),
        (True, True, True, TruePartitions.ONE, TruePartitions.ONE, [1, 1, 1, 1]),
        (True, True, True, TruePartitions.ONE, TruePartitions.NONE, [0, 0, 1, 1]),
        (True, True, True, TruePartitions.NONE, TruePartitions.NONE, [0, 0, 0, 0]),
        # PARTITIONED -> UNPARTITIONED
        (True, True, False, TruePartitions.ALL, TruePartitions.ALL, [1, 1, 1, 1]),
        (True, True, False, TruePartitions.ALL, TruePartitions.ONE, [0, 1, 1, 1]),
        (True, True, False, TruePartitions.ALL, TruePartitions.NONE, [0, 0, 1, 1]),
        (True, True, False, TruePartitions.ONE, TruePartitions.ONE, [0, 1, 0, 1]),
        (True, True, False, TruePartitions.ONE, TruePartitions.NONE, [0, 0, 0, 1]),
        (True, True, False, TruePartitions.NONE, TruePartitions.NONE, [0, 0, 0, 0]),
        # UNPARTITIONED -> PARTITIONED
        (False, False, True, TruePartitions.ALL, TruePartitions.ALL, [2, 2, 2, 2]),
        (False, False, True, TruePartitions.ALL, TruePartitions.NONE, [0, 0, 2, 2]),
        (False, False, True, TruePartitions.NONE, TruePartitions.NONE, [0, 0, 0, 0]),
        # MIXED -> UNPARTITIONED
        (True, False, False, TruePartitions.ALL, TruePartitions.ALL, [1, 1, 1, 1]),
        (True, False, False, TruePartitions.ALL, TruePartitions.NONE, [0, 0, 1, 1]),
        (True, False, False, TruePartitions.NONE, TruePartitions.ALL, [0, 0, 1, 1]),
        (True, False, False, TruePartitions.ONE, TruePartitions.ALL, [0, 1, 1, 1]),
        (True, False, False, TruePartitions.ONE, TruePartitions.NONE, [0, 0, 0, 1]),
        # MIXED -> PARTITIONED
        (True, False, True, TruePartitions.ALL, TruePartitions.ALL, [2, 2, 2, 2]),
        (True, False, True, TruePartitions.ALL, TruePartitions.NONE, [0, 0, 2, 2]),
    ],
)
def test_logic(
    A_partitioned: bool,
    B_partitioned: bool,
    C_partitioned: bool,
    A_true_partitions: TruePartitions,
    B_true_partitions: TruePartitions,
    expected_result_sizes: Sequence[int],
) -> None:
    partitions_def_A = two_partitions_def if A_partitioned else None
    partitions_def_B = two_partitions_def if B_partitioned else None
    partitions_def_C = two_partitions_def if C_partitioned else None

    class TestDepCondition(DepSchedulingCondition):
        def dep_description(self) -> str:
            return "matches one of the provided asset partitions"

        def evaluate_for_dep_asset_partition(
            self,
            context: AssetConditionEvaluationContext,
            dep_asset_partition: AssetKeyPartitionKey,
        ) -> bool:
            return dep_asset_partition in {
                *A_true_partitions.asset_partitions(AssetKey("A"), partitions_def_A),
                *B_true_partitions.asset_partitions(AssetKey("B"), partitions_def_B),
            }

    for i, (dep, dep_partition) in enumerate(
        [
            (DepSelectionType.ALL, DepSelectionType.ALL),
            (DepSelectionType.ALL, DepSelectionType.ANY),
            (DepSelectionType.ANY, DepSelectionType.ALL),
            (DepSelectionType.ANY, DepSelectionType.ANY),
        ]
    ):
        dep_condition = TestDepCondition(
            dep_selection_type=dep,
            dep_partition_selection_type=dep_partition,
        )
        scenario_spec = (
            one_asset_depends_on_two.with_asset_properties(
                "A",
                partitions_def=partitions_def_A,
            )
            .with_asset_properties(
                "B",
                partitions_def=partitions_def_B,
            )
            .with_asset_properties(
                "C",
                partitions_def=partitions_def_C,
            )
        )
        state = AssetConditionScenarioState(scenario_spec, asset_condition=dep_condition)
        state, result = state.evaluate("C")

        assert result.true_subset.size == expected_result_sizes[i], f"{dep}, {dep_partition}"

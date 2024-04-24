import pytest
from dagster import StaticPartitionMapping, StaticPartitionsDefinition
from dagster._core.definitions.partition import DefaultPartitionsSubset
from dagster._serdes.serdes import (
    deserialize_value,
    serialize_value,
)


def test_single_valued_static_mapping():
    upstream_parts = StaticPartitionsDefinition(["p1", "p2", "p3", "q1", "q2", "r1"])
    downstream_parts = StaticPartitionsDefinition(["p", "q", "r"])
    mapping = StaticPartitionMapping({"p1": "p", "p2": "p", "p3": "p", "r1": "r"})

    result = mapping.get_downstream_partitions_for_partitions(
        upstream_partitions_subset=upstream_parts.empty_subset().with_partition_keys(
            ["p1", "p3", "q2", "r1"]
        ),
        upstream_partitions_def=upstream_parts,
        downstream_partitions_def=downstream_parts,
    )

    assert result == DefaultPartitionsSubset({"p", "r"})

    result = mapping.get_upstream_mapped_partitions_result_for_partitions(
        downstream_partitions_subset=downstream_parts.empty_subset().with_partition_keys(
            ["p", "q"]
        ),
        downstream_partitions_def=downstream_parts,
        upstream_partitions_def=upstream_parts,
    )

    assert result.partitions_subset == DefaultPartitionsSubset({"p1", "p2", "p3"})


def test_multi_valued_static_mapping():
    upstream_parts = StaticPartitionsDefinition(["p", "q1", "q2", "r"])
    downstream_parts = StaticPartitionsDefinition(["p1", "p2", "p3", "q", "r1"])

    mapping = StaticPartitionMapping({"p": {"p1", "p2", "p3"}, "q1": "q", "q2": "q"})

    result = mapping.get_downstream_partitions_for_partitions(
        upstream_partitions_subset=upstream_parts.empty_subset().with_partition_keys(["p", "r"]),
        upstream_partitions_def=upstream_parts,
        downstream_partitions_def=downstream_parts,
    )

    assert result == DefaultPartitionsSubset({"p1", "p2", "p3"})

    result = mapping.get_upstream_mapped_partitions_result_for_partitions(
        downstream_partitions_subset=downstream_parts.empty_subset().with_partition_keys(
            ["p2", "p3", "q"]
        ),
        downstream_partitions_def=downstream_parts,
        upstream_partitions_def=upstream_parts,
    )

    assert result.partitions_subset == DefaultPartitionsSubset({"p", "q1", "q2"})


def test_error_on_extra_keys_in_mapping():
    upstream_parts = StaticPartitionsDefinition(["p", "q"])
    downstream_parts = StaticPartitionsDefinition(["p", "q"])

    with pytest.raises(ValueError, match="OTHER"):
        StaticPartitionMapping(
            {"p": "p", "q": {"q", "OTHER"}}
        ).get_downstream_partitions_for_partitions(
            upstream_partitions_subset=upstream_parts.empty_subset(),
            upstream_partitions_def=upstream_parts,
            downstream_partitions_def=downstream_parts,
        )

    with pytest.raises(ValueError, match="OTHER"):
        StaticPartitionMapping(
            {"p": "p", "q": "q", "OTHER": "q"}
        ).get_upstream_mapped_partitions_result_for_partitions(
            downstream_partitions_subset=downstream_parts.empty_subset(),
            downstream_partitions_def=downstream_parts,
            upstream_partitions_def=upstream_parts,
        )


def test_static_partition_mapping_serdes():
    mapping = StaticPartitionMapping(
        {"p1": "p", "p2": "p", "p3": "p", "q": ["q1", "q2"], "r1": "r"}
    )
    ser = serialize_value(mapping)
    deser = deserialize_value(ser, StaticPartitionMapping)
    assert mapping == deser

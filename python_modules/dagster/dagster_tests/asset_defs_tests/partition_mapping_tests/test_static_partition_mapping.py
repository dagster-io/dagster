import dagster as dg
import pytest
from dagster._core.definitions.partitions.subset import DefaultPartitionsSubset


def test_single_valued_static_mapping():
    upstream_parts = dg.StaticPartitionsDefinition(["p1", "p2", "p3", "q1", "q2", "r1"])
    downstream_parts = dg.StaticPartitionsDefinition(["p", "q", "r"])
    mapping = dg.StaticPartitionMapping({"p1": "p", "p2": "p", "p3": "p", "r1": "r"})

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
    upstream_parts = dg.StaticPartitionsDefinition(["p", "q1", "q2", "r"])
    downstream_parts = dg.StaticPartitionsDefinition(["p1", "p2", "p3", "q", "r1"])

    mapping = dg.StaticPartitionMapping({"p": {"p1", "p2", "p3"}, "q1": "q", "q2": "q"})

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
    upstream_parts = dg.StaticPartitionsDefinition(["p", "q"])
    downstream_parts = dg.StaticPartitionsDefinition(["p", "q"])

    with pytest.raises(ValueError, match="OTHER"):
        dg.StaticPartitionMapping(
            {"p": "p", "q": {"q", "OTHER"}}
        ).get_downstream_partitions_for_partitions(
            upstream_partitions_subset=upstream_parts.empty_subset(),
            upstream_partitions_def=upstream_parts,
            downstream_partitions_def=downstream_parts,
        )

    with pytest.raises(ValueError, match="OTHER"):
        dg.StaticPartitionMapping({"p": "p", "q": {"q", "OTHER"}}).validate_partition_mapping(
            upstream_partitions_def=upstream_parts,
            downstream_partitions_def=downstream_parts,
        )

    with pytest.raises(ValueError, match="OTHER"):
        dg.StaticPartitionMapping(
            {"p": "p", "q": "q", "OTHER": "q"}
        ).get_upstream_mapped_partitions_result_for_partitions(
            downstream_partitions_subset=downstream_parts.empty_subset(),
            downstream_partitions_def=downstream_parts,
            upstream_partitions_def=upstream_parts,
        )

    with pytest.raises(ValueError, match="OTHER"):
        dg.StaticPartitionMapping({"p": "p", "q": "q", "OTHER": "q"}).validate_partition_mapping(
            downstream_partitions_def=downstream_parts,
            upstream_partitions_def=upstream_parts,
        )


def test_static_partition_mapping_serdes():
    mapping = dg.StaticPartitionMapping(
        {"p1": "p", "p2": "p", "p3": "p", "q": ["q1", "q2"], "r1": "r"}
    )
    ser = dg.serialize_value(mapping)
    deser = dg.deserialize_value(ser, dg.StaticPartitionMapping)
    assert mapping == deser

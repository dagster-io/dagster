import pytest
from dagster import MultiPartitionKey, MultiPartitionsDefinition, StaticPartitionsDefinition
from dagster._check import CheckError
from dagster._core.definitions.partition import DefaultPartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import MultiToSingleDimensionPartitionMapping


def test_get_downstream_partitions_single_key_in_range():
    single_dimension_def = StaticPartitionsDefinition(["a", "b", "c"])
    multipartitions_def = MultiPartitionsDefinition(
        {"abc": single_dimension_def, "123": StaticPartitionsDefinition(["1", "2", "3"])}
    )

    single_dimension_subset = single_dimension_def.empty_subset().with_partition_key_range(
        PartitionKeyRange("a", "a")
    )
    result = MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=single_dimension_subset,
        downstream_partitions_def=multipartitions_def,
    )
    multipartitions_subset = multipartitions_def.empty_subset().with_partition_keys(
        {
            MultiPartitionKey({"abc": "a", "123": "1"}),
            MultiPartitionKey({"abc": "a", "123": "2"}),
            MultiPartitionKey({"abc": "a", "123": "3"}),
        },
    )
    assert result == multipartitions_subset

    result = MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=multipartitions_subset,
        downstream_partitions_def=single_dimension_def,
    )
    assert result == single_dimension_subset

    multipartitions_def = MultiPartitionsDefinition(
        {"abc": single_dimension_def, "xyz": StaticPartitionsDefinition(["x", "y", "z"])}
    )

    result = MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=single_dimension_def.empty_subset().with_partition_key_range(
            PartitionKeyRange("b", "b")
        ),
        downstream_partitions_def=multipartitions_def,
    )
    assert result == DefaultPartitionsSubset(
        multipartitions_def,
        {
            MultiPartitionKey({"abc": "b", "xyz": "x"}),
            MultiPartitionKey({"abc": "b", "xyz": "y"}),
            MultiPartitionKey({"abc": "b", "xyz": "z"}),
        },
    )


def test_get_downstream_partitions_multiple_keys_in_range():
    single_dimension_def = StaticPartitionsDefinition(["a", "b", "c"])
    multipartitions_def = MultiPartitionsDefinition(
        {"abc": single_dimension_def, "123": StaticPartitionsDefinition(["1", "2", "3"])}
    )
    single_dimension_subset = single_dimension_def.empty_subset().with_partition_key_range(
        PartitionKeyRange("a", "b")
    )
    multipartitions_subset = multipartitions_def.empty_subset().with_partition_keys(
        {
            MultiPartitionKey({"abc": "a", "123": "1"}),
            MultiPartitionKey({"abc": "a", "123": "2"}),
            MultiPartitionKey({"abc": "a", "123": "3"}),
            MultiPartitionKey({"abc": "b", "123": "1"}),
            MultiPartitionKey({"abc": "b", "123": "2"}),
            MultiPartitionKey({"abc": "b", "123": "3"}),
        },
    )

    result = MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=single_dimension_subset,
        downstream_partitions_def=multipartitions_def,
    )
    assert result == multipartitions_subset

    result = MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=multipartitions_subset,
        downstream_partitions_def=single_dimension_def,
    )
    assert result == single_dimension_subset


single_dimension_def = StaticPartitionsDefinition(["a", "b", "c"])
multipartitions_def = MultiPartitionsDefinition(
    {"abc": single_dimension_def, "123": StaticPartitionsDefinition(["1", "2", "3"])}
)


@pytest.mark.parametrize(
    "upstream_partitions_def,upstream_partitions_subset,downstream_partitions_subset",
    [
        (
            single_dimension_def,
            single_dimension_def.empty_subset().with_partition_keys({"a"}),
            multipartitions_def.empty_subset().with_partition_key_range(
                PartitionKeyRange(
                    MultiPartitionKey({"abc": "a", "123": "1"}),
                    MultiPartitionKey({"abc": "a", "123": "1"}),
                )
            ),
        ),
        (
            single_dimension_def,
            single_dimension_def.empty_subset().with_partition_keys({"a", "b"}),
            multipartitions_def.empty_subset().with_partition_keys(
                {
                    MultiPartitionKey({"abc": "b", "123": "2"}),
                    MultiPartitionKey({"abc": "a", "123": "2"}),
                }
            ),
        ),
        (
            multipartitions_def,
            multipartitions_def.empty_subset().with_partition_keys(
                {
                    MultiPartitionKey({"abc": "a", "123": "1"}),
                    MultiPartitionKey({"abc": "a", "123": "2"}),
                    MultiPartitionKey({"abc": "a", "123": "3"}),
                }
            ),
            single_dimension_def.empty_subset().with_partition_keys({"a"}),
        ),
        (
            multipartitions_def,
            multipartitions_def.empty_subset().with_partition_keys(
                {
                    MultiPartitionKey({"abc": "a", "123": "1"}),
                    MultiPartitionKey({"abc": "a", "123": "2"}),
                    MultiPartitionKey({"abc": "a", "123": "3"}),
                    MultiPartitionKey({"abc": "b", "123": "1"}),
                    MultiPartitionKey({"abc": "b", "123": "2"}),
                    MultiPartitionKey({"abc": "b", "123": "3"}),
                }
            ),
            single_dimension_def.empty_subset().with_partition_keys({"a", "b"}),
        ),
    ],
)
def test_get_upstream_single_dimension_to_multi_partition_mapping(
    upstream_partitions_def,
    upstream_partitions_subset,
    downstream_partitions_subset,
):
    assert (
        MultiToSingleDimensionPartitionMapping().get_upstream_partitions_for_partitions(
            downstream_partitions_subset,
            upstream_partitions_def,
        )
        == upstream_partitions_subset
    )


def test_error_thrown_when_no_partition_dimension_name_provided():
    multipartitions_def = MultiPartitionsDefinition(
        {
            "a": StaticPartitionsDefinition(["1", "2", "3"]),
            "b": StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )

    single_dimension_def = StaticPartitionsDefinition(["1", "2", "3"])

    with pytest.raises(CheckError, match="dimension name must be specified"):
        MultiToSingleDimensionPartitionMapping().get_upstream_partitions_for_partitions(
            multipartitions_def.empty_subset().with_partition_key_range(
                PartitionKeyRange(
                    MultiPartitionKey({"a": "1", "b": "1"}),
                    MultiPartitionKey({"a": "1", "b": "1"}),
                )
            ),
            single_dimension_def,
        )

    with pytest.raises(CheckError, match="dimension name must be specified"):
        MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
            multipartitions_def.empty_subset().with_partition_key_range(
                PartitionKeyRange(
                    MultiPartitionKey({"a": "1", "b": "1"}),
                    MultiPartitionKey({"a": "1", "b": "1"}),
                )
            ),
            single_dimension_def,
        )

    with pytest.raises(CheckError, match="dimension name must be specified"):
        MultiToSingleDimensionPartitionMapping().get_upstream_partitions_for_partitions(
            single_dimension_def.empty_subset().with_partition_key_range(
                PartitionKeyRange("1", "1")
            ),
            multipartitions_def,
        )

    with pytest.raises(CheckError, match="dimension name must be specified"):
        MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
            single_dimension_def.empty_subset().with_partition_key_range(
                PartitionKeyRange("1", "1")
            ),
            multipartitions_def,
        )

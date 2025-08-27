from datetime import datetime, timedelta

import dagster as dg
import pytest
from dagster import AssetExecutionContext, DagsterInstance
from dagster._check import CheckError
from dagster._core.definitions.partitions.subset import DefaultPartitionsSubset


def test_get_downstream_partitions_single_key_in_range():
    single_dimension_def = dg.StaticPartitionsDefinition(["a", "b", "c"])
    multipartitions_def = dg.MultiPartitionsDefinition(
        {"abc": single_dimension_def, "123": dg.StaticPartitionsDefinition(["1", "2", "3"])}
    )

    single_dimension_subset = single_dimension_def.empty_subset().with_partition_key_range(
        single_dimension_def, dg.PartitionKeyRange("a", "a")
    )
    result = dg.MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=single_dimension_subset,
        upstream_partitions_def=single_dimension_def,
        downstream_partitions_def=multipartitions_def,
    )
    multipartitions_subset = multipartitions_def.empty_subset().with_partition_keys(
        {
            dg.MultiPartitionKey({"abc": "a", "123": "1"}),
            dg.MultiPartitionKey({"abc": "a", "123": "2"}),
            dg.MultiPartitionKey({"abc": "a", "123": "3"}),
        },
    )
    assert result == multipartitions_subset

    result = dg.MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=multipartitions_subset,
        upstream_partitions_def=multipartitions_def,
        downstream_partitions_def=single_dimension_def,
    )
    assert result == single_dimension_subset

    multipartitions_def = dg.MultiPartitionsDefinition(
        {"abc": single_dimension_def, "xyz": dg.StaticPartitionsDefinition(["x", "y", "z"])}
    )

    result = dg.MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=single_dimension_def.empty_subset().with_partition_key_range(
            partitions_def=single_dimension_def, partition_key_range=dg.PartitionKeyRange("b", "b")
        ),
        upstream_partitions_def=single_dimension_def,
        downstream_partitions_def=multipartitions_def,
    )
    assert result == DefaultPartitionsSubset(
        {
            dg.MultiPartitionKey({"abc": "b", "xyz": "x"}),
            dg.MultiPartitionKey({"abc": "b", "xyz": "y"}),
            dg.MultiPartitionKey({"abc": "b", "xyz": "z"}),
        },
    )


def test_get_downstream_partitions_multiple_keys_in_range():
    single_dimension_def = dg.StaticPartitionsDefinition(["a", "b", "c"])
    multipartitions_def = dg.MultiPartitionsDefinition(
        {"abc": single_dimension_def, "123": dg.StaticPartitionsDefinition(["1", "2", "3"])}
    )
    single_dimension_subset = single_dimension_def.empty_subset().with_partition_key_range(
        single_dimension_def, dg.PartitionKeyRange("a", "b")
    )
    multipartitions_subset = multipartitions_def.empty_subset().with_partition_keys(
        {
            dg.MultiPartitionKey({"abc": "a", "123": "1"}),
            dg.MultiPartitionKey({"abc": "a", "123": "2"}),
            dg.MultiPartitionKey({"abc": "a", "123": "3"}),
            dg.MultiPartitionKey({"abc": "b", "123": "1"}),
            dg.MultiPartitionKey({"abc": "b", "123": "2"}),
            dg.MultiPartitionKey({"abc": "b", "123": "3"}),
        },
    )

    result = dg.MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=single_dimension_subset,
        upstream_partitions_def=single_dimension_def,
        downstream_partitions_def=multipartitions_def,
    )
    assert result == multipartitions_subset

    result = dg.MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
        upstream_partitions_subset=multipartitions_subset,
        upstream_partitions_def=multipartitions_def,
        downstream_partitions_def=single_dimension_def,
    )
    assert result == single_dimension_subset


static_partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c"])
static_multipartitions_def = dg.MultiPartitionsDefinition(
    {"abc": static_partitions_def, "123": dg.StaticPartitionsDefinition(["1", "2", "3"])}
)
daily_partitions_def = dg.DailyPartitionsDefinition("2023-01-01")
weekly_multipartitions_def = dg.MultiPartitionsDefinition(
    {
        "week": dg.WeeklyPartitionsDefinition("2023-01-01"),
        "ab": dg.StaticPartitionsDefinition(["a", "b"]),
    }
)


@pytest.mark.parametrize(
    "upstream_partitions_def,upstream_partitions_subset,downstream_partitions_subset,downstream_partitions_def",
    [
        (
            static_partitions_def,
            static_partitions_def.empty_subset().with_partition_keys({"a"}),
            static_multipartitions_def.empty_subset().with_partition_key_range(
                static_multipartitions_def,
                dg.PartitionKeyRange(
                    dg.MultiPartitionKey({"abc": "a", "123": "1"}),
                    dg.MultiPartitionKey({"abc": "a", "123": "1"}),
                ),
            ),
            static_multipartitions_def,
        ),
        (
            static_partitions_def,
            static_partitions_def.empty_subset().with_partition_keys({"a", "b"}),
            static_multipartitions_def.empty_subset().with_partition_keys(
                {
                    dg.MultiPartitionKey({"abc": "b", "123": "2"}),
                    dg.MultiPartitionKey({"abc": "a", "123": "2"}),
                }
            ),
            static_multipartitions_def,
        ),
        (
            static_multipartitions_def,
            static_multipartitions_def.empty_subset().with_partition_keys(
                {
                    dg.MultiPartitionKey({"abc": "a", "123": "1"}),
                    dg.MultiPartitionKey({"abc": "a", "123": "2"}),
                    dg.MultiPartitionKey({"abc": "a", "123": "3"}),
                }
            ),
            static_partitions_def.empty_subset().with_partition_keys({"a"}),
            static_partitions_def,
        ),
        (
            static_multipartitions_def,
            static_multipartitions_def.empty_subset().with_partition_keys(
                {
                    dg.MultiPartitionKey({"abc": "a", "123": "1"}),
                    dg.MultiPartitionKey({"abc": "a", "123": "2"}),
                    dg.MultiPartitionKey({"abc": "a", "123": "3"}),
                    dg.MultiPartitionKey({"abc": "b", "123": "1"}),
                    dg.MultiPartitionKey({"abc": "b", "123": "2"}),
                    dg.MultiPartitionKey({"abc": "b", "123": "3"}),
                }
            ),
            static_partitions_def.empty_subset().with_partition_keys({"a", "b"}),
            static_partitions_def,
        ),
        (
            daily_partitions_def,
            daily_partitions_def.empty_subset()
            .with_partition_key_range(
                daily_partitions_def, dg.PartitionKeyRange(start="2023-01-08", end="2023-01-14")
            )
            .with_partition_key_range(
                daily_partitions_def, dg.PartitionKeyRange(start="2023-01-29", end="2023-02-04")
            ),
            weekly_multipartitions_def.empty_subset().with_partition_keys(
                {
                    dg.MultiPartitionKey({"ab": "a", "week": "2023-01-08"}),
                    dg.MultiPartitionKey({"ab": "b", "week": "2023-01-08"}),
                    dg.MultiPartitionKey({"ab": "a", "week": "2023-01-29"}),
                    dg.MultiPartitionKey({"ab": "b", "week": "2023-01-29"}),
                }
            ),
            weekly_multipartitions_def,
        ),
    ],
)
def test_get_upstream_single_dimension_to_multi_partition_mapping(
    upstream_partitions_def,
    upstream_partitions_subset,
    downstream_partitions_subset,
    downstream_partitions_def,
):
    assert (
        dg.MultiToSingleDimensionPartitionMapping()
        .get_upstream_mapped_partitions_result_for_partitions(
            downstream_partitions_subset,
            downstream_partitions_def,
            upstream_partitions_def,
        )
        .partitions_subset
        == upstream_partitions_subset
    )


def test_error_thrown_when_no_partition_dimension_name_provided():
    multipartitions_def = dg.MultiPartitionsDefinition(
        {
            "a": dg.StaticPartitionsDefinition(["1", "2", "3"]),
            "b": dg.StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )

    single_dimension_def = dg.StaticPartitionsDefinition(["1", "2", "3"])

    with pytest.raises(CheckError, match="dimension name must be specified"):
        dg.MultiToSingleDimensionPartitionMapping().get_upstream_mapped_partitions_result_for_partitions(
            multipartitions_def.empty_subset().with_partition_key_range(
                multipartitions_def,
                dg.PartitionKeyRange(
                    dg.MultiPartitionKey({"a": "1", "b": "1"}),
                    dg.MultiPartitionKey({"a": "1", "b": "1"}),
                ),
            ),
            multipartitions_def,
            single_dimension_def,
        )

    with pytest.raises(CheckError, match="dimension name must be specified"):
        dg.MultiToSingleDimensionPartitionMapping().validate_partition_mapping(
            multipartitions_def,
            single_dimension_def,
        )

    with pytest.raises(CheckError, match="dimension name must be specified"):
        dg.MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
            multipartitions_def.empty_subset().with_partition_key_range(
                multipartitions_def,
                dg.PartitionKeyRange(
                    dg.MultiPartitionKey({"a": "1", "b": "1"}),
                    dg.MultiPartitionKey({"a": "1", "b": "1"}),
                ),
            ),
            multipartitions_def,
            single_dimension_def,
        )

    with pytest.raises(CheckError, match="dimension name must be specified"):
        dg.MultiToSingleDimensionPartitionMapping().get_upstream_mapped_partitions_result_for_partitions(
            single_dimension_def.empty_subset().with_partition_key_range(
                single_dimension_def, dg.PartitionKeyRange("1", "1")
            ),
            single_dimension_def,
            multipartitions_def,
        )

    with pytest.raises(CheckError, match="dimension name must be specified"):
        dg.MultiToSingleDimensionPartitionMapping().get_downstream_partitions_for_partitions(
            single_dimension_def.empty_subset().with_partition_key_range(
                single_dimension_def, dg.PartitionKeyRange("1", "1")
            ),
            single_dimension_def,
            multipartitions_def,
        )


upstream_and_downstream_tests = [
    (
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": dg.WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionMapping(
            {
                "abc": dg.DimensionPartitionMapping(
                    dimension_name="abc", partition_mapping=dg.IdentityPartitionMapping()
                ),
                "daily": dg.DimensionPartitionMapping(
                    dimension_name="weekly",
                    partition_mapping=dg.TimeWindowPartitionMapping(),
                ),
            }
        ),
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("a", "2023-01-01"),
                ("a", "2023-01-02"),
                ("a", "2023-01-03"),
                ("a", "2023-01-04"),
                ("a", "2023-01-05"),
                ("a", "2023-01-06"),
                ("a", "2023-01-07"),
            ]
        ],
        [dg.MultiPartitionKey({"abc": "a", "weekly": "2023-01-01"})],
    ),
    (
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": dg.WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionMapping(
            {
                "abc": dg.DimensionPartitionMapping(
                    dimension_name="abc", partition_mapping=dg.IdentityPartitionMapping()
                ),
                "daily": dg.DimensionPartitionMapping(
                    dimension_name="weekly",
                    partition_mapping=dg.TimeWindowPartitionMapping(),
                ),
            },
        ),
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("a", "2023-01-01"),
                ("a", "2023-01-02"),
                ("a", "2023-01-03"),
                ("a", "2023-01-04"),
                ("a", "2023-01-05"),
                ("a", "2023-01-06"),
                ("a", "2023-01-07"),
                ("b", "2023-01-08"),
                ("b", "2023-01-09"),
                ("b", "2023-01-10"),
                ("b", "2023-01-11"),
                ("b", "2023-01-12"),
                ("b", "2023-01-13"),
                ("b", "2023-01-14"),
            ]
        ],
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("a", "2023-01-01"),
                ("b", "2023-01-08"),
            ]
        ],
    ),
    (
        dg.MultiPartitionsDefinition(
            {
                "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionMapping(
            {
                "daily": dg.DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=dg.IdentityPartitionMapping(),
                ),
            },
        ),
        [
            dg.MultiPartitionKey({"123": values[0], "daily": values[1]})
            for values in [
                ("1", "2023-01-01"),
                ("2", "2023-01-01"),
                ("3", "2023-01-01"),
                ("1", "2023-01-02"),
                ("2", "2023-01-02"),
                ("3", "2023-01-02"),
            ]
        ],
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("a", "2023-01-01"),
                ("b", "2023-01-01"),
                ("c", "2023-01-01"),
                ("a", "2023-01-02"),
                ("b", "2023-01-02"),
                ("c", "2023-01-02"),
            ]
        ],
    ),
    (
        dg.MultiPartitionsDefinition(
            {
                "12": dg.StaticPartitionsDefinition(["1", "2"]),
                "xy": dg.StaticPartitionsDefinition(["x", "y"]),
            }
        ),
        dg.MultiPartitionsDefinition(
            {
                "ab": dg.StaticPartitionsDefinition(["a", "b"]),
                "01": dg.StaticPartitionsDefinition(["0", "1"]),
            }
        ),
        dg.MultiPartitionMapping({}),
        [
            dg.MultiPartitionKey({"12": values[0], "xy": values[1]})
            for values in [
                ("1", "x"),
                ("2", "y"),
                ("1", "y"),
                ("2", "x"),
            ]
        ],
        [
            dg.MultiPartitionKey({"ab": values[0], "01": values[1]})
            for values in [
                ("a", "0"),
                ("a", "1"),
                ("b", "0"),
                ("b", "1"),
            ]
        ],
    ),
]

upstream_only_tests = [
    (
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": dg.WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionsDefinition(
            {
                "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionMapping(
            {
                "abc": dg.DimensionPartitionMapping(
                    dimension_name="123",
                    partition_mapping=dg.SpecificPartitionsPartitionMapping(["c"]),
                ),
                "weekly": dg.DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=dg.TimeWindowPartitionMapping(),
                ),
            },
        ),
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("c", "2023-01-01"),
            ]
        ],
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("1", "2023-01-01"),
                ("3", "2023-01-02"),
            ]
        ],
    ),
    (
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": dg.WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionsDefinition(
            {
                "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionMapping(
            {
                "abc": dg.DimensionPartitionMapping(
                    dimension_name="123",
                    partition_mapping=dg.SpecificPartitionsPartitionMapping(["c"]),
                ),
                "weekly": dg.DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=dg.TimeWindowPartitionMapping(),
                ),
            }
        ),
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("c", "2023-01-01"),
                ("c", "2023-01-08"),
            ]
        ],
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("1", "2023-01-01"),
                ("1", "2023-01-02"),
                ("1", "2023-01-03"),
                ("1", "2023-01-04"),
                ("1", "2023-01-05"),
                ("1", "2023-01-06"),
                ("1", "2023-01-07"),
                ("3", "2023-01-08"),
                ("3", "2023-01-09"),
                ("3", "2023-01-10"),
                ("3", "2023-01-11"),
                ("3", "2023-01-12"),
                ("3", "2023-01-13"),
                ("3", "2023-01-14"),
            ]
        ],
    ),
    (
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionsDefinition(
            {
                "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionMapping(
            {
                "abc": dg.DimensionPartitionMapping(
                    dimension_name="123", partition_mapping=dg.AllPartitionMapping()
                ),
                "daily": dg.DimensionPartitionMapping(
                    dimension_name="daily", partition_mapping=dg.IdentityPartitionMapping()
                ),
            }
        ),
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("a", "2023-01-01"),
                ("b", "2023-01-01"),
                ("c", "2023-01-01"),
            ]
        ],
        [
            dg.MultiPartitionKey({"123": values[0], "daily": values[1]})
            for values in [
                ("1", "2023-01-01"),
            ]
        ],
    ),
]


downstream_only_tests = [
    (
        dg.MultiPartitionsDefinition(
            {
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": dg.WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionsDefinition(
            {
                "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": dg.DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        dg.MultiPartitionMapping(
            {
                "abc": dg.DimensionPartitionMapping(
                    dimension_name="123",
                    partition_mapping=dg.StaticPartitionMapping({"a": "1", "b": "2", "c": "3"}),
                ),
                "weekly": dg.DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=dg.TimeWindowPartitionMapping(),
                ),
            }
        ),
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("c", "2023-01-01"),
                ("a", "2023-01-08"),
            ]
        ],
        [
            dg.MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("3", "2023-01-01"),
                ("3", "2023-01-02"),
                ("3", "2023-01-03"),
                ("3", "2023-01-04"),
                ("3", "2023-01-05"),
                ("3", "2023-01-06"),
                ("3", "2023-01-07"),
                ("1", "2023-01-08"),
                ("1", "2023-01-09"),
                ("1", "2023-01-10"),
                ("1", "2023-01-11"),
                ("1", "2023-01-12"),
                ("1", "2023-01-13"),
                ("1", "2023-01-14"),
            ]
        ],
    ),
]


@pytest.mark.parametrize(
    "upstream_partitions_def,downstream_partitions_def,partitions_mapping,upstream_partition_keys,downstream_partition_keys",
    [
        *upstream_and_downstream_tests,
        *upstream_only_tests,
    ],
)
def test_multipartitions_mapping_get_upstream_partitions(
    upstream_partitions_def,
    downstream_partitions_def,
    partitions_mapping,
    upstream_partition_keys,
    downstream_partition_keys,
):
    result = partitions_mapping.get_upstream_mapped_partitions_result_for_partitions(
        downstream_partitions_def.empty_subset().with_partition_keys(downstream_partition_keys),
        downstream_partitions_def,
        upstream_partitions_def,
    )
    assert result.partitions_subset.get_partition_keys() == set(upstream_partition_keys)


def test_multipartitions_required_but_invalid_upstream_partitions():
    may_multipartitions_def = dg.MultiPartitionsDefinition(
        {
            "time": dg.DailyPartitionsDefinition("2023-05-01"),
            "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )
    june_multipartitions_def = dg.MultiPartitionsDefinition(
        {
            "time": dg.DailyPartitionsDefinition("2023-06-01"),
            "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
        }
    )
    result = dg.MultiPartitionMapping(
        {
            "123": dg.DimensionPartitionMapping(
                dimension_name="123",
                partition_mapping=dg.IdentityPartitionMapping(),
            ),
            "time": dg.DimensionPartitionMapping(
                dimension_name="time",
                partition_mapping=dg.TimeWindowPartitionMapping(),
            ),
        }
    ).get_upstream_mapped_partitions_result_for_partitions(
        may_multipartitions_def.empty_subset().with_partition_keys(
            [
                dg.MultiPartitionKey({"time": "2023-05-01", "123": "1"}),
                dg.MultiPartitionKey({"time": "2023-06-01", "123": "1"}),
            ]
        ),
        may_multipartitions_def,
        june_multipartitions_def,
    )
    assert result.partitions_subset.get_partition_keys() == set(
        [dg.MultiPartitionKey({"time": "2023-06-01", "123": "1"})]
    )
    assert result.required_but_nonexistent_subset.get_partition_keys() == {"2023-05-01"}
    assert (
        str(result.required_but_nonexistent_subset)
        == "DefaultPartitionsSubset(subset={'2023-05-01'})"
    )

    assert result.required_but_nonexistent_partition_keys == ["2023-05-01"]


@pytest.mark.parametrize(
    "upstream_partitions_def,downstream_partitions_def,partitions_mapping,upstream_partition_keys,downstream_partition_keys",
    [
        *upstream_and_downstream_tests,
        *downstream_only_tests,
    ],
)
def test_multipartitions_mapping_get_downstream_partitions(
    upstream_partitions_def,
    downstream_partitions_def,
    partitions_mapping,
    upstream_partition_keys,
    downstream_partition_keys,
):
    assert partitions_mapping.get_downstream_partitions_for_partitions(
        upstream_partitions_def.empty_subset().with_partition_keys(upstream_partition_keys),
        upstream_partitions_def,
        downstream_partitions_def,
    ).get_partition_keys() == set(downstream_partition_keys)


def test_multipartitions_mapping_dynamic():
    mapping = dg.MultiPartitionMapping(
        {"dynamic": dg.DimensionPartitionMapping("dynamic", dg.IdentityPartitionMapping())}
    )
    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("dynamic", ["a", "b", "c"])
        downstream_partitions_def = dg.MultiPartitionsDefinition(
            {
                "dynamic": dg.DynamicPartitionsDefinition(name="dynamic"),
                "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
            }
        )
        upstream_partitions_def = dg.MultiPartitionsDefinition(
            {
                "dynamic": dg.DynamicPartitionsDefinition(name="dynamic"),
                "456": dg.StaticPartitionsDefinition(["4", "5", "6"]),
            }
        )
        mapped_partitions_result = mapping.get_upstream_mapped_partitions_result_for_partitions(
            downstream_partitions_def.empty_subset().with_partition_keys(
                [dg.MultiPartitionKey({"dynamic": "a", "123": "1"})]
            ),
            downstream_partitions_def,
            upstream_partitions_def,
            dynamic_partitions_store=instance,
        )
        assert mapped_partitions_result.partitions_subset.get_partition_keys() == set(
            [
                dg.MultiPartitionKey({"dynamic": val[1], "abc": val[0]})
                for val in [("4", "a"), ("5", "a"), ("6", "a")]
            ]
        )


def test_error_multipartitions_mapping():
    weekly_abc = dg.MultiPartitionsDefinition(
        {
            "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
            "weekly": dg.WeeklyPartitionsDefinition("2023-01-01"),
        }
    )
    daily_123 = dg.MultiPartitionsDefinition(
        {
            "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
            "daily": dg.DailyPartitionsDefinition("2023-01-01"),
        }
    )

    error_mapping = dg.MultiPartitionMapping(
        {
            "nonexistent dimension": dg.DimensionPartitionMapping(
                "other nonexistent dimension", dg.SpecificPartitionsPartitionMapping(["c"])
            )
        }
    )

    with pytest.raises(
        CheckError, match="upstream dimension name that is not in the upstream partitions def"
    ):
        error_mapping.get_upstream_mapped_partitions_result_for_partitions(
            weekly_abc.empty_subset(), weekly_abc, daily_123
        )

    with pytest.raises(
        CheckError, match="upstream dimension name that is not in the upstream partitions def"
    ):
        error_mapping.validate_partition_mapping(weekly_abc, daily_123)


def test_multi_partition_mapping_with_asset_deps():
    partitions_def = dg.MultiPartitionsDefinition(
        {
            "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
            "time": dg.DailyPartitionsDefinition("2023-01-01"),
        }
    )

    ### With @asset and deps
    @dg.asset(partitions_def=partitions_def)
    def upstream():
        return

    mapping = dg.MultiPartitionMapping(
        {
            "123": dg.DimensionPartitionMapping(
                dimension_name="123",
                partition_mapping=dg.IdentityPartitionMapping(),
            ),
            "time": dg.DimensionPartitionMapping(
                dimension_name="time",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            ),
        }
    )

    @dg.asset(
        partitions_def=partitions_def, deps=[dg.AssetDep(upstream, partition_mapping=mapping)]
    )
    def downstream(context: AssetExecutionContext):
        upstream_mp_key = context.asset_partition_key_for_input("upstream")
        current_mp_key = context.partition_key

        if isinstance(upstream_mp_key, dg.MultiPartitionKey) and isinstance(
            current_mp_key, dg.MultiPartitionKey
        ):
            upstream_key = datetime.strptime(upstream_mp_key.keys_by_dimension["time"], "%Y-%m-%d")

            current_partition_key = datetime.strptime(
                current_mp_key.keys_by_dimension["time"], "%Y-%m-%d"
            )

            assert current_partition_key - upstream_key == timedelta(days=1)
        else:
            assert False, "partition keys for upstream and downstream should be MultiPartitionKeys"

        return

    dg.materialize(
        [upstream, downstream],
        partition_key=dg.MultiPartitionKey({"123": "1", "time": "2023-08-05"}),
    )

    assert downstream.get_partition_mapping(dg.AssetKey("upstream")) == mapping

    ### With @multi_asset and AssetSpec
    asset_1 = dg.AssetSpec(key="asset_1")
    asset_2 = dg.AssetSpec(key="asset_2")

    asset_1_partition_mapping = dg.MultiPartitionMapping(
        {
            "123": dg.DimensionPartitionMapping(
                dimension_name="123",
                partition_mapping=dg.IdentityPartitionMapping(),
            ),
            "time": dg.DimensionPartitionMapping(
                dimension_name="time",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            ),
        }
    )
    asset_2_partition_mapping = dg.MultiPartitionMapping(
        {
            "123": dg.DimensionPartitionMapping(
                dimension_name="123",
                partition_mapping=dg.IdentityPartitionMapping(),
            ),
            "time": dg.DimensionPartitionMapping(
                dimension_name="time",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-2, end_offset=-2),
            ),
        }
    )

    asset_3 = dg.AssetSpec(
        key="asset_3",
        deps=[
            dg.AssetDep(
                asset=asset_1,
                partition_mapping=asset_1_partition_mapping,
            ),
            dg.AssetDep(
                asset=asset_2,
                partition_mapping=asset_2_partition_mapping,
            ),
        ],
    )
    asset_4 = dg.AssetSpec(
        key="asset_4",
        deps=[
            dg.AssetDep(
                asset=asset_1,
                partition_mapping=asset_1_partition_mapping,
            ),
            dg.AssetDep(
                asset=asset_2,
                partition_mapping=asset_2_partition_mapping,
            ),
        ],
    )

    @dg.multi_asset(specs=[asset_1, asset_2], partitions_def=partitions_def)
    def multi_asset_1():
        return

    @dg.multi_asset(specs=[asset_3, asset_4], partitions_def=partitions_def)
    def multi_asset_2(context: AssetExecutionContext):
        asset_1_mp_key = context.asset_partition_key_for_input("asset_1")
        asset_2_mp_key = context.asset_partition_key_for_input("asset_2")
        current_mp_key = context.partition_key

        if (
            isinstance(asset_1_mp_key, dg.MultiPartitionKey)
            and isinstance(asset_2_mp_key, dg.MultiPartitionKey)
            and isinstance(current_mp_key, dg.MultiPartitionKey)
        ):
            asset_1_key = datetime.strptime(asset_1_mp_key.keys_by_dimension["time"], "%Y-%m-%d")
            asset_2_key = datetime.strptime(asset_2_mp_key.keys_by_dimension["time"], "%Y-%m-%d")

            current_partition_key = datetime.strptime(
                current_mp_key.keys_by_dimension["time"], "%Y-%m-%d"
            )

            assert current_partition_key - asset_1_key == timedelta(days=1)
            assert current_partition_key - asset_2_key == timedelta(days=2)
        else:
            assert False, (
                "partition keys for asset_1, asset_2, and multi_asset_2 should be MultiPartitionKeys"
            )

        return

    dg.materialize(
        [multi_asset_1, multi_asset_2],
        partition_key=dg.MultiPartitionKey({"123": "1", "time": "2023-08-05"}),
    )

    assert multi_asset_2.get_partition_mapping(dg.AssetKey("asset_1")) == asset_1_partition_mapping
    assert multi_asset_2.get_partition_mapping(dg.AssetKey("asset_2")) == asset_2_partition_mapping


def test_dynamic_dimension_multipartition_mapping():
    instance = DagsterInstance.ephemeral()

    foo = dg.DynamicPartitionsDefinition(name="foo")
    foo_bar = dg.MultiPartitionsDefinition(
        {
            "foo": foo,
            "bar": dg.DynamicPartitionsDefinition(name="bar"),
        }
    )

    instance.add_dynamic_partitions("foo", ["a", "b", "c"])
    instance.add_dynamic_partitions("bar", ["1", "2"])

    result = dg.MultiToSingleDimensionPartitionMapping().get_upstream_mapped_partitions_result_for_partitions(
        downstream_partitions_subset=foo.empty_subset().with_partition_keys(["a"]),
        downstream_partitions_def=foo,
        upstream_partitions_def=foo_bar,
        dynamic_partitions_store=instance,
    )
    assert result.partitions_subset == foo_bar.empty_subset().with_partition_keys(["2|a", "1|a"])


def test_description():
    description = dg.MultiPartitionMapping(
        {
            "abc": dg.DimensionPartitionMapping(
                dimension_name="abc", partition_mapping=dg.IdentityPartitionMapping()
            ),
            "daily": dg.DimensionPartitionMapping(
                dimension_name="weekly",
                partition_mapping=dg.TimeWindowPartitionMapping(),
            ),
        }
    ).description
    assert (
        "'abc' mapped to downstream dimension 'abc' using IdentityPartitionMapping" in description
    )
    assert (
        "'daily' mapped to downstream dimension 'weekly' using TimeWindowPartitionMapping"
        in description
    )

    assert dg.MultiPartitionMapping({}).description == ""

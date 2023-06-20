import pytest
from dagster import (
    AllPartitionMapping,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    IdentityPartitionMapping,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    SpecificPartitionsPartitionMapping,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    WeeklyPartitionsDefinition,
)
from dagster._check import CheckError
from dagster._core.definitions.partition import DefaultPartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import (
    DimensionPartitionMapping,
    MultiPartitionMapping,
    MultiToSingleDimensionPartitionMapping,
)
from dagster._core.test_utils import instance_for_test


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


upstream_and_downstream_tests = [
    (
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionMapping(
            {
                "abc": DimensionPartitionMapping(
                    dimension_name="abc", partition_mapping=IdentityPartitionMapping()
                ),
                "daily": DimensionPartitionMapping(
                    dimension_name="weekly",
                    partition_mapping=TimeWindowPartitionMapping(),
                ),
            }
        ),
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
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
        [MultiPartitionKey({"abc": "a", "weekly": "2023-01-01"})],
    ),
    (
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionMapping(
            {
                "abc": DimensionPartitionMapping(
                    dimension_name="abc", partition_mapping=IdentityPartitionMapping()
                ),
                "daily": DimensionPartitionMapping(
                    dimension_name="weekly",
                    partition_mapping=TimeWindowPartitionMapping(),
                ),
            },
        ),
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
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
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("a", "2023-01-01"),
                ("b", "2023-01-08"),
            ]
        ],
    ),
    (
        MultiPartitionsDefinition(
            {
                "123": StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionMapping(
            {
                "daily": DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=IdentityPartitionMapping(),
                ),
            },
        ),
        [
            MultiPartitionKey({"123": values[0], "daily": values[1]})
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
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
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
        MultiPartitionsDefinition(
            {
                "12": StaticPartitionsDefinition(["1", "2"]),
                "xy": StaticPartitionsDefinition(["x", "y"]),
            }
        ),
        MultiPartitionsDefinition(
            {
                "ab": StaticPartitionsDefinition(["a", "b"]),
                "01": StaticPartitionsDefinition(["0", "1"]),
            }
        ),
        MultiPartitionMapping({}),
        [
            MultiPartitionKey({"12": values[0], "xy": values[1]})
            for values in [
                ("1", "x"),
                ("2", "y"),
                ("1", "y"),
                ("2", "x"),
            ]
        ],
        [
            MultiPartitionKey({"ab": values[0], "01": values[1]})
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
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionsDefinition(
            {
                "123": StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionMapping(
            {
                "abc": DimensionPartitionMapping(
                    dimension_name="123",
                    partition_mapping=SpecificPartitionsPartitionMapping(["c"]),
                ),
                "weekly": DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=TimeWindowPartitionMapping(),
                ),
            },
        ),
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("c", "2023-01-01"),
            ]
        ],
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("1", "2023-01-01"),
                ("3", "2023-01-02"),
            ]
        ],
    ),
    (
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionsDefinition(
            {
                "123": StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionMapping(
            {
                "abc": DimensionPartitionMapping(
                    dimension_name="123",
                    partition_mapping=SpecificPartitionsPartitionMapping(["c"]),
                ),
                "weekly": DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=TimeWindowPartitionMapping(),
                ),
            }
        ),
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("c", "2023-01-01"),
                ("c", "2023-01-08"),
            ]
        ],
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
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
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionsDefinition(
            {
                "123": StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionMapping(
            {
                "abc": DimensionPartitionMapping(
                    dimension_name="123", partition_mapping=AllPartitionMapping()
                ),
                "daily": DimensionPartitionMapping(
                    dimension_name="daily", partition_mapping=IdentityPartitionMapping()
                ),
            }
        ),
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("a", "2023-01-01"),
                ("b", "2023-01-01"),
                ("c", "2023-01-01"),
            ]
        ],
        [
            MultiPartitionKey({"123": values[0], "daily": values[1]})
            for values in [
                ("1", "2023-01-01"),
            ]
        ],
    ),
]


downstream_only_tests = [
    (
        MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                "weekly": WeeklyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionsDefinition(
            {
                "123": StaticPartitionsDefinition(["1", "2", "3"]),
                "daily": DailyPartitionsDefinition("2023-01-01"),
            }
        ),
        MultiPartitionMapping(
            {
                "abc": DimensionPartitionMapping(
                    dimension_name="123",
                    partition_mapping=StaticPartitionMapping({"a": "1", "b": "2", "c": "3"}),
                ),
                "weekly": DimensionPartitionMapping(
                    dimension_name="daily",
                    partition_mapping=TimeWindowPartitionMapping(),
                ),
            }
        ),
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
            for values in [
                ("c", "2023-01-01"),
                ("a", "2023-01-08"),
            ]
        ],
        [
            MultiPartitionKey({"abc": values[0], "daily": values[1]})
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
    assert partitions_mapping.get_upstream_partitions_for_partitions(
        downstream_partitions_def.empty_subset().with_partition_keys(downstream_partition_keys),
        upstream_partitions_def,
    ).get_partition_keys() == set(upstream_partition_keys)


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
        downstream_partitions_def,
    ).get_partition_keys() == set(downstream_partition_keys)


def test_multipartitions_mapping_dynamic():
    mapping = MultiPartitionMapping(
        {"dynamic": DimensionPartitionMapping("dynamic", IdentityPartitionMapping())}
    )
    with instance_for_test() as instance:
        instance.add_dynamic_partitions("dynamic", ["a", "b", "c"])
        downstream_partitions_def = MultiPartitionsDefinition(
            {
                "dynamic": DynamicPartitionsDefinition(name="dynamic"),
                "123": StaticPartitionsDefinition(["1", "2", "3"]),
            }
        )
        upstream_partitions_def = MultiPartitionsDefinition(
            {
                "dynamic": DynamicPartitionsDefinition(name="dynamic"),
                "456": StaticPartitionsDefinition(["4", "5", "6"]),
            }
        )
        assert mapping.get_upstream_partitions_for_partitions(
            downstream_partitions_def.empty_subset().with_partition_keys(
                [MultiPartitionKey({"dynamic": "a", "123": "1"})]
            ),
            upstream_partitions_def,
            dynamic_partitions_store=instance,
        ).get_partition_keys() == set(
            [
                MultiPartitionKey({"dynamic": val[1], "abc": val[0]})
                for val in [("4", "a"), ("5", "a"), ("6", "a")]
            ]
        )


def test_error_multipartitions_mapping():
    weekly_abc = MultiPartitionsDefinition(
        {
            "abc": StaticPartitionsDefinition(["a", "b", "c"]),
            "weekly": WeeklyPartitionsDefinition("2023-01-01"),
        }
    )
    daily_123 = MultiPartitionsDefinition(
        {
            "123": StaticPartitionsDefinition(["1", "2", "3"]),
            "daily": DailyPartitionsDefinition("2023-01-01"),
        }
    )

    with pytest.raises(
        CheckError, match="upstream dimension name that is not in the upstream partitions def"
    ):
        MultiPartitionMapping(
            {
                "nonexistent dimension": DimensionPartitionMapping(
                    "other nonexistent dimension", SpecificPartitionsPartitionMapping(["c"])
                )
            }
        ).get_upstream_partitions_for_partitions(weekly_abc.empty_subset(), daily_123)

    with pytest.raises(ValueError):
        MultiPartitionMapping(
            {
                "123": DimensionPartitionMapping(
                    "abc",
                    StaticPartitionMapping({"1": "a", "2": "b", "3": "c"}),
                ),
                "daily": DimensionPartitionMapping("weekly", IdentityPartitionMapping()),  # Invalid
            }
        ).get_upstream_partitions_for_partitions(
            weekly_abc.empty_subset().with_partition_keys(
                MultiPartitionKey({"abc": "a", "weekly": "2023-01-01"})
            ),
            daily_123,
        )

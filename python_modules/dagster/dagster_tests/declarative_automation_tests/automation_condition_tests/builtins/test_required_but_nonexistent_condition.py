import datetime

import dagster as dg
from dagster import AssetKey, AssetSelection, AutomationCondition
from dagster_shared.serdes import deserialize_value, serialize_value

# data for the latest two hours never exists yet, a common shape for e.g. warehouse
# tables whose data lands with a delay
hourly_offset_partitions_def = dg.HourlyPartitionsDefinition(
    start_date="2013-01-05-00:00", end_offset=-2
)
hourly_partitions_def = dg.HourlyPartitionsDefinition(start_date="2013-01-05-00:00")
daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2013-01-05")


def _at(**kwargs) -> datetime.datetime:
    return datetime.datetime(2013, 1, 5) + datetime.timedelta(**kwargs)


def _materialize_existing_partitions(
    instance: dg.DagsterInstance,
    partitions_def: dg.PartitionsDefinition,
    asset_key: str,
    evaluation_time: datetime.datetime,
    already_materialized: set[str],
) -> None:
    """Reports a materialization for every partition which exists at the given time, so that the
    only possible reason to consider a parent incomplete is nonexistence, never staleness.
    """
    existing = set(partitions_def.get_partition_keys(current_time=evaluation_time))
    for partition_key in sorted(existing - already_materialized):
        instance.report_runless_asset_event(
            dg.AssetMaterialization(asset_key, partition=partition_key)
        )
    already_materialized |= existing


def test_hourly_downstream_of_offset_hourly() -> None:
    @dg.asset(partitions_def=hourly_offset_partitions_def)
    def A() -> None: ...

    @dg.asset(
        partitions_def=hourly_partitions_def,
        deps=[A],
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    defs = dg.Definitions(assets=[A, B])
    instance = dg.DagsterInstance.ephemeral()

    # at 12:01, A's partitions exist through 09:00, while B has partitions through 11:00
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=_at(days=2, hours=12, minutes=1)
    )
    assert result.get_requested_partitions(AssetKey("B")) == {
        "2013-01-07-10:00",
        "2013-01-07-11:00",
    }

    # two hours later, A's partitions through 11:00 exist, so B's 10:00 and 11:00 partitions are
    # released without any parent event -- purely because the parent keys came into existence
    result = dg.evaluate_automation_conditions(
        defs=defs,
        instance=instance,
        cursor=result.cursor,
        evaluation_time=_at(days=2, hours=14, minutes=1),
    )
    assert result.get_requested_partitions(AssetKey("B")) == {
        "2013-01-07-12:00",
        "2013-01-07-13:00",
    }


def test_unguarded_eager_requests_nonexistent_parent_partitions() -> None:
    """Demonstrates the behavior this condition exists to guard against: eager() requests a
    downstream partition whose mapped upstream partitions do not exist.
    """

    @dg.asset(partitions_def=hourly_offset_partitions_def)
    def A() -> None: ...

    @dg.asset(
        partitions_def=daily_partitions_def,
        deps=[A],
        automation_condition=AutomationCondition.eager(),
    )
    def B() -> None: ...

    defs = dg.Definitions(assets=[A, B])
    instance = dg.DagsterInstance.ephemeral()
    materialized: set[str] = set()

    evaluation_time = _at(hours=23, minutes=59)
    _materialize_existing_partitions(
        instance, hourly_offset_partitions_def, "A", evaluation_time, materialized
    )
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0

    # B's first daily partition comes into existence at midnight, and is immediately requested
    # even though A's partitions for 22:00 and 23:00 of that day do not exist
    evaluation_time = _at(days=1, minutes=1)
    _materialize_existing_partitions(
        instance, hourly_offset_partitions_def, "A", evaluation_time, materialized
    )
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    assert result.get_requested_partitions(AssetKey("B")) == {"2013-01-05"}


def test_guarded_eager_waits_for_parent_partitions_to_exist() -> None:
    @dg.asset(partitions_def=hourly_offset_partitions_def)
    def A() -> None: ...

    @dg.asset(
        partitions_def=daily_partitions_def,
        deps=[A],
        automation_condition=AutomationCondition.eager()
        & ~AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    defs = dg.Definitions(assets=[A, B])
    instance = dg.DagsterInstance.ephemeral()
    materialized: set[str] = set()

    evaluation_time = _at(hours=23, minutes=59)
    _materialize_existing_partitions(
        instance, hourly_offset_partitions_def, "A", evaluation_time, materialized
    )
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0

    # B's first daily partition comes into existence, but A's partitions for 22:00 and 23:00
    # of that day do not exist yet, so nothing is requested
    evaluation_time = _at(days=1, minutes=1)
    _materialize_existing_partitions(
        instance, hourly_offset_partitions_def, "A", evaluation_time, materialized
    )
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0

    # by 02:01, all of A's partitions for the day exist; once they are materialized, B's daily
    # partition is requested exactly once
    evaluation_time = _at(days=1, hours=2, minutes=1)
    _materialize_existing_partitions(
        instance, hourly_offset_partitions_def, "A", evaluation_time, materialized
    )
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    assert result.get_requested_partitions(AssetKey("B")) == {"2013-01-05"}

    # the request is not repeated on the next evaluation
    result = dg.evaluate_automation_conditions(
        defs=defs,
        instance=instance,
        cursor=result.cursor,
        evaluation_time=_at(days=1, hours=2, minutes=31),
    )
    assert result.total_requested == 0


def test_respects_allow_nonexistent_upstream_partitions() -> None:
    @dg.asset(partitions_def=hourly_offset_partitions_def)
    def A() -> None: ...

    @dg.asset(
        partitions_def=daily_partitions_def,
        deps=[
            dg.AssetDep(
                "A",
                partition_mapping=dg.TimeWindowPartitionMapping(
                    allow_nonexistent_upstream_partitions=True
                ),
            )
        ],
        automation_condition=AutomationCondition.eager()
        & ~AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    defs = dg.Definitions(assets=[A, B])
    instance = dg.DagsterInstance.ephemeral()
    materialized: set[str] = set()

    evaluation_time = _at(hours=23, minutes=59)
    _materialize_existing_partitions(
        instance, hourly_offset_partitions_def, "A", evaluation_time, materialized
    )
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=evaluation_time
    )
    assert result.total_requested == 0

    # B's daily partition maps onto A partitions which do not exist, but the mapping explicitly
    # allows this, so the guard is a no-op and eager() fires as if unguarded
    evaluation_time = _at(days=1, minutes=1)
    _materialize_existing_partitions(
        instance, hourly_offset_partitions_def, "A", evaluation_time, materialized
    )
    result = dg.evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=evaluation_time
    )
    assert result.get_requested_partitions(AssetKey("B")) == {"2013-01-05"}


def test_allow_ignore_scoping() -> None:
    def build_defs(condition: AutomationCondition) -> dg.Definitions:
        @dg.asset(partitions_def=hourly_offset_partitions_def)
        def A() -> None: ...

        @dg.asset(partitions_def=hourly_partitions_def)
        def B() -> None: ...

        @dg.asset(partitions_def=hourly_partitions_def, deps=[A, B], automation_condition=condition)
        def C() -> None: ...

        return dg.Definitions(assets=[A, B, C])

    evaluation_time = _at(days=2, hours=12, minutes=1)

    # C's latest partitions require nonexistent partitions of A, but B is fully existent
    result = dg.evaluate_automation_conditions(
        defs=build_defs(AutomationCondition.any_deps_required_but_nonexistent()),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=evaluation_time,
    )
    assert result.get_requested_partitions(AssetKey("C")) == {
        "2013-01-07-10:00",
        "2013-01-07-11:00",
    }

    result = dg.evaluate_automation_conditions(
        defs=build_defs(
            AutomationCondition.any_deps_required_but_nonexistent().ignore(
                AssetSelection.assets("A")
            )
        ),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=evaluation_time,
    )
    assert result.total_requested == 0

    result = dg.evaluate_automation_conditions(
        defs=build_defs(
            AutomationCondition.any_deps_required_but_nonexistent().allow(
                AssetSelection.assets("B")
            )
        ),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=evaluation_time,
    )
    assert result.total_requested == 0


def test_unpartitioned_child_of_partitioned_parent() -> None:
    @dg.asset(partitions_def=hourly_offset_partitions_def)
    def A() -> None: ...

    @dg.asset(
        deps=[A], automation_condition=AutomationCondition.any_deps_required_but_nonexistent()
    )
    def B() -> None: ...

    # an unpartitioned child maps onto the existing partitions of its parent
    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A, B]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=_at(days=2, hours=12, minutes=1),
    )
    assert result.total_requested == 0


def test_unpartitioned_parent_of_partitioned_child() -> None:
    @dg.asset
    def A() -> None: ...

    @dg.asset(
        partitions_def=hourly_partitions_def,
        deps=[A],
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A, B]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=_at(days=2, hours=12, minutes=1),
    )
    assert result.total_requested == 0


def test_no_deps() -> None:
    @dg.asset(automation_condition=AutomationCondition.any_deps_required_but_nonexistent())
    def A() -> None: ...

    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A]), instance=dg.DagsterInstance.ephemeral()
    )
    assert result.total_requested == 0


def test_self_dependency_at_series_start() -> None:
    # the first partition of a self-dependent asset maps onto a window before the start of the
    # partitions def, which the mapping clamps to an empty subset rather than treating as
    # nonexistent
    @dg.asset(
        partitions_def=hourly_partitions_def,
        deps=[
            dg.AssetDep(
                "A",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            )
        ],
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def A() -> None: ...

    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=_at(hours=4, minutes=1),
    )
    assert result.total_requested == 0


def test_dynamic_partitions_identity_mapping() -> None:
    @dg.asset(partitions_def=dg.DynamicPartitionsDefinition(name="dp_A"))
    def A() -> None: ...

    @dg.asset(
        partitions_def=dg.DynamicPartitionsDefinition(name="dp_B"),
        deps=[dg.AssetDep("A", partition_mapping=dg.IdentityPartitionMapping())],
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("dp_A", ["p1"])
    instance.add_dynamic_partitions("dp_B", ["p1", "p2"])

    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A, B]), instance=instance
    )
    # B's p2 partition has no identity-mapped counterpart in A
    assert result.get_requested_partitions(AssetKey("B")) == {"p2"}


def test_multi_partitioned_child_multi_to_single_dimension_mapping() -> None:
    daily_offset = dg.DailyPartitionsDefinition(start_date="2013-01-05", end_offset=-1)

    @dg.asset(partitions_def=daily_offset)
    def A() -> None: ...

    @dg.asset(
        partitions_def=dg.MultiPartitionsDefinition(
            {"date": daily_partitions_def, "static": dg.StaticPartitionsDefinition(["a", "b"])}
        ),
        deps=[
            dg.AssetDep(
                "A",
                partition_mapping=dg.MultiToSingleDimensionPartitionMapping(
                    partition_dimension_name="date"
                ),
            )
        ],
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    # at 01-08, B has date partitions through 01-07 while A (end_offset=-1) only exists
    # through 01-06
    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A, B]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=_at(days=3, minutes=1),
    )
    assert result.get_requested_partitions(AssetKey("B")) == {
        "2013-01-07|a",
        "2013-01-07|b",
    }


def test_multi_partitioned_child_time_window_dimension_mapping() -> None:
    static_partitions_def = dg.StaticPartitionsDefinition(["a", "b"])

    @dg.asset(
        partitions_def=dg.MultiPartitionsDefinition(
            {"time": hourly_offset_partitions_def, "static": static_partitions_def}
        )
    )
    def A() -> None: ...

    @dg.asset(
        partitions_def=dg.MultiPartitionsDefinition(
            {"time": hourly_partitions_def, "static": static_partitions_def}
        ),
        deps=[
            dg.AssetDep(
                "A",
                partition_mapping=dg.MultiPartitionMapping(
                    {
                        "time": dg.DimensionPartitionMapping(
                            dimension_name="time",
                            partition_mapping=dg.TimeWindowPartitionMapping(),
                        ),
                        "static": dg.DimensionPartitionMapping(
                            dimension_name="static",
                            partition_mapping=dg.IdentityPartitionMapping(),
                        ),
                    }
                ),
            )
        ],
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    # at 05:30, B has time partitions through 04:00 while A (end_offset=-2) only exists
    # through 02:00
    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A, B]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=_at(hours=5, minutes=30),
    )
    assert result.get_requested_partitions(AssetKey("B")) == {
        "a|2013-01-05-03:00",
        "b|2013-01-05-03:00",
        "a|2013-01-05-04:00",
        "b|2013-01-05-04:00",
    }


def test_resolve_through_virtual_is_a_no_op() -> None:
    daily_offset = dg.DailyPartitionsDefinition(start_date="2013-01-05", end_offset=-1)

    @dg.asset(partitions_def=daily_offset)
    def grandparent() -> None: ...

    virtual = dg.AssetSpec("virtual", deps=["grandparent"], is_virtual=True)

    @dg.asset(
        deps=["virtual"],
        partitions_def=daily_partitions_def,
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent().resolve_through_virtual(),
    )
    def child() -> None: ...

    # partition mappings are only defined along direct dependency edges, so virtual resolution
    # is a no-op for this condition rather than an error
    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[grandparent, virtual, child]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=_at(days=3, minutes=1),
    )
    assert result.total_requested == 0


def test_cross_cadence_offset_mapping_uses_exhaustive_scan() -> None:
    # a daily child of a weekly parent with a nonzero mapping offset: cross-cadence
    # realignment can collapse individual mapped windows to zero width, so the responsible
    # child keys form a periodic pattern rather than a suffix of the chronologically-ordered
    # candidates. the bisection fast path must not be used here (see the gate in
    # AssetGraphView._localize_required_but_nonexistent_child_keys)
    @dg.asset(partitions_def=dg.WeeklyPartitionsDefinition(start_date="2013-06-08", end_offset=-2))
    def A() -> None: ...

    @dg.asset(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2013-06-15"),
        deps=[
            dg.AssetDep(
                "A",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=0, end_offset=-1),
            )
        ],
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A, B]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=datetime.datetime(2013, 7, 5, 23, 1),
    )
    # 2013-06-16, 2013-06-23, and 2013-06-30 map to zero-width (empty) parent windows,
    # requiring nothing, and must not be flagged; 2013-06-15 maps onto the existing parent week
    assert result.get_requested_partitions(AssetKey("B")) == {
        "2013-06-17",
        "2013-06-18",
        "2013-06-19",
        "2013-06-20",
        "2013-06-21",
        "2013-06-22",
        "2013-06-24",
        "2013-06-25",
        "2013-06-26",
        "2013-06-27",
        "2013-06-28",
        "2013-06-29",
        "2013-07-01",
        "2013-07-02",
        "2013-07-03",
        "2013-07-04",
    }


def test_resolve_through_virtual_with_partitioned_virtual_parent() -> None:
    def build_defs(condition: AutomationCondition) -> dg.Definitions:
        virtual = dg.AssetSpec(
            "virtual", is_virtual=True, partitions_def=hourly_offset_partitions_def
        )

        @dg.asset(
            partitions_def=hourly_partitions_def,
            deps=["virtual"],
            automation_condition=condition,
        )
        def child() -> None: ...

        return dg.Definitions(assets=[virtual, child])

    evaluation_time = _at(days=2, hours=12, minutes=1)
    expected = {"2013-01-07-10:00", "2013-01-07-11:00"}

    result = dg.evaluate_automation_conditions(
        defs=build_defs(AutomationCondition.any_deps_required_but_nonexistent()),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=evaluation_time,
    )
    assert result.get_requested_partitions(AssetKey("child")) == expected

    # a partitioned virtual parent is still a direct parent: resolving through virtual
    # deps is a no-op for this condition and must not drop the edge
    result = dg.evaluate_automation_conditions(
        defs=build_defs(
            AutomationCondition.any_deps_required_but_nonexistent().resolve_through_virtual()
        ),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=evaluation_time,
    )
    assert result.get_requested_partitions(AssetKey("child")) == expected


def test_partitioned_asset_check_with_partitioned_dep() -> None:
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2013-01-07"))
    def parent() -> None: ...

    @dg.asset(
        partitions_def=daily_partitions_def,
        check_specs=[
            dg.AssetCheckSpec(
                "my_check",
                asset="child",
                additional_deps=["parent"],
                partitions_def=daily_partitions_def,
                automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
            )
        ],
    )
    def child(): ...

    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[parent, child]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=_at(days=4, minutes=1),
    )
    check_key = dg.AssetCheckKey(AssetKey("child"), "my_check")
    check_result = next(r for r in result.results if r.key == check_key)
    # the check's 01-05 and 01-06 partitions require parent partitions which do not exist
    assert set(check_result.true_subset.expensively_compute_partition_keys()) == {
        "2013-01-05",
        "2013-01-06",
    }


def test_positive_mapping_offset_not_detected() -> None:
    # a mapping with a positive end_offset requires future parent partitions, but
    # TimeWindowPartitionMapping clamps those windows to the parent's existing range before
    # the required_but_nonexistent report is computed, so no consumer of the report can see
    # them (https://github.com/dagster-io/dagster/issues/26935). this test documents that
    # inherited limitation
    @dg.asset(partitions_def=hourly_partitions_def)
    def A() -> None: ...

    @dg.asset(
        partitions_def=hourly_partitions_def,
        deps=[
            dg.AssetDep(
                "A",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=0, end_offset=2),
            )
        ],
        automation_condition=AutomationCondition.any_deps_required_but_nonexistent(),
    )
    def B() -> None: ...

    result = dg.evaluate_automation_conditions(
        defs=dg.Definitions(assets=[A, B]),
        instance=dg.DagsterInstance.ephemeral(),
        evaluation_time=_at(days=2, hours=12, minutes=1),
    )
    assert result.total_requested == 0


def test_serialization() -> None:
    condition = (
        AutomationCondition.eager() & ~AutomationCondition.any_deps_required_but_nonexistent()
    )
    assert condition.is_serializable
    assert deserialize_value(serialize_value(condition)) == condition

    scoped = AutomationCondition.any_deps_required_but_nonexistent().ignore(
        AssetSelection.assets("A")
    )
    assert deserialize_value(serialize_value(scoped)) == scoped


def test_name_and_description() -> None:
    condition = AutomationCondition.any_deps_required_but_nonexistent()
    assert condition.get_label() == "any_deps_required_but_nonexistent"
    assert condition.name == "ANY_DEPS_REQUIRED_BUT_NONEXISTENT"
    # string parity with AutoMaterializeRule.skip_on_required_but_nonexistent_parents()
    assert condition.description == "required parent partitions do not exist"

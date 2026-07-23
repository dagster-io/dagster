import dagster as dg
from dagster import AutomationCondition
from dagster._core.definitions.automation_tick_evaluation_context import build_run_requests


def test_asset_job_discovered_and_produces_run_request() -> None:
    @dg.asset
    def upstream():
        return 1

    @dg.asset(deps=[upstream])
    def downstream_a():
        return 2

    @dg.asset(deps=[upstream])
    def downstream_b():
        return 3

    job = dg.define_asset_job(
        "my_job",
        selection=[downstream_a, downstream_b],
        automation_condition=AutomationCondition.all_job_root_assets_match(
            AutomationCondition.eager()
        ),
    )

    defs = dg.Definitions(assets=[upstream, downstream_a, downstream_b], jobs=[job])

    with dg.instance_for_test() as instance:
        # tick 1: nothing materialized — no request
        result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
        assert result.total_requested == 0

        # tick 2: materialize upstream — both downstream assets become eager-requestable
        instance.report_runless_asset_event(dg.AssetMaterialization("upstream"))
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=instance, cursor=result.cursor
        )
        assert result.total_requested == 1

        # verify run request shape
        run_requests = build_run_requests(
            entity_subsets=list(result._requested_subsets),  # noqa: SLF001
            asset_graph=defs.resolve_asset_graph(),
            run_tags=None,
            emit_backfills=False,
        )
        assert len(run_requests) == 1
        rr = run_requests[0]
        assert rr.job_name == "my_job"


def test_all_job_root_assets_match_requires_all() -> None:
    """With all_job_root_assets_match, the job should not be requested until ALL constituent
    assets' conditions pass simultaneously.
    """

    @dg.asset
    def src_a():
        return 1

    @dg.asset
    def src_b():
        return 2

    @dg.asset(deps=[src_a])
    def tgt_a():
        return 3

    @dg.asset(deps=[src_b])
    def tgt_b():
        return 4

    job = dg.define_asset_job(
        "all_match_job",
        selection=[tgt_a, tgt_b],
        automation_condition=AutomationCondition.all_job_root_assets_match(
            AutomationCondition.eager()
        ),
    )

    defs = dg.Definitions(assets=[src_a, src_b, tgt_a, tgt_b], jobs=[job])

    with dg.instance_for_test() as instance:
        # tick 1: empty tick to consume initial evaluation reset
        result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
        assert result.total_requested == 0

        # materialize only src_a — only tgt_a's condition passes, not all
        instance.report_runless_asset_event(dg.AssetMaterialization("src_a"))
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=instance, cursor=result.cursor
        )
        assert result.total_requested == 0

        # materialize src_b — now both targets' conditions should pass
        instance.report_runless_asset_event(dg.AssetMaterialization("src_b"))
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=instance, cursor=result.cursor
        )
        assert result.total_requested == 1

        run_requests = build_run_requests(
            entity_subsets=list(result._requested_subsets),  # noqa: SLF001
            asset_graph=defs.resolve_asset_graph(),
            run_tags=None,
            emit_backfills=False,
        )
        assert len(run_requests) == 1
        assert run_requests[0].job_name == "all_match_job"


def test_any_job_root_assets_match_triggers_on_any() -> None:
    """With any_job_root_assets_match, the job should be requested when ANY constituent
    asset's condition passes.
    """

    @dg.asset
    def src_x():
        return 1

    @dg.asset
    def src_y():
        return 2

    @dg.asset(deps=[src_x])
    def tgt_x():
        return 3

    @dg.asset(deps=[src_y])
    def tgt_y():
        return 4

    job = dg.define_asset_job(
        "any_match_job",
        selection=[tgt_x, tgt_y],
        automation_condition=AutomationCondition.any_job_root_assets_match(
            AutomationCondition.eager()
        ),
    )

    defs = dg.Definitions(assets=[src_x, src_y, tgt_x, tgt_y], jobs=[job])

    with dg.instance_for_test() as instance:
        # tick 1: empty tick to consume initial evaluation reset
        result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
        assert result.total_requested == 0

        # tick 2: materialize only src_x — tgt_x's condition passes, triggers job
        instance.report_runless_asset_event(dg.AssetMaterialization("src_x"))
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=instance, cursor=result.cursor
        )
        assert result.total_requested == 1

        run_requests = build_run_requests(
            entity_subsets=list(result._requested_subsets),  # noqa: SLF001
            asset_graph=defs.resolve_asset_graph(),
            run_tags=None,
            emit_backfills=False,
        )
        assert len(run_requests) == 1
        assert run_requests[0].job_name == "any_match_job"


def test_mixed_asset_and_job_conditions_y_shaped() -> None:
    """Y-shaped topology where asset-level and job-level conditions coexist.

    Topology:
        src_x -> x ─┐
                     ├─> b ─> c   (b, c in "my_job")
        src_y -> y ─┘

    - x has eager() directly (asset-level condition)
    - y has eager() directly (asset-level condition)
    - my_job (containing b, c) has all_job_root_assets_match(eager())

    The test verifies:
    1. Nothing happens initially
    2. Materializing src_x triggers x but not y and not the job
    3. Materializing src_y triggers y but not the job (x already handled)
    4. With both x and y materialized, the job fires (b and c both have updated deps)
    """

    @dg.asset
    def src_x():
        return 1

    @dg.asset
    def src_y():
        return 2

    @dg.asset(deps=[src_x], automation_condition=AutomationCondition.eager())
    def x():
        return 3

    @dg.asset(deps=[src_y], automation_condition=AutomationCondition.eager())
    def y():
        return 4

    @dg.asset(deps=[x, y])
    def b():
        return 5

    @dg.asset(deps=[b])
    def c():
        return 6

    job = dg.define_asset_job(
        "my_job",
        selection=[b, c],
        automation_condition=AutomationCondition.all_job_root_assets_match(
            AutomationCondition.eager()
        ),
    )

    defs = dg.Definitions(assets=[src_x, src_y, x, y, b, c], jobs=[job])

    with dg.instance_for_test() as instance:
        # tick 1: nothing materialized — no requests
        result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
        assert result.total_requested == 0

        # tick 2: materialize src_x — only x should be requested
        instance.report_runless_asset_event(dg.AssetMaterialization("src_x"))
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=instance, cursor=result.cursor
        )
        assert result.total_requested == 1
        assert result.get_num_requested(dg.AssetKey("x")) == 1

        # simulate x materializing
        instance.report_runless_asset_event(dg.AssetMaterialization("x"))

        # tick 3: materialize src_y — y should be requested, job should NOT fire yet
        # because b depends on both x and y, but y hasn't materialized yet
        instance.report_runless_asset_event(dg.AssetMaterialization("src_y"))
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=instance, cursor=result.cursor
        )
        assert result.total_requested == 1
        assert result.get_num_requested(dg.AssetKey("y")) == 1

        # simulate y materializing
        instance.report_runless_asset_event(dg.AssetMaterialization("y"))

        # tick 4: both x and y are now materialized — job should fire
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=instance, cursor=result.cursor
        )
        assert result.total_requested == 1

        requested_results = [r for r in result.results if r.true_subset.size > 0]
        assert len(requested_results) == 1
        assert requested_results[0].true_subset.key == dg.AssetJobKey("my_job")


def test_partitioned_job_produces_run_request_per_partition() -> None:
    """A conditioned partitioned job evaluates per-partition, and each requested
    partition becomes its own whole-job run request carrying the partition's tags.
    """
    from dagster._core.storage.tags import PARTITION_NAME_TAG

    partitions_def = dg.StaticPartitionsDefinition(["p1", "p2"])

    @dg.asset(partitions_def=partitions_def)
    def part_asset() -> None: ...

    job = dg.define_asset_job(
        "my_job",
        selection=[part_asset],
        automation_condition=AutomationCondition.all_job_root_assets_match(
            AutomationCondition.missing()
        ),
    )

    defs = dg.Definitions(assets=[part_asset], jobs=[job])
    instance = dg.DagsterInstance.ephemeral()

    # tick 1: both partitions are missing, so both are requested
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 2

    run_requests = build_run_requests(
        entity_subsets=list(result._requested_subsets),  # noqa: SLF001
        asset_graph=defs.resolve_asset_graph(),
        run_tags=None,
        emit_backfills=False,
    )
    assert [(rr.job_name, rr.partition_key) for rr in run_requests] == [
        ("my_job", "p1"),
        ("my_job", "p2"),
    ]
    assert all(rr.tags[PARTITION_NAME_TAG] == rr.partition_key for rr in run_requests)
    assert all(rr.asset_selection is None for rr in run_requests)

    # tick 2: materialize p1 -- only p2 remains missing and requested
    instance.report_runless_asset_event(dg.AssetMaterialization("part_asset", partition="p1"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    run_requests = build_run_requests(
        entity_subsets=list(result._requested_subsets),  # noqa: SLF001
        asset_graph=defs.resolve_asset_graph(),
        run_tags=None,
        emit_backfills=False,
    )
    assert [(rr.job_name, rr.partition_key) for rr in run_requests] == [("my_job", "p2")]


def test_all_job_root_assets_match_with_mixed_partition_roots() -> None:
    """An unpartitioned root's condition result applies to every partition of a
    partitioned job: for all_, once the unpartitioned root materializes, "all roots
    missing" is false for every partition -- even if the partitioned root is still
    missing everywhere.
    """
    partitions_def = dg.StaticPartitionsDefinition(["p1", "p2"])

    @dg.asset(partitions_def=partitions_def)
    def part_root() -> None: ...

    @dg.asset
    def unpart_root() -> None: ...

    job = dg.define_asset_job(
        "mixed_job",
        selection=[part_root, unpart_root],
        automation_condition=AutomationCondition.all_job_root_assets_match(
            AutomationCondition.missing()
        ),
    )
    defs = dg.Definitions(assets=[part_root, unpart_root], jobs=[job])
    instance = dg.DagsterInstance.ephemeral()

    # both roots missing: every partition is requested
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 2

    # the unpartitioned root materializes: no partition is requested anymore
    instance.report_runless_asset_event(dg.AssetMaterialization("unpart_root"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_any_job_root_assets_match_with_mixed_partition_roots() -> None:
    """For any_, a still-missing partitioned root keeps its own partitions true after
    the unpartitioned root materializes, and each partition drops out individually as
    it materializes.
    """
    partitions_def = dg.StaticPartitionsDefinition(["p1", "p2"])

    @dg.asset(partitions_def=partitions_def)
    def part_root() -> None: ...

    @dg.asset
    def unpart_root() -> None: ...

    job = dg.define_asset_job(
        "mixed_job",
        selection=[part_root, unpart_root],
        automation_condition=AutomationCondition.any_job_root_assets_match(
            AutomationCondition.missing()
        ),
    )
    defs = dg.Definitions(assets=[part_root, unpart_root], jobs=[job])
    instance = dg.DagsterInstance.ephemeral()

    # both roots missing: every partition is requested
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 2

    # the unpartitioned root materializes, but the partitioned root is still missing
    # everywhere: every partition stays requested
    instance.report_runless_asset_event(dg.AssetMaterialization("unpart_root"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 2

    # p1 of the partitioned root materializes: only p2 remains requested
    instance.report_runless_asset_event(dg.AssetMaterialization("part_root", partition="p1"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1
    run_requests = build_run_requests(
        entity_subsets=list(result._requested_subsets),  # noqa: SLF001
        asset_graph=defs.resolve_asset_graph(),
        run_tags=None,
        emit_backfills=False,
    )
    assert [(rr.job_name, rr.partition_key) for rr in run_requests] == [("mixed_job", "p2")]

    # p2 materializes: nothing left
    instance.report_runless_asset_event(dg.AssetMaterialization("part_root", partition="p2"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

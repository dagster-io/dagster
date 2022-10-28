from dagster._utils.calculate_data_time import get_upstream_materialization_times_for_record


@pytest.mark.parametrize(
    ["asset_keys", "materialization_effects"],
    [
        (
            "e",
            [
                ("e", {"e": False}),
                ("abd", {"e": False}),
                ("ac", {"e": False}),
                ("e", {"e": True}),
            ],
        ),
        (
            "e",
            [
                ("abce", {"e": True}),
            ],
        ),
        (
            "e",
            [
                ("ae", {"e": False}),
                ("b", {"e": False}),
                ("c", {"e": False}),
                ("e", {"e": True}),
            ],
        ),
        (
            "e",
            [
                ("a", {"e": False}),
                ("c", {"e": False}),
                ("e", {"e": True}),
            ],
        ),
        (
            "e",
            [
                ("ce", {"e": False}),
                ("ac", {"e": False}),
                ("e", {"e": True}),
            ],
        ),
        (
            "f",
            [
                ("acd", {"f": False}),
                ("bf", {"f": False}),
                ("bdf", {"f": True}),
            ],
        ),
        (
            "f",
            [
                ("bdf", {"f": False}),
                ("a", {"f": False}),
                ("bdf", {"f": False}),
                ("c", {"f": False}),
                ("bdf", {"f": True}),
            ],
        ),
        (
            "ef",
            [
                ("a", {"f": False, "e": False}),
                ("bc", {"f": False, "e": False}),
                ("de", {"f": False, "e": True}),
                ("f", {"f": True, "e": True}),
            ],
        ),
        (
            "ef",
            [
                ("cdef", {"f": False, "e": False}),
                ("ab", {"f": False, "e": False}),
                ("cdef", {"f": True, "e": True}),
            ],
        ),
        (
            "ef",
            [
                ("acdef", {"f": False, "e": True}),
                ("ab", {"f": False, "e": True}),
                ("bd", {"f": False, "e": True}),
                ("f", {"f": True, "e": True}),
            ],
        ),
    ],
)
def test_calculate_data_time(asset_keys, materialization_effects):
    """
    A = B = D = F
     \\  //
       C = E
    B,C,D share an op
    """

    @asset
    def a():
        return 1

    @multi_asset(
        non_argument_deps={AssetKey("a")},
        outs={
            "b": AssetOut(is_required=False),
            "c": AssetOut(is_required=False),
            "d": AssetOut(is_required=False),
        },
        can_subset=True,
        internal_asset_deps={
            "b": {AssetKey("a")},
            "c": {AssetKey("a")},
            "d": {AssetKey("b"), AssetKey("c")},
        },
    )
    def bcd(context):
        for output_name in sorted(context.selected_output_names):
            yield Output(output_name, output_name)

    @asset(non_argument_deps={AssetKey("c")})
    def e():
        return 1

    @asset(non_argument_deps={AssetKey("d")})
    def f():
        return 1

    asset_keys = [AssetKey(c) for c in asset_keys]
    all_assets = [a, bcd, e, f]

    @repository
    def my_repo():
        return [all_assets]

    with instance_for_test() as instance:

        for to_materialize, expected_results in materialization_effects:
            # materialize selected assets
            build_asset_selection_job(
                "materialize_job",
                assets=all_assets,
                source_assets=[],
                asset_selection=AssetSelection.keys(*(AssetKey(c) for c in to_materialize)).resolve(
                    all_assets
                ),
            ).execute_in_process(instance=instance)

        # 1.5 hours later, everything should be stale
        with pendulum.test(pendulum.now().add(hours=1.5)):
            ctx = build_freshness_policy_sensor_context(
                asset_keys=asset_keys,
                repository_def=my_repo,
                cursor=ctx.cursor,
                instance=instance,
            )
            ret = list(my_sla_sensor(ctx))
            assert len(ret) == len(asset_keys)
            for ak in asset_keys:
                assert (
                    RunRequest(run_key=None, tags={"status": "False"}, asset_selection=[ak]) in ret
                )

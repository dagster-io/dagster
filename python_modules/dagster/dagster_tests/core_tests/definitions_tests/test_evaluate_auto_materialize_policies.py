from dagster import (
    AutoMaterializeEvaluationResult,
    AutoMaterializePolicy,
    DagsterInstance,
    RunRequest,
    asset,
    evaluate_auto_materialize_policies,
    materialize,
)


def test_basic():
    @asset(auto_materialize_policy=AutoMaterializePolicy.eager())
    def asset1() -> None:
        ...

    result = evaluate_auto_materialize_policies(assets=[asset1])
    assert result == AutoMaterializeEvaluationResult(
        run_requests=[RunRequest(asset_selection=[asset1.key])]
    )


def test_multiple_assets():
    @asset(auto_materialize_policy=AutoMaterializePolicy.eager())
    def asset1() -> None:
        ...

    @asset(auto_materialize_policy=AutoMaterializePolicy.eager())
    def asset2() -> None:
        ...

    result = evaluate_auto_materialize_policies(assets=[asset1, asset2])
    assert result.requested_asset_keys == {asset1.key, asset2.key}


def test_with_instance():
    @asset(auto_materialize_policy=AutoMaterializePolicy.eager())
    def asset1() -> None:
        ...

    instance = DagsterInstance.ephemeral()
    materialize(assets=[asset1], instance=instance)

    result = evaluate_auto_materialize_policies(assets=[asset1], instance=instance)
    assert result == AutoMaterializeEvaluationResult(run_requests=[])

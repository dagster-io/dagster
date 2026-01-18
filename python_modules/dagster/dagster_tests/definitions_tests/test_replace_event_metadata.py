import dagster as dg
from dagster import AssetCheckSeverity


def test_output_object_with_metadata() -> None:
    def _get_output() -> dg.Output:
        return dg.Output(5, output_name="foo", metadata={"foo": "bar"}, tags={"baz": "qux"})

    assert _get_output() == _get_output()

    assert _get_output().with_metadata({"new": "metadata"}) == dg.Output(
        5, output_name="foo", metadata={"new": "metadata"}, tags={"baz": "qux"}
    )

    out = _get_output()
    assert out.with_metadata({**out.metadata, "new": "metadata"}) == dg.Output(
        5, output_name="foo", metadata={"foo": "bar", "new": "metadata"}, tags={"baz": "qux"}
    )


def test_asset_materialization_object_with_metadata() -> None:
    def _get_materialization() -> dg.AssetMaterialization:
        return dg.AssetMaterialization(
            asset_key=dg.AssetKey("my_key"),
            description="foo",
            metadata={"foo": "bar"},
            tags={"baz": "qux"},
            partition="my_partition",
        )

    assert _get_materialization() == _get_materialization()

    assert _get_materialization().with_metadata({"new": "metadata"}) == dg.AssetMaterialization(
        asset_key=dg.AssetKey("my_key"),
        description="foo",
        metadata={"new": "metadata"},
        tags={"baz": "qux"},
        partition="my_partition",
    )

    mat = _get_materialization()

    assert mat.with_metadata({**mat.metadata, "new": "metadata"}) == dg.AssetMaterialization(
        asset_key=dg.AssetKey("my_key"),
        description="foo",
        metadata={"foo": "bar", "new": "metadata"},
        tags={"baz": "qux"},
        partition="my_partition",
    )


def test_asset_observation_object_with_metadata() -> None:
    def _get_observation() -> dg.AssetObservation:
        return dg.AssetObservation(
            asset_key=dg.AssetKey("my_key"),
            description="foo",
            metadata={"foo": "bar"},
            tags={"baz": "qux"},
            partition="my_partition",
        )

    assert _get_observation() == _get_observation()

    assert _get_observation().with_metadata({"new": "metadata"}) == dg.AssetObservation(
        asset_key=dg.AssetKey("my_key"),
        description="foo",
        metadata={"new": "metadata"},
        tags={"baz": "qux"},
        partition="my_partition",
    )

    obs = _get_observation()

    assert obs.with_metadata({**obs.metadata, "new": "metadata"}) == dg.AssetObservation(
        asset_key=dg.AssetKey("my_key"),
        description="foo",
        metadata={"foo": "bar", "new": "metadata"},
        tags={"baz": "qux"},
        partition="my_partition",
    )


def test_asset_check_result_object_with_metadata() -> None:
    def _get_check_result() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(
            asset_key=dg.AssetKey("my_key"),
            metadata={"foo": "bar"},
            passed=True,
            severity=AssetCheckSeverity.WARN,
            description="foo",
            check_name="my_check",
        )

    assert _get_check_result() == _get_check_result()

    assert _get_check_result().with_metadata({"new": "metadata"}) == dg.AssetCheckResult(
        asset_key=dg.AssetKey("my_key"),
        metadata={"new": "metadata"},
        passed=True,
        severity=AssetCheckSeverity.WARN,
        description="foo",
        check_name="my_check",
    )

    check = _get_check_result()
    assert check.with_metadata({**check.metadata, "new": "metadata"}) == dg.AssetCheckResult(
        asset_key=dg.AssetKey("my_key"),
        metadata={"foo": "bar", "new": "metadata"},
        passed=True,
        severity=AssetCheckSeverity.WARN,
        description="foo",
        check_name="my_check",
    )


def test_asset_check_evaluation_object_with_metadata() -> None:
    def _get_check_evaluation() -> dg.AssetCheckEvaluation:
        return dg.AssetCheckEvaluation(
            asset_key=dg.AssetKey("my_key"),
            metadata={"foo": "bar"},
            passed=True,
            severity=AssetCheckSeverity.WARN,
            description="foo",
            check_name="my_check",
        )

    assert _get_check_evaluation() == _get_check_evaluation()

    assert _get_check_evaluation().with_metadata({"new": "metadata"}) == dg.AssetCheckEvaluation(
        asset_key=dg.AssetKey("my_key"),
        metadata={"new": "metadata"},
        passed=True,
        severity=AssetCheckSeverity.WARN,
        description="foo",
        check_name="my_check",
    )

    check = _get_check_evaluation()
    assert check.with_metadata({**check.metadata, "new": "metadata"}) == dg.AssetCheckEvaluation(
        asset_key=dg.AssetKey("my_key"),
        metadata={"foo": "bar", "new": "metadata"},
        passed=True,
        severity=AssetCheckSeverity.WARN,
        description="foo",
        check_name="my_check",
    )

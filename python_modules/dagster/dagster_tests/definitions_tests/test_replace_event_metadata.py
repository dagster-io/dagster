from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    Output,
)


def test_output_object_with_metadata() -> None:
    def _get_output() -> Output:
        return Output(5, output_name="foo", metadata={"foo": "bar"}, tags={"baz": "qux"})

    assert _get_output() == _get_output()

    assert _get_output().with_metadata({"new": "metadata"}) == Output(
        5, output_name="foo", metadata={"new": "metadata"}, tags={"baz": "qux"}
    )

    out = _get_output()
    assert out.with_metadata({**out.metadata, "new": "metadata"}) == Output(
        5, output_name="foo", metadata={"foo": "bar", "new": "metadata"}, tags={"baz": "qux"}
    )


def test_asset_materialization_object_with_metadata() -> None:
    def _get_materialization() -> AssetMaterialization:
        return AssetMaterialization(
            asset_key=AssetKey("my_key"),
            description="foo",
            metadata={"foo": "bar"},
            tags={"baz": "qux"},
            partition="my_partition",
        )

    assert _get_materialization() == _get_materialization()

    assert _get_materialization().with_metadata({"new": "metadata"}) == AssetMaterialization(
        asset_key=AssetKey("my_key"),
        description="foo",
        metadata={"new": "metadata"},
        tags={"baz": "qux"},
        partition="my_partition",
    )

    mat = _get_materialization()

    assert mat.with_metadata({**mat.metadata, "new": "metadata"}) == AssetMaterialization(
        asset_key=AssetKey("my_key"),
        description="foo",
        metadata={"foo": "bar", "new": "metadata"},
        tags={"baz": "qux"},
        partition="my_partition",
    )


def test_asset_observation_object_with_metadata() -> None:
    def _get_observation() -> AssetObservation:
        return AssetObservation(
            asset_key=AssetKey("my_key"),
            description="foo",
            metadata={"foo": "bar"},
            tags={"baz": "qux"},
            partition="my_partition",
        )

    assert _get_observation() == _get_observation()

    assert _get_observation().with_metadata({"new": "metadata"}) == AssetObservation(
        asset_key=AssetKey("my_key"),
        description="foo",
        metadata={"new": "metadata"},
        tags={"baz": "qux"},
        partition="my_partition",
    )

    obs = _get_observation()

    assert obs.with_metadata({**obs.metadata, "new": "metadata"}) == AssetObservation(
        asset_key=AssetKey("my_key"),
        description="foo",
        metadata={"foo": "bar", "new": "metadata"},
        tags={"baz": "qux"},
        partition="my_partition",
    )


def test_asset_check_result_object_with_metadata() -> None:
    def _get_check_result() -> AssetCheckResult:
        return AssetCheckResult(
            asset_key=AssetKey("my_key"),
            metadata={"foo": "bar"},
            passed=True,
            severity=AssetCheckSeverity.WARN,
            description="foo",
            check_name="my_check",
        )

    assert _get_check_result() == _get_check_result()

    assert _get_check_result().with_metadata({"new": "metadata"}) == AssetCheckResult(
        asset_key=AssetKey("my_key"),
        metadata={"new": "metadata"},
        passed=True,
        severity=AssetCheckSeverity.WARN,
        description="foo",
        check_name="my_check",
    )

    check = _get_check_result()
    assert check.with_metadata({**check.metadata, "new": "metadata"}) == AssetCheckResult(
        asset_key=AssetKey("my_key"),
        metadata={"foo": "bar", "new": "metadata"},
        passed=True,
        severity=AssetCheckSeverity.WARN,
        description="foo",
        check_name="my_check",
    )

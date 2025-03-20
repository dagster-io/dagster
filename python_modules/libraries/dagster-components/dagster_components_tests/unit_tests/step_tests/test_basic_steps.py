from collections.abc import Iterator, Mapping
from typing import Optional

from dagster._config.pythonic_config.config import Config
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.definitions.result import AssetRecord
from dagster._core.events import StepMaterializationData
from dagster._core.execution.context.invocation import build_asset_context
from dagster_components import ComponentLoadContext
from dagster_components.components.step.step import (
    ExecutionContext,
    ExecutionRecord,
    StepComponent,
    execute_step,
)
from dagster_shared import check


class SingleAssetStep(StepComponent):
    def execute(self, context: ExecutionContext) -> ExecutionRecord:
        return ExecutionRecord.for_asset(
            metadata={"whatami": "singleasset"},
        )


class ManyAssetStep(StepComponent):
    def execute(self, context: ExecutionContext) -> ExecutionRecord:
        return ExecutionRecord(
            asset_records=[AssetRecord(asset_key=asset.key) for asset in (self.assets or [])]
        )


class SomeConfig(Config):
    a_value: str


class SingleAssetWithConfigStep(StepComponent):
    def execute(self, context: ExecutionContext, config: SomeConfig) -> ExecutionRecord:
        return ExecutionRecord(
            asset_records=[
                AssetRecord(
                    asset_key=next(iter(self.assets)).key, metadata={"config": config.a_value}
                )
            ]
        )


class AResource:
    def get_value(self) -> str:
        return "a_value"


class SingleAssetWithResource(StepComponent):
    def execute(
        self, context: ExecutionContext, a_resource: ResourceParam[AResource]
    ) -> ExecutionRecord:
        a_resource = check.inst(a_resource, AResource)
        return ExecutionRecord.for_asset(
            metadata={"resource": a_resource.get_value()},
        )

    def required_resource_keys(self) -> set[str]:
        return {"a_resource"}


def get_assets_def(step: StepComponent) -> AssetsDefinition:
    defs = step.build_defs(ComponentLoadContext.for_test())
    specs = defs.get_all_asset_specs()
    assert len(specs) > 0
    return defs.get_assets_def(specs[0].key)


def execute_single_asset(
    step: StepComponent,
    resources: Optional[Mapping[str, object]] = None,
) -> AssetMaterialization:
    mats = list(execute_many_assets(step, resources=resources))
    assert len(mats) == 1
    return mats[0]


def execute_many_assets(
    step: StepComponent,
    resources: Optional[Mapping[str, object]] = None,
) -> Iterator[AssetMaterialization]:
    result = execute_step(step, resources=resources)
    assert result.success
    mat_events = result.get_asset_materialization_events()
    for mat_event in mat_events:
        assert isinstance(mat_event.event_specific_data, StepMaterializationData)
        yield mat_event.event_specific_data.materialization


def test_hello_world() -> None:
    step = SingleAssetStep(name="hello_world", assets=[AssetSpec("the_key")])
    assert isinstance(get_assets_def(step), AssetsDefinition)

    materialization = execute_single_asset(step)
    assert materialization.metadata == {"whatami": TextMetadataValue("singleasset")}


def test_hello_world_autoname() -> None:
    step = SingleAssetStep(assets=[AssetSpec("the_key")])
    assets_def = get_assets_def(step)
    assert assets_def.op.name == "execute__the_key"


def test_hello_many_asset() -> None:
    step = ManyAssetStep(assets=[AssetSpec("the_key"), AssetSpec("the_key2")])
    assert step.name == "execute__the_key__the_key2"

    assets_def = get_assets_def(step)
    assert assets_def.keys == {AssetKey("the_key"), AssetKey("the_key2")}

    mats = list(execute_many_assets(step))
    assert len(mats) == 2
    assert mats[0].asset_key == AssetKey("the_key")
    assert mats[1].asset_key == AssetKey("the_key2")


def test_kitchen_sink() -> None:
    step = SingleAssetStep(
        name="foo",
        assets=[AssetSpec("the_key")],
        checks=[AssetCheckSpec("check_name", asset="the_key")],
        description="desc",
        tags={"tag": "val"},
        retry_policy=RetryPolicy(max_retries=1),
        pool="a_pool",
        can_subset=True,
    )

    assets_def = get_assets_def(step)
    assert assets_def.op.name == "foo"
    assert assets_def.op.tags == {"tag": "val"}
    assert assets_def.op.retry_policy == RetryPolicy(max_retries=1)
    assert assets_def.op.pool == "a_pool"

    assert assets_def.can_subset is True
    assert assets_def.key == AssetKey("the_key")
    assert assets_def.check_keys == {
        AssetCheckKey(asset_key=AssetKey("the_key"), name="check_name")
    }


def test_step_with_config() -> None:
    step = SingleAssetWithConfigStep(assets=[AssetSpec("the_key")])

    record = step.execute(ExecutionContext(build_asset_context()), SomeConfig(a_value="foo"))
    assert isinstance(record, ExecutionRecord)

    assert get_assets_def(step).op.name == "execute__the_key"
    assert get_assets_def(step).op.config_schema
    assert execute_step(
        step, run_config={"ops": {"execute__the_key": {"config": {"a_value": "foo"}}}}
    ).success


def test_step_with_resource() -> None:
    step = SingleAssetWithResource(assets=[AssetSpec("the_key")])
    record = step.execute(ExecutionContext(build_asset_context()), a_resource=AResource())
    assert isinstance(record, ExecutionRecord)
    assert next(iter(record.asset_records or [])).metadata == {"resource": "a_value"}

    defs = step.build_defs(ComponentLoadContext.for_test(resources={"a_resource": AResource()}))
    Definitions.validate_loadable(defs)

    assets_def = defs.get_assets_def("the_key")
    assert isinstance(assets_def, AssetsDefinition)

    result = materialize([assets_def])
    assert result.success

    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    assert isinstance(mat_events[0].event_specific_data, StepMaterializationData)
    assert mat_events[0].event_specific_data.materialization.metadata == {
        "resource": TextMetadataValue("a_value")
    }

    mat = execute_single_asset(step, resources={"a_resource": AResource()})
    assert mat.metadata == {"resource": TextMetadataValue("a_value")}

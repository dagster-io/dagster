from dagster._config.pythonic_config.config import Config
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization, AssetObservation
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.definitions.observe import observe
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.definitions.result import ObserveResult
from dagster._core.events import AssetObservationData, StepMaterializationData
from dagster._core.execution.context.invocation import build_asset_context
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster_components import ComponentLoadContext
from dagster_components.components.step.config_param import ConfigParam
from dagster_components.components.step.step import (
    AssetCheckRecord,
    AssetRecord,
    ExecutionContext,
    ExecutionRecord,
    StepComponent,
    execute_step_component,
    mark_spec_observable,
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
    def execute(
        self, context: ExecutionContext, config: ConfigParam[SomeConfig]
    ) -> ExecutionRecord:
        return ExecutionRecord(
            asset_records=[
                AssetRecord(
                    asset_key=next(iter(self.assets)).key, metadata={"config": config.a_value}
                )
            ]
        )


class SingleAssetWithConfigStepAltName(StepComponent):
    def execute(
        self, context: ExecutionContext, diff_name: ConfigParam[SomeConfig]
    ) -> ExecutionRecord:
        return ExecutionRecord(
            asset_records=[
                AssetRecord(
                    asset_key=next(iter(self.assets)).key, metadata={"config": diff_name.a_value}
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


def get_assets_def(step: StepComponent) -> AssetsDefinition:
    defs = step.build_defs(ComponentLoadContext.for_test())
    specs = defs.get_all_asset_specs()
    assert len(specs) > 0
    return defs.get_assets_def(specs[0].key)


def single_asset_mat(result: ExecuteInProcessResult) -> AssetMaterialization:
    mats = list(asset_mats(result))
    assert len(mats) == 1
    return mats[0]


def asset_mats(result: ExecuteInProcessResult) -> list[AssetMaterialization]:
    def _fn():
        mats = result.get_asset_materialization_events()
        for mat in mats:
            assert isinstance(mat.event_specific_data, StepMaterializationData)
            yield mat.event_specific_data.materialization

    return list(_fn())


def single_asset_obs(result: ExecuteInProcessResult) -> AssetObservation:
    obs = asset_obs(result)
    assert len(obs) == 1
    return obs[0]


def asset_obs(result: ExecuteInProcessResult) -> list[AssetObservation]:
    def _fn():
        obs = result.get_asset_observation_events()
        for ob in obs:
            assert isinstance(ob.event_specific_data, AssetObservationData)
            yield ob.event_specific_data.asset_observation

    return list(_fn())


def single_asset_check_eval(result: ExecuteInProcessResult) -> AssetCheckEvaluation:
    evals = result.get_asset_check_evaluations()
    assert len(evals) == 1
    return evals[0]


def test_hello_world() -> None:
    step = SingleAssetStep(name="hello_world", assets=[AssetSpec("the_key")])
    assert isinstance(get_assets_def(step), AssetsDefinition)

    materialization = single_asset_mat(execute_step_component(step))
    assert materialization.metadata == {"whatami": TextMetadataValue("singleasset")}


def test_hello_world_decorator() -> None:
    # avoiding name collision at module scope
    from dagster_components.components.step.decorator import step

    @step(assets=[AssetSpec("the_key")])
    def hello_world(context: ExecutionContext) -> ExecutionRecord:
        return ExecutionRecord.for_asset(
            metadata={"whatami": "singleasset"},
        )

    # directly invoke loader func
    step_inst = hello_world(ComponentLoadContext.for_test())

    assert isinstance(get_assets_def(step_inst), AssetsDefinition)

    materialization = single_asset_mat(execute_step_component(step_inst))
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

    mats = asset_mats(execute_step_component(step))
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
    assert execute_step_component(
        step, run_config={"ops": {"execute__the_key": {"config": {"a_value": "foo"}}}}
    ).success


def test_step_with_config_alt_name() -> None:
    step = SingleAssetWithConfigStepAltName(assets=[AssetSpec("the_key")])

    assert get_assets_def(step).op.name == "execute__the_key"
    assert get_assets_def(step).op.config_schema
    assert execute_step_component(
        step, run_config={"ops": {"execute__the_key": {"config": {"a_value": "foo"}}}}
    ).success


def test_step_with_resource() -> None:
    step = SingleAssetWithResource(assets=[AssetSpec("the_key")])
    record = step.execute(ExecutionContext(build_asset_context()), a_resource=AResource())
    assert isinstance(record, ExecutionRecord)
    assert next(iter(record.asset_records)).metadata == {"resource": "a_value"}

    defs = step.build_defs(ComponentLoadContext.for_test(resources={"a_resource": AResource()}))
    Definitions.validate_loadable(defs)

    assets_def = defs.get_assets_def("the_key")
    assert isinstance(assets_def, AssetsDefinition)

    result = materialize([assets_def])
    assert result.success

    mat = single_asset_mat(execute_step_component(step, resources={"a_resource": AResource()}))
    assert mat.metadata == {"resource": TextMetadataValue("a_value")}


class SingleAssetSingleCheck(StepComponent):
    def execute(self, context: ExecutionContext) -> ExecutionRecord:
        return ExecutionRecord(
            asset_records=[AssetRecord()],
            asset_check_records=[AssetCheckRecord(passed=True)],
        )


def test_single_asset_single_check() -> None:
    step = SingleAssetSingleCheck(
        assets=[AssetSpec("the_key")],
        checks=[AssetCheckSpec("check_name", asset="the_key")],
    )
    result = execute_step_component(step)
    assert result.success
    assert single_asset_mat(result).asset_key == AssetKey("the_key")
    assert single_asset_check_eval(result).passed
    assert single_asset_check_eval(result).asset_key == AssetKey("the_key")
    assert single_asset_check_eval(result).check_name == "check_name"


class SingleCheckStep(StepComponent):
    def execute(self, context: ExecutionContext) -> ExecutionRecord:
        return ExecutionRecord(
            asset_check_records=[AssetCheckRecord(passed=True)],
        )


def test_single_standalone_check() -> None:
    step = SingleCheckStep(
        checks=[AssetCheckSpec("check_name", asset="somekey_elsewhere")],
    )
    result = execute_step_component(step)
    assert result.success
    assert single_asset_check_eval(result).asset_check_key == AssetCheckKey(
        asset_key=AssetKey("somekey_elsewhere"), name="check_name"
    )


class ManyCheckStep(StepComponent):
    def execute(self, context: ExecutionContext) -> ExecutionRecord:
        return ExecutionRecord(
            asset_check_records=[
                AssetCheckRecord(passed=True, asset_key="key_one", check_name="check_one"),
                AssetCheckRecord(passed=False, asset_key="key_two", check_name="check_two"),
            ]
        )


def test_multi_check() -> None:
    step = ManyCheckStep(
        checks=[
            AssetCheckSpec(asset="key_one", name="check_one"),
            AssetCheckSpec(asset="key_two", name="check_two"),
        ],
    )

    result = execute_step_component(step)
    assert result.success
    eval_list = result.get_asset_check_evaluations()

    evals = {e.asset_check_key: e for e in eval_list}

    k1_c1 = AssetCheckKey(asset_key=AssetKey("key_one"), name="check_one")
    k2_c2 = AssetCheckKey(asset_key=AssetKey("key_two"), name="check_two")

    assert set(evals.keys()) == {k1_c1, k2_c2}

    assert evals[k1_c1].passed
    assert not evals[k2_c2].passed


def test_observable_source_asset() -> None:
    @observable_source_asset(
        key="my_asset",
        description="my description",
        tags={"tag": "val"},
    )
    def fn() -> DataVersion:
        return DataVersion("my_data")

    result = observe(assets=[fn])
    assert result.success
    asset_observation = single_asset_obs(result)
    assert asset_observation.data_version == "my_data"


def test_emit_observe_result_from_asset() -> None:
    @asset
    def emit_observe() -> ObserveResult:
        return ObserveResult(data_version=DataVersion("my_data"))

    result = materialize([emit_observe])
    assert result.success

    # I can't believe this is our behavior. This should be one event
    observe_events = result.get_asset_observation_events()
    assert len(observe_events) == 0

    # I can't believe this is our behavior. This should be zero events
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    mat_event = mat_events[0]
    assert isinstance(mat_event.event_specific_data, StepMaterializationData)
    mat = mat_event.event_specific_data.materialization
    assert mat.tags
    assert mat.tags["dagster/data_version"] == "my_data"


def test_osa_in_step() -> None:
    # Note in the mental model I'm not even sure it is necesary
    # to model this as a separate use case at all, but demonstrating
    # how we would support backwards compat for good measure
    class SingleObserve(StepComponent):
        def execute(self, context: ExecutionContext) -> ExecutionRecord:
            return ExecutionRecord.for_asset(
                asset_key="my_asset",
                data_version=DataVersion("my_data"),
            )

    result = execute_step_component(
        SingleObserve(assets=[mark_spec_observable(AssetSpec("my_asset"))])
    )

    assert result.success
    obs = single_asset_obs(result)
    assert obs.data_version == "my_data"

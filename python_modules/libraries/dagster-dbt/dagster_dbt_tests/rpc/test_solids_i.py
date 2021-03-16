import uuid
from typing import Any, Dict, Tuple

import pytest
from dagster import (
    AssetKey,
    DagsterInstance,
    ModeDefinition,
    PipelineDefinition,
    SolidDefinition,
    SolidExecutionResult,
    configured,
    execute_pipeline,
    execute_solid,
    resource,
)
from dagster_dbt import (
    DbtRpcClient,
    DbtRpcOutput,
    dbt_rpc_run,
    dbt_rpc_run_and_wait,
    dbt_rpc_test,
    local_dbt_rpc_resource,
)
from mock import MagicMock


def output_for_solid_executed_with_rpc_resource(
    a_solid, rpc_resource=local_dbt_rpc_resource
) -> Tuple[SolidExecutionResult, DbtRpcOutput]:
    mode_def = ModeDefinition(resource_defs={"dbt_rpc": rpc_resource})  # use config defaults
    solid_result = execute_solid(a_solid, mode_def)

    assert solid_result.success
    output = solid_result.output_value()
    assert isinstance(output, DbtRpcOutput)
    return solid_result, output


class TestDBTRunAndWaitSolid:

    ALL_MODELS_KEY_SET = {
        "model.dagster_dbt_test_project.sort_by_calories",
        "model.dagster_dbt_test_project.least_caloric",
        "model.dagster_dbt_test_project.sort_cold_cereals_by_calories",
        "model.dagster_dbt_test_project.sort_hot_cereals_by_calories",
    }

    def test_run_all(self, dbt_rpc_server):  # pylint: disable=unused-argument
        run_all_fast_poll = configured(dbt_rpc_run_and_wait, name="run_all_fast_poll")(
            {"interval": 2}
        )

        dagster_result, dbt_output = output_for_solid_executed_with_rpc_resource(run_all_fast_poll)

        executed_model_from_result = set(res.node["unique_id"] for res in dbt_output.result.results)
        assert executed_model_from_result == TestDBTRunAndWaitSolid.ALL_MODELS_KEY_SET

        materialization_asset_keys = set(
            mat.asset_key.to_string() for mat in dagster_result.materializations_during_compute
        )
        assert materialization_asset_keys == {
            AssetKey(key.split(".")).to_string()
            for key in TestDBTRunAndWaitSolid.ALL_MODELS_KEY_SET
        }

    SINGLE_MODEL_KEY_SET = {"model.dagster_dbt_test_project.least_caloric"}

    def test_run_single(self, dbt_rpc_server):  # pylint: disable=unused-argument
        run_single_fast_poll = configured(dbt_rpc_run_and_wait, name="run_least_caloric")(
            {"interval": 2, "models": ["least_caloric"]}
        )

        dagster_result, dbt_output = output_for_solid_executed_with_rpc_resource(
            run_single_fast_poll
        )

        executed_model_from_result = set(res.node["unique_id"] for res in dbt_output.result.results)
        assert executed_model_from_result == TestDBTRunAndWaitSolid.SINGLE_MODEL_KEY_SET

        materialization_asset_keys = set(
            mat.asset_key.to_string() for mat in dagster_result.materializations_during_compute
        )

        assert materialization_asset_keys == {
            AssetKey(key.split(".")).to_string()
            for key in TestDBTRunAndWaitSolid.SINGLE_MODEL_KEY_SET
        }


SINGLE_OP_CONFIGS: Dict[str, Tuple[SolidDefinition, Dict[str, Any]]] = {
    "run": (dbt_rpc_run, {"models": ["model_1", "model_2"], "exclude": ["bad_model"]}),
    "test": (
        dbt_rpc_test,
        {
            "models": ["model_1", "model_2"],
            "exclude": ["bad_model"],
            "data": False,
            "schema": True,
        },
    ),
}


class TestDBTSingleOperationSolids:
    @pytest.mark.parametrize("op", list(SINGLE_OP_CONFIGS.keys()))
    def test_dbt_rpc_single_op(self, op: str):
        op_solid, op_config = SINGLE_OP_CONFIGS[op]

        mocked_rpc_client = MagicMock(spec=DbtRpcClient)
        mocked_client_op_method = getattr(mocked_rpc_client, op)

        @resource
        def mock_dbt_rpc_resource(_init_context):
            return mocked_rpc_client

        response_sentinel_value = "<rpc response: {}>".format(uuid.uuid4())
        mocked_client_op_method.return_value.text = response_sentinel_value
        request_token_sentinel_value = "<request token: {}>".format(uuid.uuid4())
        mocked_client_op_method.return_value.json.return_value = {
            "result": {"request_token": request_token_sentinel_value}
        }

        configured_solid = configured(op_solid, name="configured_solid")(op_config)

        instance = DagsterInstance.ephemeral()
        result = execute_pipeline(
            PipelineDefinition(
                [configured_solid],
                name="test",
                mode_defs=[ModeDefinition(resource_defs={"dbt_rpc": mock_dbt_rpc_resource})],
            ),
            instance=instance,
        )

        mocked_client_op_method.assert_called_once_with(**op_config)
        assert (
            result.output_for_solid(configured_solid.name, "request_token")
            == request_token_sentinel_value
        )
        assert any(
            response_sentinel_value in event.message for event in instance.all_logs(result.run_id)
        )

from dagster_dbt.core.dbt_cli_event import DbtFusionCliEventMessage


def test_dbt_fusion_cli_event_message_get_check_passed():
    # 1. Success test event (what dbt-fusion emits: "pass")
    success_test_event = {
        "info": {"name": "NodeFinished", "msg": "Test passed", "invocation_id": "1"},
        "data": {
            "node_info": {"unique_id": "test.my_project.my_test", "node_status": "pass"},
            "status": "pass",
            "num_failures": 0,
        },
    }

    # 2. Failed test event
    failed_test_event = {
        "info": {"name": "NodeFinished", "msg": "Test failed", "invocation_id": "2"},
        "data": {
            "node_info": {"unique_id": "test.my_project.my_test", "node_status": "fail"},
            "status": "fail",
            "num_failures": 1,
        },
    }

    # 3. Model success event (not a test, e.g. a model run that emits "success")
    success_model_event = {
        "info": {"name": "NodeFinished", "msg": "Model successful", "invocation_id": "3"},
        "data": {
            "node_info": {"unique_id": "model.my_project.my_model", "node_status": "success"},
            "status": "success",
        },
    }

    # Test 1: dbt-fusion test passing
    msg1 = DbtFusionCliEventMessage(raw_event=success_test_event, event_history_metadata={})
    assert msg1._get_check_passed() is True

    # Test 2: dbt-fusion test failing
    msg2 = DbtFusionCliEventMessage(raw_event=failed_test_event, event_history_metadata={})
    assert msg2._get_check_passed() is False

    # Test 3: dbt-fusion model success
    msg3 = DbtFusionCliEventMessage(raw_event=success_model_event, event_history_metadata={})
    assert msg3._get_check_passed() is True

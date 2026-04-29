import time
from unittest.mock import MagicMock, patch

from dagster import build_op_context

import dagster_aws.pipes.clients.emr_serverless as emr_serverless_module
from dagster_aws.pipes import PipesEMRServerlessClient


def test_emr_serverless_url_refresh():
    mock_client = MagicMock()
    
    # Mock get_job_run to return RUNNING twice then SUCCESS
    mock_client.get_job_run.side_effect = [
        {"jobRun": {"state": "RUNNING", "applicationId": "app-1", "jobRunId": "job-1"}},
        {"jobRun": {"state": "RUNNING", "applicationId": "app-1", "jobRunId": "job-1"}},
        {"jobRun": {"state": "SUCCESS", "applicationId": "app-1", "jobRunId": "job-1"}}
    ]
    
    # Mock get_dashboard_for_job_run to return different URLs in dict shape
    mock_client.get_dashboard_for_job_run.side_effect = [
        {"url": "https://spark-ui-1.com", "ResponseMetadata": {}},
        {"url": "https://spark-ui-2.com", "ResponseMetadata": {}},
        {"url": "https://spark-ui-completed.com", "ResponseMetadata": {}},
    ]

    # Set refresh interval to 0.1 seconds for testing
    with patch.object(emr_serverless_module, "DASHBOARD_URL_REFRESH_INTERVAL", 0.1):
        # We need to mock time.sleep to bypass the wait, but also ensure 
        # that time.time() advances enough between calls if we were testing based on real time.
        
        start_time = time.time()
        # Use a function to avoid StopIteration if time.time() is called more than expected (e.g. by logging)
        current_time = [start_time]
        def mock_time_fn():
            ret = current_time[0]
            current_time[0] += 0.5
            return ret

        with patch("time.time", side_effect=mock_time_fn):            
            # Also mock sleep to do nothing
            with patch("time.sleep"):
                client = PipesEMRServerlessClient(client=mock_client)
                context = build_op_context()
                
                # Mock add_output_metadata to track calls
                context.add_output_metadata = MagicMock()
                
                start_response = {"applicationId": "app-1", "jobRunId": "job-1"}
                response, final_url = client._wait_for_completion(context, start_response) # noqa: SLF001
                
                assert response["jobRun"]["state"] == "SUCCESS"
                assert final_url == "https://spark-ui-2.com" # The last one from RUNNING state
                
                # Verify get_dashboard_for_job_run was called:
                # 1. First time in RUNNING (None)
                # 2. Second time in RUNNING (Time threshold exceeded)
                assert mock_client.get_dashboard_for_job_run.call_count == 2
                
                # Verify metadata was reported twice
                assert context.add_output_metadata.call_count == 2

def test_emr_serverless_terminal_refresh():
    mock_client = MagicMock()
    
    # Mock get_job_run to return SUCCESS immediately
    mock_client.get_job_run.side_effect = [
        {"jobRun": {"state": "SUCCESS", "applicationId": "app-1", "jobRunId": "job-1"}}
    ]
    
    # Mock get_dashboard_for_job_run in dict shape
    mock_client.get_dashboard_for_job_run.return_value = {"url": "https://spark-ui-completed.com", "ResponseMetadata": {}}

    client = PipesEMRServerlessClient(client=mock_client)
    context = build_op_context()
    
    start_response = {"applicationId": "app-1", "jobRunId": "job-1"}
    response, final_url = client._wait_for_completion(context, start_response) # noqa: SLF001
    
    assert response["jobRun"]["state"] == "SUCCESS"
    assert final_url == "https://spark-ui-completed.com"
    assert mock_client.get_dashboard_for_job_run.call_count == 1

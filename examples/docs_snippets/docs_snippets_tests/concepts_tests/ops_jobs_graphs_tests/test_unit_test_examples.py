from docs_snippets.concepts.ops_jobs_graphs.unit_tests import (
    test_job,
    test_basic_asset,
    test_data_assets,
    test_event_stream,
    test_op_with_config,
    test_job_with_config,
    test_op_with_context,
    test_op_with_resource,
    test_asset_with_inputs,
    test_asset_requires_bar,
    test_op_with_invocation,
    test_asset_requires_config,
    test_assets_require_service,
    test_inputs_op_with_invocation,
)


def test_unit_tests():
    test_job()
    test_op_with_invocation()
    test_op_with_context()
    test_job_with_config()
    test_event_stream()
    test_inputs_op_with_invocation()
    test_basic_asset()
    test_asset_with_inputs()
    test_data_assets()
    test_op_with_config()
    test_op_with_resource()
    test_asset_requires_bar()
    test_asset_requires_config()
    test_assets_require_service()

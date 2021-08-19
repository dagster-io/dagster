from docs_snippets.concepts.solids_pipelines.unit_tests import (
    test_event_stream,
    test_inputs_solid_with_invocation,
    test_pipeline,
    test_pipeline_with_config,
    test_solid_resource_def,
    test_solid_with_context,
    test_solid_with_invocation,
    test_subset_execution,
)


def test_unit_tests():
    test_pipeline()
    test_solid_with_invocation()
    test_solid_with_context()
    test_pipeline_with_config()
    test_subset_execution()
    test_event_stream()
    test_inputs_solid_with_invocation()
    test_solid_resource_def()

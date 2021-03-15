from docs_snippets.concepts.solids_pipelines.unit_tests import (
    test_event_stream,
    test_pipeline,
    test_pipeline_with_config,
    test_solid,
    test_subset_execution,
)


def test_unit_tests():
    test_pipeline()
    test_solid()
    test_pipeline_with_config()
    test_subset_execution()
    test_event_stream()

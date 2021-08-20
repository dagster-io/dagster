from dagster import execute_pipeline
from docs_snippets_crag.concepts.configuration.configured_named_solid_example import (
    dataset_pipeline,
)


def test_pipeline():

    result = execute_pipeline(
        dataset_pipeline,
        {
            "solids": {
                "sample_dataset": {"inputs": {"xs": [4, 8, 15, 16, 23, 42]}},
                "full_dataset": {
                    "inputs": {"xs": [33, 30, 27, 29, 32, 30, 27, 28, 30, 30, 30, 31]}
                },
            }
        },
    )

    sample_dataset = result.result_for_solid("sample_dataset").output_value()
    full_dataset = result.result_for_solid("full_dataset").output_value()

    assert len(sample_dataset) == 5
    assert len(full_dataset) == 12

from docs_snippets_crag.concepts.configuration.configured_named_op_example import datasets


def test_job():

    result = datasets.to_job().execute_in_process(
        run_config={
            "ops": {
                "sample_dataset": {"inputs": {"xs": [4, 8, 15, 16, 23, 42]}},
                "full_dataset": {
                    "inputs": {"xs": [33, 30, 27, 29, 32, 30, 27, 28, 30, 30, 30, 31]}
                },
            }
        }
    )

    sample_dataset = result.output_for_node("sample_dataset")
    full_dataset = result.output_for_node("full_dataset")

    assert len(sample_dataset) == 5
    assert len(full_dataset) == 12

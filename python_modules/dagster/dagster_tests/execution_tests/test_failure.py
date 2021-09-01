from dagster import EventMetadataEntry, Failure, execute_pipeline, lambda_solid, pipeline


def test_failure():
    @lambda_solid
    def throw():
        raise Failure(
            description="it Failure",
            metadata_entries=[
                EventMetadataEntry.text(label="label", text="text", description="description")
            ],
        )

    @pipeline
    def failure():
        throw()

    result = execute_pipeline(failure, raise_on_error=False)
    assert not result.success
    failure_data = result.result_for_solid("throw").failure_data
    assert failure_data
    assert failure_data.error.cls_name == "Failure"

    # hard coded
    assert failure_data.user_failure_data.label == "intentional-failure"
    # from Failure
    assert failure_data.user_failure_data.description == "it Failure"
    assert failure_data.user_failure_data.metadata_entries[0].label == "label"
    assert failure_data.user_failure_data.metadata_entries[0].entry_data.text == "text"
    assert failure_data.user_failure_data.metadata_entries[0].description == "description"

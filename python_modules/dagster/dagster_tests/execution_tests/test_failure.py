from dagster import Failure
from dagster._core.definitions.decorators import op
from dagster._core.definitions.metadata import MetadataValue
from dagster._legacy import execute_pipeline, pipeline


def test_failure():
    @op
    def throw():
        raise Failure(
            description="it Failure",
            metadata={"label": "text"},
        )

    @pipeline
    def failure():
        throw()

    result = execute_pipeline(failure, raise_on_error=False)
    assert not result.success
    failure_data = result.result_for_node("throw").failure_data
    assert failure_data
    assert failure_data.error.cls_name == "Failure"

    # hard coded
    assert failure_data.user_failure_data.label == "intentional-failure"
    # from Failure
    assert failure_data.user_failure_data.description == "it Failure"
    assert failure_data.user_failure_data.metadata["label"] == MetadataValue.text("text")

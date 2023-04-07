from dagster import Failure, job
from dagster._core.definitions.decorators import op
from dagster._core.definitions.metadata import MetadataValue


def test_failure():
    @op
    def throw():
        raise Failure(
            description="it Failure",
            metadata={"label": "text"},
        )

    @job
    def failure():
        throw()

    result = failure.execute_in_process(raise_on_error=False)
    assert not result.success
    failure_data = result.failure_data_for_node("throw")
    assert failure_data
    assert failure_data.error.cls_name == "Failure"

    # hard coded
    assert failure_data.user_failure_data.label == "intentional-failure"
    # from Failure
    assert failure_data.user_failure_data.description == "it Failure"
    assert failure_data.user_failure_data.metadata["label"] == MetadataValue.text("text")

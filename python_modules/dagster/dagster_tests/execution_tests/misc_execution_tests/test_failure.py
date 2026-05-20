import dagster as dg
from dagster._core.definitions.metadata import MetadataValue


def test_failure():
    @dg.op
    def throw():
        raise dg.Failure(
            description="it Failure",
            metadata={"label": "text"},
        )

    @dg.job
    def failure():
        throw()

    result = failure.execute_in_process(raise_on_error=False)
    assert not result.success
    failure_data = result.failure_data_for_node("throw")
    assert failure_data
    assert failure_data.error.cls_name == "Failure"  # ty: ignore[unresolved-attribute]

    # hard coded
    assert failure_data.user_failure_data.label == "intentional-failure"  # ty: ignore[unresolved-attribute]
    # from Failure
    assert failure_data.user_failure_data.description == "it Failure"  # ty: ignore[unresolved-attribute]
    assert failure_data.user_failure_data.metadata["label"] == MetadataValue.text("text")  # ty: ignore[unresolved-attribute]

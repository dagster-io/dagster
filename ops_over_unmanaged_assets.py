from dagster import DagsterInstance, job, op
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.execution.context.compute import OpExecutionContext

# This is an example of how a user who has a lot of existing ops that did
# not want to migrate could still plug into the asset graph


@op
def op_produces_asset_one(context: OpExecutionContext):
    context.log_event(
        AssetMaterialization(
            asset_key="observable_asset_one", metadata={"foo_metadata_label": "metadata_value_1"}
        )
    )


@job
def my_job():
    op_produces_asset_one()


if __name__ == "__main__":
    my_job.execute_in_process(instance=DagsterInstance.get())

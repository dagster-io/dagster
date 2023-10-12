import os

from dagster import (
    AssetExecutionContext,
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
    RunRequest,
    SensorEvaluationContext,
    SensorResult,
    asset,
    define_asset_job,
    sensor,
)

# start_dynamic_partitions_marker
images_partitions_def = DynamicPartitionsDefinition(name="images")


@asset(partitions_def=images_partitions_def)
def images(context: AssetExecutionContext):
    ...


# end_dynamic_partitions_marker

# start_dynamic_partitions_2


images_job = define_asset_job(
    "images_job", AssetSelection.keys("images"), partitions_def=images_partitions_def
)


@sensor(job=images_job)
def image_sensor(context: SensorEvaluationContext):
    new_images = [
        img_filename
        for img_filename in os.listdir(os.getenv("MY_DIRECTORY"))
        if not context.instance.has_dynamic_partition(
            images_partitions_def.name, img_filename
        )
    ]

    return SensorResult(
        run_requests=[
            RunRequest(partition_key=img_filename) for img_filename in new_images
        ],
        dynamic_partitions_requests=[
            images_partitions_def.build_add_request(new_images)
        ],
    )


# end_dynamic_partitions_2

defs = Definitions([images], sensors=[image_sensor], jobs=[images_job])

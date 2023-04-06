import os

from dagster import (
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
    RunRequest,
    asset,
    define_asset_job,
    sensor,
)

# start_dynamic_partitions_marker
images_partitions_def = DynamicPartitionsDefinition(name="images")


@asset(partitions_def=images_partitions_def)
def images(context):
    ...


# end_dynamic_partitions_marker

# start_dynamic_partitions_2


images_job = define_asset_job(
    "images_job", AssetSelection.keys("images"), partitions_def=images_partitions_def
)


@sensor(job=images_job)
def image_sensor(context):
    new_images = [
        img_filename
        for img_filename in os.listdir(os.getenv("MY_DIRECTORY"))
        if not context.instance.has_dynamic_partition(
            images_partitions_def.name, img_filename
        )
    ]

    context.instance.add_dynamic_partitions(images_partitions_def.name, new_images)

    run_requests = [
        RunRequest(partition_key=img_filename) for img_filename in new_images
    ]
    return run_requests


# end_dynamic_partitions_2

defs = Definitions([images], sensors=[image_sensor], jobs=[images_job])

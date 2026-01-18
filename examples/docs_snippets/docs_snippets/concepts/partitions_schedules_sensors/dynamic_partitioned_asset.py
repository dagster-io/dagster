import os

import dagster as dg

# start_dynamic_partitions_marker
images_partitions_def = dg.DynamicPartitionsDefinition(name="images")


@dg.asset(partitions_def=images_partitions_def)
def images(context: dg.AssetExecutionContext): ...


# end_dynamic_partitions_marker

# start_dynamic_partitions_2


images_job = dg.define_asset_job(
    "images_job",
    dg.AssetSelection.assets("images"),
    partitions_def=images_partitions_def,
)


@dg.sensor(job=images_job)
def image_sensor(context: dg.SensorEvaluationContext):
    new_images = [
        img_filename
        for img_filename in os.listdir(os.getenv("MY_DIRECTORY"))
        if not images_partitions_def.has_partition_key(
            img_filename, dynamic_partitions_store=context.instance
        )
    ]

    return dg.SensorResult(
        run_requests=[
            dg.RunRequest(partition_key=img_filename) for img_filename in new_images
        ],
        dynamic_partitions_requests=[
            images_partitions_def.build_add_request(new_images)
        ],
    )


# end_dynamic_partitions_2

defs = dg.Definitions([images], sensors=[image_sensor], jobs=[images_job])

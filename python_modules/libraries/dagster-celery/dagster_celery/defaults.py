import os

broker_url = "pyamqp://guest@{hostname}:5672//".format(
    hostname=os.getenv("DAGSTER_CELERY_BROKER_HOST", "localhost")
)

backend = "rpc://"

result_backend = backend

task_default_priority = 5

task_default_queue = "dagster"

worker_prefetch_multiplier = 4

broker_transport_options = {
    # these defaults were lifted from examples - worth updating after some experience
    "max_retries": 3,
    "interval_start": 0,
    "interval_step": 0.2,
    "interval_max": 0.5,
}

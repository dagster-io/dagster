from dagster.core.storage.tags import PARTITION_NAME_TAG, PARTITION_SET_TAG
from tqdm import tqdm

RUN_PARTITIONS = "run_partitions"

RUN_DATA_MIGRATIONS = {
    RUN_PARTITIONS: lambda: migrate_run_partition,
}


def migrate_run_partition(instance, print_fn=None):
    """
    Utility method to build an asset key index from the data in existing event log records.
    Takes in event_log_storage, and a print_fn to keep track of progress.
    """
    if print_fn:
        print_fn("Querying run storage.")
    runs = instance.get_runs()
    if print_fn:
        runs = tqdm(runs)
    for run in runs:
        if PARTITION_NAME_TAG not in run.tags:
            continue
        if PARTITION_SET_TAG not in run.tags:
            continue

        instance.add_run_tags(run.run_id, run.tags)

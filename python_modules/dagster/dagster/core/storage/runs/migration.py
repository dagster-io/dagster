from contextlib import ExitStack

from tqdm import tqdm

from ..tags import PARTITION_NAME_TAG, PARTITION_SET_TAG

RUN_PARTITIONS = "run_partitions"

RUN_DATA_MIGRATIONS = {
    RUN_PARTITIONS: lambda: migrate_run_partition,
}

RUN_CHUNK_SIZE = 100


def chunked_run_iterator(storage, print_fn=None, chunk_size=RUN_CHUNK_SIZE):
    with ExitStack() as stack:
        if print_fn:
            run_count = storage.get_runs_count()
            progress = stack.enter_context(tqdm(total=run_count))
        else:
            progress = None

        cursor = None
        has_more = True

        while has_more:
            chunk = storage.get_runs(cursor=cursor, limit=chunk_size)
            has_more = chunk_size and len(chunk) >= chunk_size

            for run in chunk:
                cursor = run.run_id
                yield run

            if progress:
                progress.update(len(chunk))


def migrate_run_partition(storage, print_fn=None):
    """
    Utility method to build an asset key index from the data in existing event log records.
    Takes in event_log_storage, and a print_fn to keep track of progress.
    """
    if print_fn:
        print_fn("Querying run storage.")

    for run in chunked_run_iterator(storage, print_fn):
        if PARTITION_NAME_TAG not in run.tags:
            continue
        if PARTITION_SET_TAG not in run.tags:
            continue

        storage.add_run_tags(run.run_id, run.tags)

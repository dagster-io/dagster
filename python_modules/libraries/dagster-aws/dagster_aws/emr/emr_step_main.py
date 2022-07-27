import io
import os
import pickle
import sys
import time
from queue import Empty, Queue
from threading import Thread

import boto3
from dagster_aws.s3.file_manager import S3FileHandle, S3FileManager

from dagster._core.execution.plan.external_step import (
    PICKLED_EVENTS_FILE_NAME,
    external_instance_from_step_run_ref,
    run_step_from_ref,
)
from dagster._serdes import serialize_value

DONE = object()


def main(step_run_ref_bucket, s3_dir_key):
    session = boto3.client("s3")
    file_manager = S3FileManager(session, step_run_ref_bucket, "")
    file_handle = S3FileHandle(step_run_ref_bucket, s3_dir_key)
    step_run_ref_data = file_manager.read_data(file_handle)

    step_run_ref = pickle.loads(step_run_ref_data)

    events_bucket = step_run_ref_bucket
    events_s3_key = os.path.dirname(s3_dir_key) + "/" + PICKLED_EVENTS_FILE_NAME

    def put_events(events):
        file_obj = io.BytesIO(pickle.dumps(serialize_value(events)))
        session.put_object(Body=file_obj, Bucket=events_bucket, Key=events_s3_key)

    # Set up a thread to handle writing events back to the plan process, so execution doesn't get
    # blocked on remote communication
    events_queue = Queue()
    event_writing_thread = Thread(
        target=event_writing_loop,
        kwargs=dict(events_queue=events_queue, put_events_fn=put_events),
    )
    event_writing_thread.start()

    try:
        instance = external_instance_from_step_run_ref(
            step_run_ref, event_listener_fn=events_queue.put
        )
        # consume iterator
        list(run_step_from_ref(step_run_ref, instance))
    finally:
        events_queue.put(DONE)
        event_writing_thread.join()


def event_writing_loop(events_queue, put_events_fn):
    """
    Periodically check whether the step has posted any new events to the queue.  If they have,
    write ALL events (not just the new events) to an S3 bucket.

    This approach was motivated by a few challenges:
    * We can't expect a process on EMR to be able to hit an endpoint in the plan process, because
      the plan process might be behind someone's home internet.
    * We can't expect the plan process to be able to hit an endpoint in the process on EMR, because
      EMR is often behind a VPC.
    * S3 is eventually consistent and doesn't support appends
    """
    all_events = []

    done = False
    got_new_events = False
    time_posted_last_batch = time.time()
    while not done:
        try:
            event_or_done = events_queue.get(timeout=1)
            if event_or_done == DONE:
                done = True
            else:
                all_events.append(event_or_done)
                got_new_events = True
        except Empty:
            pass

        enough_time_between_batches = time.time() - time_posted_last_batch > 1
        if got_new_events and (done or enough_time_between_batches):
            put_events_fn(all_events)
            got_new_events = False
            time_posted_last_batch = time.time()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

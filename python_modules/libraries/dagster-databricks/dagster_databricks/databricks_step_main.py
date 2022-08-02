"""The main entrypoint for ops executed using the DatabricksPySparkStepLauncher.

This script is launched on Databricks using a `spark_python_task` and is passed the following
parameters:

- the DBFS path to the pickled `step_run_ref` file
- the DBFS path to the zipped dagster job
- paths to any other zipped packages which have been uploaded to DBFS.
"""

import gzip
import os
import pickle
import site
import sys
import tempfile
import time
import traceback
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from queue import Empty, Queue
from threading import Thread

from dagster._core.execution.plan.external_step import (
    PICKLED_EVENTS_FILE_NAME,
    external_instance_from_step_run_ref,
    run_step_from_ref,
)
from dagster._serdes import serialize_value

# This won't be set in Databricks but is needed to be non-None for the
# Dagster step to run.
if "DATABRICKS_TOKEN" not in os.environ:
    os.environ["DATABRICKS_TOKEN"] = ""

DONE = object()


def event_writing_loop(events_queue: Queue, put_events_fn):
    """
    Periodically check whether the instance has posted any new events to the queue.  If they have,
    write ALL events (not just the new events) to DBFS.
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


def main(
    step_run_ref_filepath,
    setup_filepath,
    dagster_job_zip,
):
    events_queue = None
    with tempfile.TemporaryDirectory() as tmp, StringIO() as stderr, StringIO() as stdout, redirect_stderr(
        stderr
    ), redirect_stdout(
        stdout
    ):
        try:
            # Extract any zip files to a temporary directory and add that temporary directory
            # to the site path so the contained files can be imported.
            #
            # We can't rely on pip or other packaging tools because the zipped files might not
            # even be Python packages.
            with zipfile.ZipFile(dagster_job_zip) as zf:
                zf.extractall(tmp)
            site.addsitedir(tmp)

            # We can use regular local filesystem APIs to access DBFS inside the Databricks runtime.
            with open(setup_filepath, "rb") as handle:
                databricks_config = pickle.load(handle)

            # sc and dbutils are globally defined in the Databricks runtime.
            databricks_config.setup(dbutils, sc)  # noqa pylint: disable=undefined-variable

            with open(step_run_ref_filepath, "rb") as handle:
                step_run_ref = pickle.load(handle)
            print("Running dagster job")  # noqa pylint: disable=print-call

            step_run_dir = os.path.dirname(step_run_ref_filepath)
            if step_run_ref.known_state is not None:
                attempt_count = step_run_ref.known_state.get_retry_state().get_attempt_count(
                    step_run_ref.step_key
                )
            else:
                attempt_count = 0
            events_filepath = os.path.join(
                step_run_dir,
                f"{attempt_count}_{PICKLED_EVENTS_FILE_NAME}",
            )
            stdout_filepath = os.path.join(step_run_dir, "stdout")
            stderr_filepath = os.path.join(step_run_dir, "stderr")

            # create empty files
            with open(events_filepath, "wb"), open(stdout_filepath, "wb"), open(
                stderr_filepath, "wb"
            ):
                pass

            def put_events(events):
                with gzip.open(events_filepath, "wb") as handle:
                    pickle.dump(serialize_value(events), handle)

            # Set up a thread to handle writing events back to the plan process, so execution doesn't get
            # blocked on remote communication
            events_queue = Queue()
            event_writing_thread = Thread(
                target=event_writing_loop,
                kwargs=dict(events_queue=events_queue, put_events_fn=put_events),
            )
            event_writing_thread.start()

            instance = external_instance_from_step_run_ref(
                step_run_ref, event_listener_fn=events_queue.put
            )
            # consume iterator
            list(run_step_from_ref(step_run_ref, instance))
        except Exception as e:
            # ensure that exceptiosn make their way into stdout
            traceback.print_exc()
            raise e
        finally:
            # write final stdout and stderr
            with open(stderr_filepath, "wb") as handle:
                stderr_str = stderr.getvalue()
                sys.stderr.write(stderr_str)
                handle.write(stderr_str.encode())
            with open(stdout_filepath, "wb") as handle:
                stdout_str = stdout.getvalue()
                sys.stdout.write(stdout_str)
                handle.write(stdout_str.encode())
            if events_queue is not None:
                events_queue.put(DONE)
                event_writing_thread.join()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

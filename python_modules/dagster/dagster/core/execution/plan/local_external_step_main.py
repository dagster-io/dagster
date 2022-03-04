import os
import pickle
import sys
from typing import List

from dagster.core.events.log import EventLogEntry
from dagster.core.execution.plan.external_step import (
    PICKLED_EVENTS_FILE_NAME,
    external_instance_from_step_run_ref,
    run_step_from_ref,
)
from dagster.core.storage.file_manager import LocalFileHandle, LocalFileManager
from dagster.serdes import serialize_value


def main(step_run_ref_path: str) -> None:
    file_manager = LocalFileManager(".")
    file_handle = LocalFileHandle(step_run_ref_path)
    step_run_ref = pickle.loads(file_manager.read_data(file_handle))

    all_events: List[EventLogEntry] = []

    try:
        instance = external_instance_from_step_run_ref(
            step_run_ref, event_listener_fn=all_events.append
        )
        # consume entire step iterator
        list(run_step_from_ref(step_run_ref, instance))
    finally:
        events_out_path = os.path.join(os.path.dirname(step_run_ref_path), PICKLED_EVENTS_FILE_NAME)
        with open(events_out_path, "wb") as events_file:
            pickle.dump(serialize_value(all_events), events_file)


if __name__ == "__main__":
    main(sys.argv[1])

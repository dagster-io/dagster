import os
import pickle
import sys

from dagster.core.execution.plan.external_step import PICKLED_EVENTS_FILE_NAME, run_step_from_ref
from dagster.core.instance import DagsterInstance
from dagster.core.storage.file_manager import LocalFileHandle, LocalFileManager


def main(step_run_ref_path: str) -> None:
    file_manager = LocalFileManager(".")
    file_handle = LocalFileHandle(step_run_ref_path)
    step_run_ref = pickle.loads(file_manager.read_data(file_handle))

    with DagsterInstance.ephemeral() as instance:
        events = list(run_step_from_ref(step_run_ref, instance))
        events_out_path = os.path.join(os.path.dirname(step_run_ref_path), PICKLED_EVENTS_FILE_NAME)
        with open(events_out_path, "wb") as events_file:
            pickle.dump(events, events_file)


if __name__ == "__main__":
    main(sys.argv[1])

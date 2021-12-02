"""The main entrypoint for ops executed using the DatabricksPySparkStepLauncher.

This script is launched on Databricks using a `spark_python_task` and is passed the following
parameters:

- the DBFS path to the pickled `step_run_ref` file
- the DBFS path to the zipped dagster job
- paths to any other zipped packages which have been uploaded to DBFS.
"""

import os
import pickle
import site
import sys
import tempfile
import zipfile
import logging

from dagster.core.execution.plan.external_step import PICKLED_EVENTS_FILE_NAME, run_step_from_ref
from dagster.core.instance import DagsterInstance
from dagster.core.log_manager import DAGSTER_META_KEY
from dagster.serdes import serialize_value


# This won't be set in Databricks but is needed to be non-None for the
# Dagster step to run.
if "DATABRICKS_TOKEN" not in os.environ:
    os.environ["DATABRICKS_TOKEN"] = ""


LOGS_COMPLETE = "__DONE__"


class MyHandler(logging.Handler):
    def __init__(self, events_filepath: str):
        super().__init__()
        self._all_events = []
        self._events_filepath = events_filepath

    def _write_obj(self, obj):
        with open(self._events_filepath, "wb") as handle:
            pickle.dump(obj, handle)

    def emit(self, record):
        # can't directly serialize DagsterEvents
        record.__dict__[DAGSTER_META_KEY]["dagster_event"] = serialize_value(
            record.__dict__[DAGSTER_META_KEY]["dagster_event"]
        )
        self._all_events.append(record)
        self._write_obj(self._all_events)

    def mark_complete(self):
        self._write_obj(self._all_events + [LOGS_COMPLETE])


def main(
    step_run_ref_filepath,
    setup_filepath,
    dagster_job_zip,
):
    # Extract any zip files to a temporary directory and add that temporary directory
    # to the site path so the contained files can be imported.
    #
    # We can't rely on pip or other packaging tools because the zipped files might not
    # even be Python packages.
    with tempfile.TemporaryDirectory() as tmp:

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
        events_filepath = os.path.dirname(step_run_ref_filepath) + "/" + PICKLED_EVENTS_FILE_NAME

        events_handler = MyHandler(events_filepath=events_filepath)

        with DagsterInstance.ephemeral() as instance:
            # hack to send all events to a specific filepath
            instance.get_handlers = lambda: [events_handler]
            # run the step
            list(run_step_from_ref(step_run_ref, instance))

        events_handler.mark_complete()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

"""The main entrypoint for solids executed using the DatabricksPySparkStepLauncher.

This script is launched on Databricks using a `spark_python_task` and is passed the following
parameters:

- the DBFS path to the pickled `step_run_ref` file
- the DBFS path to the zipped pipeline
- paths to any other zipped packages which have been uploaded to DBFS.
"""

import os
import pickle
import site
import sys
import tempfile
import zipfile

from dagster.core.execution.plan.external_step import PICKLED_EVENTS_FILE_NAME, run_step_from_ref
from dagster.core.instance import DagsterInstance
from dagster.serdes import serialize_value

# This won't be set in Databricks but is needed to be non-None for the
# Dagster step to run.
if "DATABRICKS_TOKEN" not in os.environ:
    os.environ["DATABRICKS_TOKEN"] = ""


def main(
    step_run_ref_filepath, setup_filepath, pipeline_zip,
):
    # Extract any zip files to a temporary directory and add that temporary directory
    # to the site path so the contained files can be imported.
    #
    # We can't rely on pip or other packaging tools because the zipped files might not
    # even be Python packages.
    with tempfile.TemporaryDirectory() as tmp:

        with zipfile.ZipFile(pipeline_zip) as zf:
            zf.extractall(tmp)
        site.addsitedir(tmp)

        # We can use regular local filesystem APIs to access DBFS inside the Databricks runtime.
        with open(setup_filepath, "rb") as handle:
            databricks_config = pickle.load(handle)

        # sc and dbutils are globally defined in the Databricks runtime.
        databricks_config.setup(dbutils, sc)  # noqa pylint: disable=undefined-variable

        with open(step_run_ref_filepath, "rb") as handle:
            step_run_ref = pickle.load(handle)
        print("Running pipeline")  # noqa pylint: disable=print-call
        with DagsterInstance.ephemeral() as instance:
            events = list(run_step_from_ref(step_run_ref, instance))

    events_filepath = os.path.dirname(step_run_ref_filepath) + "/" + PICKLED_EVENTS_FILE_NAME
    with open(events_filepath, "wb") as handle:
        pickle.dump(serialize_value(events), handle)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

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

from dagster import check
from dagster.core.execution.plan.external_step import PICKLED_EVENTS_FILE_NAME, run_step_from_ref
from dagster.serdes import serialize_value

# This won't be set in Databricks but is needed to be non-None for the
# Dagster step to run.
if "DATABRICKS_TOKEN" not in os.environ:
    os.environ["DATABRICKS_TOKEN"] = ""


def setup_s3_storage(storage):
    """Obtain AWS credentials from Databricks secrets and export so both Spark and boto can use them.
    """

    scope = storage["secret_scope"]

    # dbutils is globally defined in the Databricks runtime
    access_key = dbutils.secrets.get(  # noqa  # pylint: disable=undefined-variable
        scope=scope, key=storage["access_key_key"]
    )
    secret_key = dbutils.secrets.get(  # noqa  # pylint: disable=undefined-variable
        scope=scope, key=storage["secret_key_key"]
    )

    # Spark APIs will use this.
    # See https://docs.databricks.com/data/data-sources/aws/amazon-s3.html#alternative-1-set-aws-keys-in-the-spark-context.
    # sc is globally defined in the Databricks runtime and points to the Spark context
    sc._jsc.hadoopConfiguration().set(  # noqa  # pylint: disable=undefined-variable,protected-access
        "fs.s3n.awsAccessKeyId", access_key
    )
    sc._jsc.hadoopConfiguration().set(  # noqa  # pylint: disable=undefined-variable,protected-access
        "fs.s3n.awsSecretAccessKey", secret_key
    )

    # Boto will use these.
    os.environ["AWS_ACCESS_KEY_ID"] = access_key
    os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key


def setup_adls2_storage(storage):
    """Obtain an Azure Storage Account key from Databricks secrets and export so Spark can use it.
    """
    # dbutils is globally defined in the Databricks runtime
    storage_account_key = dbutils.secrets.get(  # noqa  # pylint: disable=undefined-variable
        scope=storage["secret_scope"], key=storage["storage_account_key_key"]
    )
    # Spark APIs will use this.
    # See https://docs.microsoft.com/en-gb/azure/databricks/data/data-sources/azure/azure-datalake-gen2#--access-directly-using-the-storage-account-access-key
    # sc is globally defined in the Databricks runtime and points to the Spark context
    sc._jsc.hadoopConfiguration().set(  # noqa  # pylint: disable=undefined-variable,protected-access
        "fs.azure.account.key.{}.dfs.core.windows.net".format(storage["storage_account_name"]),
        storage_account_key,
    )


def setup_storage(step_run_ref):
    """Setup any storage required by the run.

    At least one of S3 or ADLS2 storage should be provided in config, so that the run can
    save intermediate files to a location accessible by the original process which launched
    the job.

    This requires modifying the 'sc' global which isn't great.
    https://github.com/dagster-io/dagster/issues/2492 tracks a better solution
    """
    root_storage = step_run_ref.run_config.get(
        "intermediate_storage", step_run_ref.run_config["storage"]
    )
    check.invariant(
        "s3" in root_storage or "adls2" in root_storage, "No compatible storage found in config"
    )

    storage = step_run_ref.run_config["resources"]["pyspark_step_launcher"]["config"]["storage"]
    check.invariant(
        len(storage) == 1, "No valid storage credentials found in pyspark_step_launcher config"
    )
    check.invariant(
        list(storage)[0] == list(root_storage)[0],
        "Storage credentials in step launcher config don't match root storage",
    )

    if "s3" in storage:
        setup_s3_storage(storage["s3"])
    elif "adls2" in storage:
        setup_adls2_storage(storage["adls2"])
    else:
        raise Exception("No valid storage found!")


def main(step_run_ref_filepath, pipeline_zip):
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
        with open(step_run_ref_filepath, "rb") as handle:
            step_run_ref = pickle.load(handle)

        setup_storage(step_run_ref)

        events = list(run_step_from_ref(step_run_ref))

    events_filepath = os.path.dirname(step_run_ref_filepath) + "/" + PICKLED_EVENTS_FILE_NAME
    with open(events_filepath, "wb") as handle:
        pickle.dump(serialize_value(events), handle)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

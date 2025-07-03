# example Dataproc creation CLI:
# gcloud dataproc clusters create dagster --enable-component-gateway --bucket dagster-pipes --region us-central1 --subnet default --single-node --master-machine-type n2-standard-4 --master-boot-disk-type pd-balanced --master-boot-disk-size 100 --public-ip-address --image-version 2.2-debian12 --optional-components DOCKER --initialization-actions 'gs://dagster-pipes/init.sh' --metadata PEX_ENV_FILE_URI=gs://dagster-pipes/venv.pex --project dagster-infra

# start_asset_marker

from dagster_gcp.pipes import (
    PipesDataprocJobClient,
    PipesGCSContextInjector,
    PipesGCSMessageReader,
)
from google.cloud.dataproc_v1 import (
    Job,
    JobControllerClient,
    JobPlacement,
    PySparkJob,
    SubmitJobRequest,
)
from google.cloud.storage import Client as GCSClient

import dagster as dg


@dg.asset
def dataproc_job_asset(
    context: dg.AssetExecutionContext,
    dataproc_job_client: PipesDataprocJobClient,
):
    return dataproc_job_client.run(
        context=context,
        submit_job_params={
            "request": SubmitJobRequest(
                region="us-central1",
                project_id="dagster-infra",
                job=Job(
                    placement=JobPlacement(cluster_name="dagster"),
                    pyspark_job=PySparkJob(
                        main_python_file_uri="gs://dagster-pipes/script.py",
                        # args=["./venv.pex", "./script.py"],
                        file_uris=[
                            # "gs://dagster-pipes/venv.pex",
                            # "gs://dagster-pipes/script.py",
                        ],
                        properties={
                            "spark.pyspark.python": "/pexenvs/venv.pex/bin/python",
                            # "spark.pyspark.driver.python": "/pexenvs/venv.pex",
                            # "dataproc:pip.packages": "google-cloud-storage,git+https://github.com/dagster-io/dagster.git@main",
                            # load gs://dagster-pipes/venv.pex  as venv.pex file
                        },
                    ),
                ),
            )
        },
    ).get_results()


# end_asset_marker

# start_definitions_marker
import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "dataproc_job_client": PipesDataprocJobClient(
                client=JobControllerClient(
                    client_options={
                        "api_endpoint": "us-central1-dataproc.googleapis.com:443"
                    },
                ),
                message_reader=PipesGCSMessageReader(
                    bucket="dagster-pipes",
                    client=GCSClient(project="dagster-infra"),
                    include_stdio_in_messages=True,
                ),
                context_injector=PipesGCSContextInjector(
                    bucket="dagster-pipes",
                    client=GCSClient(project="dagster-infra"),
                ),
            )
        },
    )


# end_definitions_marker

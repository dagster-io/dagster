import boto3
import uuid
from dagster_externals.aws import S3NotificationWriter

def test_integration_test_that_will_only_work_locally():
    bucket = "dagster-externals-test-lksdjflksjdlfkjs"
    region = "us-east-2"
    run_id = str(uuid.uuid4())
    step_key = "some_step"
    # create_bucket(bucket, region)
    # next_file = str(uuid.uuid1(0, 0)) + datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
    deployment_name = "some_deployment"

    # structured_event_log_path = f"dagster/{deployment_name}/structured_event_logs/{run_id}/{step_key}/{next_file}.json"
    key_for_step = f"dagster/{deployment_name}/runs/{run_id}/{step_key}/structured_event_logs"
    s3_client = boto3.client("s3", region_name=region)


def test_s3_notification_writer():
    pass
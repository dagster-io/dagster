import boto3
import uuid
from dagster_externals.aws import S3NotificationWriter
import json

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

    prev_key = None

    def read_loop(s3_client) -> None:
        page_size = 2
        prev_key = None
        while True:

            list_obj_params = dict(Bucket=bucket, Prefix=key_for_step, MaxKeys=page_size)
            if prev_key:
                list_obj_params['StartAfter'] = prev_key
            results = s3_client.list_objects_v2(**list_obj_params)

            contents = results['Contents']
            for entry in contents:
                key = entry['Key']
                get_obj_response = s3_client.get_object(Bucket=bucket, Key=key)
                muh_bytes = get_obj_response['Body'].read()
                muh_string = muh_bytes.decode()
                jsonlines = muh_string.split("\n")
                for jsonline in jsonlines:
                    if jsonline:
                        muh_object = json.loads(jsonline)
                        if muh_object['method'] == 'complete':
                            return

                prev_key = key

    read_loop(s3_client)

def test_s3_notification_writer():
    pass
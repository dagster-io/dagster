import uuid

import boto3
from dagster_externals._protocol import Notification
from dagster_externals.aws import S3NotificationReader, S3NotificationWriter


def not_in_bk_test_integration_test_that_will_only_work_locally():
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

    writer = S3NotificationWriter(bucket, key_for_step, s3_client)

    for i in range(0, 2):
        writer.write_notification(
            Notification(
                method="report_asset_metadata",
                params={"asset_key": "kajsldkfjasd", "label": "label1", "value": "value1"},
            )
        )
        writer.write_notification(
            Notification(
                method="report_asset_metadata",
                params={"asset_key": "kajsldkfjasd", "label": "label2", "value": "value2"},
            )
        )
        writer.write_notification(
            Notification(
                method="report_asset_metadata",
                params={"asset_key": "kajsldkfjasd", "label": "label3", "value": "value3"},
            )
        )

    writer.write_notification(
        Notification(
            method="complete",
            params={"asset_key": "kajsldkfjasd"},
        )
    )

    writer.flush()

    def read_loop(s3_client) -> None:
        page_size = 2
        reader = S3NotificationReader(s3_client, bucket, key_for_step, page_size)
        while True:
            page = reader.get_next_page()
            for notif in page.notifications:
                if notif['method'] == 'complete':
                    return

    read_loop(s3_client)

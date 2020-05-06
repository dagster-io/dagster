import io
import os
import pickle
import sys

import boto3
from dagster_aws.s3.file_manager import S3FileHandle, S3FileManager

from dagster.core.execution.plan.external_step import PICKLED_EVENTS_FILE_NAME, run_step_from_ref


def main(step_run_ref_bucket, s3_dir_key):
    session = boto3.client('s3')
    file_manager = S3FileManager(session, step_run_ref_bucket, '')
    file_handle = S3FileHandle(step_run_ref_bucket, s3_dir_key)
    step_run_ref_data = file_manager.read_data(file_handle)

    step_run_ref = pickle.loads(step_run_ref_data)

    events = list(run_step_from_ref(step_run_ref))
    file_obj = io.BytesIO(pickle.dumps(events))
    events_key = os.path.dirname(s3_dir_key) + '/' + PICKLED_EVENTS_FILE_NAME
    session.put_object(Body=file_obj, Bucket=step_run_ref_bucket, Key=events_key)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

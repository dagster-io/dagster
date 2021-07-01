#!/usr/bin/env python

import os
import subprocess
import sys

from google.cloud import storage

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


def deploy():
    bucket_name = os.getenv("GCP_DEPLOY_BUCKET")

    if not bucket_name:
        raise Exception(
            "bucket not provided; did you forget to export GCP_DEPLOY_BUCKET in your environment?"
        )
    # pylint: disable=unexpected-keyword-arg
    git_commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SCRIPT_PATH).strip()

    if sys.version_info.major >= 3:
        git_commit_hash = git_commit_hash.decode()

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    destination_blob_key = "dagster/scala_modules/events-assembly-{git_commit_hash}.jar".format(
        git_commit_hash=git_commit_hash
    )

    pwd = os.path.dirname(os.path.realpath(__file__))
    jar_path = os.path.join(
        pwd, "..", "events/target/scala-2.11/events-assembly-0.1.0-SNAPSHOT.jar"
    )

    blob = bucket.blob(destination_blob_key)

    blob.upload_from_filename(jar_path)

    print("File {} uploaded to gs://{}/{}.".format(jar_path, bucket_name, destination_blob_key))


if __name__ == "__main__":
    deploy()

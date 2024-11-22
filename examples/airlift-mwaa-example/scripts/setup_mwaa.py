"""This script uploads DAG files and requirements.txt to an S3 bucket in a directory
matching the name of the specified MWAA environment. It then attempts to update
the MWAA environment with the new S3 location. If the environment doesn't exist,
it provides instructions for creating one.

The script prompts for user confirmation before deleting any existing contents
in the target S3 directory, then uploads the new files, ensuring a clean deployment.
"""

import os
from typing import List

import boto3
import click
from botocore.exceptions import ClientError


def get_s3_objects(s3_client: boto3.client, bucket: str, prefix: str) -> list[dict]:  # pyright: ignore (reportGeneralTypeIssues)
    """Get list of objects in the S3 bucket with the given prefix."""
    try:
        objects = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return objects.get("Contents", [])
    except ClientError as e:
        click.echo(f"Error listing objects in s3://{bucket}/{prefix}: {e}", err=True)
        return []


def delete_s3_prefix(s3_client: boto3.client, bucket: str, prefix: str) -> None:  # pyright: ignore (reportGeneralTypeIssues)
    """Delete all objects in the S3 bucket with the given prefix."""
    objects_to_delete = get_s3_objects(s3_client, bucket, prefix)
    if objects_to_delete:
        try:
            delete_keys = {"Objects": [{"Key": obj["Key"]} for obj in objects_to_delete]}
            s3_client.delete_objects(Bucket=bucket, Delete=delete_keys)
            click.echo(f"Deleted existing contents in s3://{bucket}/{prefix}")
        except ClientError as e:
            click.echo(f"Error deleting objects in s3://{bucket}/{prefix}: {e}", err=True)
    else:
        click.echo(f"No existing contents found in s3://{bucket}/{prefix}")


def upload_file(s3_client: boto3.client, file_path: str, bucket: str, object_name: str) -> bool:  # pyright: ignore (reportGeneralTypeIssues)
    """Upload a file to an S3 bucket."""
    try:
        s3_client.upload_file(file_path, bucket, object_name)
    except ClientError as e:
        click.echo(f"Error uploading {file_path}: {e}", err=True)
        return False
    return True


def update_mwaa_environment(
    mwaa_client: boto3.client,  # pyright: ignore (reportGeneralTypeIssues)
    environment_name: str,
    s3_bucket: str,
    s3_key: str,
) -> None:
    """Update MWAA environment or provide instructions if it doesn't exist."""
    try:
        mwaa_client.update_environment(
            Name=environment_name,
            SourceBucketArn=f"arn:aws:s3:::{s3_bucket}",
            DagS3Path=s3_key,
            RequirementsS3Path=f"{s3_key}/requirements.txt",
        )
        click.echo(f"MWAA environment {environment_name} updated successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":  # pyright: ignore (reportTypedDictNotRequiredAccess)
            click.echo(f"MWAA environment {environment_name} not found.")
            click.echo("To create a new environment, use the following information:")
            click.echo(f"S3 bucket: {s3_bucket}")
            click.echo(f"DAGs folder: s3://{s3_bucket}/{s3_key}")
            click.echo(f"Requirements file: s3://{s3_bucket}/{s3_key}/requirements.txt")
        else:
            click.echo(f"Error updating MWAA environment: {e}", err=True)


@click.command()
@click.option("--region", required=True, help="AWS region")
@click.option("--profile", default="default", help="AWS profile name")
@click.option("--bucket", required=True, help="S3 bucket name")
@click.option("--env-name", required=True, help="MWAA environment name")
@click.option("--dags-folder", default="dags", help="Path to the DAGs folder")
def upload_dags(region: str, profile: str, bucket: str, env_name: str, dags_folder: str) -> None:
    """Upload DAG files to S3 and update MWAA environment."""
    # Set up AWS session and clients
    session = boto3.Session(profile_name=profile, region_name=region)
    s3_client = session.client("s3")
    mwaa_client = session.client("mwaa")

    # Create S3 key for the environment
    s3_key = f"mwaa-environments/{env_name}"

    # Check for existing contents and prompt for deletion
    existing_objects = get_s3_objects(s3_client, bucket, s3_key)
    if existing_objects:
        click.echo(f"Found existing contents in s3://{bucket}/{s3_key}")
        if click.confirm("Do you want to delete existing contents?"):
            delete_s3_prefix(s3_client, bucket, s3_key)
        else:
            click.echo("Proceeding without deleting existing contents.")
    else:
        click.echo(f"No existing contents found in s3://{bucket}/{s3_key}")

    # Upload DAG files
    for root, _, files in os.walk(dags_folder):
        for file in files:
            if file.endswith(".py") or file == "requirements.txt":
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, dags_folder)
                s3_object_name = f"{s3_key}/{relative_path}"

                if upload_file(s3_client, local_path, bucket, s3_object_name):
                    click.echo(f"Uploaded {local_path} to s3://{bucket}/{s3_object_name}")
                else:
                    click.echo(f"Failed to upload {local_path}", err=True)

    # Update MWAA environment
    update_mwaa_environment(mwaa_client, env_name, bucket, s3_key)


if __name__ == "__main__":
    upload_dags()

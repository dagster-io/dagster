# pylint: disable=no-value-for-parameter
import json
import os
import re
import shutil

import boto3
import click
from dagster import file_relative_path

CONTENT_DIR = file_relative_path(__file__, "./content")
IMAGE_DIR = file_relative_path(__file__, "next/public/images")
VERSIONED_DIR = file_relative_path(__file__, "next/.versioned_content")

TMP_OUTPUT_PATH = "/tmp/docs_versioned_output/"
CONTENT_OUTPUT_DIR = os.path.join(TMP_OUTPUT_PATH, "versioned_content")
IMAGE_OUTPUT_DIR = os.path.join(TMP_OUTPUT_PATH, "versioned_images")

s3_client = boto3.resource("s3")
bucket = s3_client.Bucket("dagster-docs-versioned-content")


def read_json(filename):
    with open(filename) as f:
        data = json.load(f)
        return data


def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, sort_keys=True, indent=2)


def remove_files_from_s3(s3_dir):
    # Remove all files in `prefix/version/` folder
    click.echo(f"Removing files from S3 path: {s3_dir}")
    bucket.objects.filter(Prefix=f"{s3_dir}/").delete()


def upload_files_to_s3(source_dir):
    # Upload all files from source_dir to its cooresponding s3 path: /tmp/* to s3:bucket/*
    for root, _, files in os.walk(source_dir):
        # Upload each file using os.walk
        for filename in files:
            source_path = os.path.join(root, filename)
            s3_path = os.path.join(re.sub(f"^{TMP_OUTPUT_PATH}", "", root), filename)
            click.echo(f"Uploading file {source_path} to S3 path: {s3_path}")
            bucket.upload_file(source_path, s3_path)


@click.command()
@click.option("--version", required=True, help="Version to release")
@click.option("--overwrite", is_flag=True, help="Overwrite an existing version")
def main(version, overwrite):
    # Check if version exists
    versions = read_json(os.path.join(VERSIONED_DIR, "_versions.json"))
    if version in versions:
        if not overwrite:
            raise click.ClickException(
                "Error: Version {} already exists. To overwrite this version, "
                "use the --overwrite option.".format(version)
            )

        value = click.prompt(
            "Are you sure you want to overwrite version {}? This is a dangerous action, make sure "
            "that the docs haven't drifted from the version that you are attempting to overwrite. "
            "It is okay if there is an error in old docs, it can be fixed in future releases.\n\n"
            "Enter the version number to continue "
        )

        if value == version:
            remove_files_from_s3(os.path.join("versioned_content", version))
            click.echo(f'✅ successfully removed versioned content for version "{version}"')
            remove_files_from_s3(os.path.join("versioned_images", version))
            click.echo(f'✅ successfully removed versioned images for version "{version}"')
            versions.remove(version)
        else:
            raise click.ClickException("Incorrect version number: {}".format(value))

    # clean up old files in tmp dir in case this is a retry
    if os.path.isdir(TMP_OUTPUT_PATH):
        shutil.rmtree(TMP_OUTPUT_PATH)

    # Create versioned content locally
    version_content_directory = os.path.join(CONTENT_OUTPUT_DIR, version)
    shutil.copytree(CONTENT_DIR, version_content_directory)
    click.echo(f"✅ successfully wrote versioned content for to path: {version_content_directory}")
    # Upload versioned content to s3
    upload_files_to_s3(version_content_directory)
    click.echo(f'✅ successfully uploaded versioned content for version "{version}"')

    # Create versioned images locally
    version_image_directory = os.path.join(IMAGE_OUTPUT_DIR, version)
    shutil.copytree(IMAGE_DIR, version_image_directory)
    click.echo(f"✅ successfully wrote versioned images for to path: {version_image_directory}")
    # Upload versioned images to s3
    upload_files_to_s3(version_image_directory)
    click.echo(f'✅ successfully uploaded versioned images for version "{version}"')

    # Update versions file
    versions.append(version)
    write_json(os.path.join(VERSIONED_DIR, "_versions.json"), versions)
    click.echo(f'✅ successfully updated {os.path.join(VERSIONED_DIR, "_versions.json")}')

    # Create master navigation file
    # TODO yuhan: move versioned navigation to s3
    versioned_navigation = read_json(os.path.join(VERSIONED_DIR, "_versioned_navigation.json"))
    for (root, _, files) in os.walk(CONTENT_OUTPUT_DIR):
        for filename in files:
            if filename == "_navigation.json":
                curr_version = root.split("/")[-1]
                data = read_json(os.path.join(root, filename))
                versioned_navigation[curr_version] = data

    write_json(
        os.path.join(VERSIONED_DIR, "_versioned_navigation.json"),
        versioned_navigation,
    )
    click.echo(
        f'✅ successfully updated {os.path.join(VERSIONED_DIR, "_versioned_navigation.json")}'
    )


if __name__ == "__main__":
    main()

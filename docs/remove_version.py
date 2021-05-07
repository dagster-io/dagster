# pylint: disable=no-value-for-parameter
# pylint: disable=print-call

import json
import os
import shutil

import click
from dagster import file_relative_path

VERSIONED_CONTENT_DIR = file_relative_path(__file__, "next/.versioned_content")
VERSIONED_IMAGE_DIR = file_relative_path(__file__, "next/public/.versioned_images/")
CONTENT_DIR = file_relative_path(__file__, "./content")
IMAGE_DIR = file_relative_path(__file__, "next/public/images")


def read_json(filename):
    with open(filename) as f:
        data = json.load(f)
        return data


def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, sort_keys=True)


@click.command()
@click.option("--version", required=True, help="Version to remove")
def main(version):
    # NOTE: this is primarily use for removing rc versions created by the pre-release process
    # Caveat: this script doesn't update the "latest" version, meaning when the removed version was
    # the latest version, the latest versioned content will be out-of-sync after the removal.

    curr_content_directory = os.path.join(VERSIONED_CONTENT_DIR, version)
    curr_image_directory = os.path.join(VERSIONED_IMAGE_DIR, version)
    master_navigation_path = os.path.join(VERSIONED_CONTENT_DIR, "_versioned_navigation.json")

    # Remove content dir of the given version
    if os.path.isdir(curr_content_directory):
        shutil.rmtree(curr_content_directory)
        print(f'Successfully removed "{curr_content_directory}"')
    else:
        print(f'No "{curr_content_directory}" found. Skipping.')

    # Remove image dir of the given version
    if os.path.isdir(curr_image_directory):
        shutil.rmtree(curr_image_directory)
        print(f'Successfully removed "{curr_image_directory}"')
    else:
        print(f'No "{curr_image_directory}" found. Skipping.')

    # Remove the navigation entry of the given version in the master navigation file
    versioned_navigation = read_json(master_navigation_path)
    if version in versioned_navigation:
        del versioned_navigation[version]
        write_json(master_navigation_path, versioned_navigation)
        print(f'Successfully removed "{version}" from "{master_navigation_path}"')
    else:
        print(f'No "{version} in "{master_navigation_path}". Skipping.')

    # Remove the given version from the versions file
    versions_path = os.path.join(VERSIONED_CONTENT_DIR, "_versions.json")
    versions = read_json(versions_path)
    if version in versions:
        versions.remove(version)
        write_json(versions_path, versions)
        print(f'Successfully removed "{version}" from "{versions_path}"')
    else:
        print(f'No "{version} in "{versions_path}". Skipping.')


if __name__ == "__main__":
    main()

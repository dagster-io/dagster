# pylint: disable=no-value-for-parameter
# pylint: disable=print-call

import json
import os

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
        json.dump(data, f, sort_keys=True, indent=2)


@click.command()
@click.option("--version", required=True, help="Version to remove")
def main(version):
    # This is primarily use for removing rc versions created by the pre-release process
    master_navigation_path = os.path.join(VERSIONED_CONTENT_DIR, "_versioned_navigation.json")

    # Remove the navigation entry of the given version in the master navigation file
    versioned_navigation = read_json(master_navigation_path)
    if version in versioned_navigation:
        del versioned_navigation[version]
        write_json(master_navigation_path, versioned_navigation)
        click.echo(f'Successfully removed "{version}" from "{master_navigation_path}"')
    else:
        click.echo(f'No "{version} in "{master_navigation_path}". Skipping.')

    # Remove the given version from the versions file
    versions_path = os.path.join(VERSIONED_CONTENT_DIR, "_versions.json")
    versions = read_json(versions_path)
    if version in versions:
        versions.remove(version)
        write_json(versions_path, versions)
        click.echo(f'Successfully removed "{version}" from "{versions_path}"')
    else:
        click.echo(f'No "{version} in "{versions_path}". Skipping.')


if __name__ == "__main__":
    main()

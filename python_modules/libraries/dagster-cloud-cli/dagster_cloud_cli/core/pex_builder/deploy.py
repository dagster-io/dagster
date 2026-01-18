# end-to-end workflow for rebuilding and publishing code locations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional

import click
from packaging import version

from dagster_cloud_cli import gql, ui
from dagster_cloud_cli.core.pex_builder import (
    deps,
    github_context,
    parse_workspace,
    pex_registry,
    source,
    util,
)


@dataclass
class LocationBuild:
    """Inputs and outputs for each code location."""

    location: parse_workspace.Location

    # local dependencies are packaged with the source.pex along with the main code location
    local_packages: deps.LocalPackages

    # all other dependencies are packaged in the deps.pex
    deps_requirements: deps.DepsRequirements

    # One of deps_pex_path or published_deps_pex should be set
    deps_pex_path: Optional[str] = None  # locally build deps.pex
    published_deps_pex: Optional[str] = None  # already published deps.pex
    # dagster_version should be always set for both cases, pre published and locally built deps
    dagster_version: Optional[str] = None
    source_pex_path: Optional[str] = None
    pex_tag: Optional[str] = None  # composite tag used to identify the set of pex files

    code_location_update_error: Optional[Exception] = None


@dataclass
class DepsCacheTags:
    deps_cache_from_tag: Optional[str]
    deps_cache_to_tag: Optional[str]


def build_locations(
    dagster_cloud_url: str,
    dagster_cloud_api_token: str,
    locations: list[parse_workspace.Location],
    output_directory: str,
    upload_pex: bool,
    deps_cache_tags: DepsCacheTags,
    python_version: version.Version,
    build_method: deps.BuildMethod = deps.BuildMethod.DOCKER_FALLBACK,
) -> list[LocationBuild]:
    location_builds = []
    for location in locations:
        local_packages, deps_requirements = deps.get_deps_requirements(
            location.directory,
            python_version=python_version,
        )
        location_builds.append(
            LocationBuild(
                location=location,
                local_packages=local_packages,
                deps_requirements=deps_requirements,
            )
        )

    # dedup requirements so each is only built once
    builds_for_requirements_hash: dict[str, list[LocationBuild]] = {}
    for location_build in location_builds:
        requirements_hash = location_build.deps_requirements.hash
        builds_for_requirements_hash.setdefault(requirements_hash, []).append(location_build)

    # build each deps pex once and assign to all related builds
    for requirements_hash in builds_for_requirements_hash:
        builds = builds_for_requirements_hash[requirements_hash]
        deps_requirements = builds[0].deps_requirements

        # if a --deps-cache-from is specified, don't build deps.pex files if it is already published
        if upload_pex and deps_cache_tags.deps_cache_from_tag:
            published_deps_pex_info = pex_registry.get_cached_deps_details(
                dagster_cloud_url,
                dagster_cloud_api_token,
                deps_requirements.hash,
                deps_cache_tags.deps_cache_from_tag,
            )
        else:
            published_deps_pex_info = None

        if published_deps_pex_info:
            published_deps_pex = published_deps_pex_info["deps_pex_name"]
            ui.print(
                f"Found published deps.pex {published_deps_pex} for requirements_hash {deps_requirements.hash}, cache_tag {deps_cache_tags.deps_cache_from_tag}, "
                "skipping rebuild.",
            )

            for location_build in builds:
                location_build.published_deps_pex = published_deps_pex
                location_build.dagster_version = published_deps_pex_info["dagster_version"]
        else:
            ui.print(
                f"No published deps.pex found for requirements_hash {deps_requirements.hash}, cache_tag {deps_cache_tags.deps_cache_from_tag}, will rebuild.",
            )
            try:
                deps_pex_path, dagster_version = deps.build_deps_from_requirements(
                    deps_requirements,
                    output_directory,
                    build_method=build_method,
                )
            except deps.DepsBuildFailure as err:
                logging.error("Failed to build dependencies: %s", err.stderr)
                sys.exit(1)
            for location_build in builds:
                location_build.deps_pex_path = deps_pex_path
                location_build.dagster_version = dagster_version

    # build each source once
    for location_build in location_builds:
        location_build.source_pex_path = source.build_source_pex(
            location_build.location.directory,
            location_build.local_packages.local_package_paths,
            output_directory,
            python_version,
        )

    # compute pex tags
    for location_build in location_builds:
        deps_pex = (
            location_build.deps_pex_path
            if location_build.deps_pex_path
            else location_build.published_deps_pex
        )
        if not deps_pex or not location_build.source_pex_path:
            raise ValueError("No deps.pex or source.pex")

        location_build.pex_tag = util.build_pex_tag([deps_pex, location_build.source_pex_path])
    return location_builds


def get_user_specified_base_image_for(
    dagster_cloud_url: str, dagster_cloud_api_token: str, location_build: LocationBuild
) -> Optional[str]:
    # Full path to base image is supplied
    base_image = os.getenv("SERVERLESS_BASE_IMAGE")
    if base_image:
        return base_image

    # Tag suffix for base image is supplied - uses custom uploaded image
    base_image_tag = os.getenv("SERVERLESS_BASE_IMAGE_TAG")
    if base_image_tag:
        # Point to user's registry info with this tag suffix
        with gql.graphql_client_from_url(dagster_cloud_url, dagster_cloud_api_token) as client:
            registry_info = gql.get_ecr_info(client)
            return f"{registry_info['registry_url']}:{base_image_tag}"

    return None


def notify(deployment_name: Optional[str], location_name: str, action: str):
    if github_event:
        github_context.update_pr_comment(
            github_event,
            action=action,
            deployment_name=deployment_name,
            location_name=location_name,
        )


github_event: Optional[github_context.GithubEvent] = None


def load_github_event(project_dir):
    global github_event  # noqa: PLW0603
    github_event = github_context.get_github_event(project_dir)


@click.command()
@click.argument("dagster_cloud_file", type=click.Path(exists=True))
@click.argument("build_output_dir", type=click.Path(exists=False))
@click.option(
    "--upload-pex",
    is_flag=True,
    show_default=True,
    default=False,
    help="Upload PEX files to registry.",
)
@click.option(
    "--deps-cache-from",
    type=str,
    required=False,
    help=(
        "Try to reuse a pre-existing deps pex file. A deps pex file is reused if it was "
        "built with a --deps-cache-to value that matches this flag value, AND the requirements.txt "
        "and setup.py were identical."
    ),
)
@click.option(
    "--deps-cache-to",
    type=str,
    required=False,
    help=(
        "Allow reusing the generated deps pex and associate with the given tag. "
        "See --deps-cache-from for how to reuse deps pex files."
    ),
)
@click.option(
    "--update-code-location",
    is_flag=True,
    show_default=True,
    default=False,
    help="Update code location to use new PEX files.",
)
@click.option(
    "--code-location-details",
    callback=util.parse_kv,
    help=(
        "Syntax: --code-location-details deployment=NAME,commit_hash=HASH. "
        "When not provided, details are inferred from the github action environment."
    ),
)
@util.python_version_option()
@click.option(
    "--build-sdists/--no-build-sdists",
    is_flag=True,
    default=False,
    help="Whether to build source only Python dependencies (sdists).",
)
def cli(
    dagster_cloud_file,
    build_output_dir,
    upload_pex,
    deps_cache_to,
    deps_cache_from,
    update_code_location,
    code_location_details,
    python_version,
    build_sdists,
):
    logging.error(
        "This entrypoint is obsolete. Please use `dagster-cloud serverless"
        " deploy-python-executable`."
    )
    sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli()

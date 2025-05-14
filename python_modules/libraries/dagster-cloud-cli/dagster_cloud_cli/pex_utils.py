# Handles python executable (pex) specific flags and wraps pex_builder

import os
import tempfile
from typing import Any

from typer import Option

from dagster_cloud_cli import ui
from dagster_cloud_cli.core import pex_builder
from dagster_cloud_cli.core.pex_builder.deps import BuildMethod
from dagster_cloud_cli.utils import DEFAULT_PYTHON_VERSION, get_file_size

DEPLOY_PEX_OPTIONS = {
    "python_version": (
        str,
        Option(
            DEFAULT_PYTHON_VERSION,
            "--python-version",
            help="Target Python version specified as 'major.minor'.",
        ),
    ),
    "deps_cache_from": (
        str,
        Option(
            None,
            "--deps-cache-from",
            help=(
                "Reuse cached dependencies for this tag, "
                "if the dependency names match the cached names."
            ),
        ),
    ),
    "deps_cache_to": (
        str,
        Option(
            None,
            "--deps-cache-to",
            help=(
                "Cache dependencies and annotate with this tag. "
                "Use this tag in --deps-cache-from to reuse dependencies."
            ),
            hidden=True,
        ),
    ),
    "base_image_tag": (
        str,
        Option(
            None,
            "--base-image-tag",
            help="Tag that selects a base image uploaded using upload-base-image",
        ),
    ),
    "build_method": (
        BuildMethod,
        Option("docker-fallback", help="Environment used to build the dependencies."),
    ),
}


def build_upload_pex(
    url: str,
    api_token: str,
    location: pex_builder.parse_workspace.Location,
    build_method: BuildMethod,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    # build and upload the python executable, return the modified kwargs with pex_tag and image
    kwargs = kwargs.copy()

    if kwargs.get("base_image_tag"):
        if kwargs.get("image"):
            raise ui.error("Only one of --base-image-tag or --image can be specified.")
        os.environ["SERVERLESS_BASE_IMAGE_TAG"] = kwargs.pop("base_image_tag")

    python_version = pex_builder.util.parse_python_version(
        kwargs.setdefault("python_version", DEFAULT_PYTHON_VERSION)
    )
    ui.print(
        ui.blue(
            f"Building Python executable for {location.name} from directory {location.directory} "
            f"and Python {python_version}."
        )
    )
    deps_cache_tags = pex_builder.deploy.DepsCacheTags(
        kwargs.pop("deps_cache_from", None), kwargs.pop("deps_cache_to", None)
    )
    with tempfile.TemporaryDirectory() as temp_folder:
        builds = pex_builder.deploy.build_locations(
            url,
            api_token,
            [location],
            temp_folder,
            upload_pex=True,
            deps_cache_tags=deps_cache_tags,
            python_version=python_version,
            build_method=build_method,
        )

        build = builds[0]
        kwargs["pex_tag"] = build.pex_tag
        image = kwargs.get("image")
        if not image:
            image = pex_builder.deploy.get_user_specified_base_image_for(url, api_token, build)
            if image:
                kwargs["image"] = image
        if image:
            ui.print(f"Will deploy {build.location.name} on image: {image}")
            del kwargs["python_version"]
        else:
            ui.print(
                f"Will deploy {build.location.name} on a standard base image for Python"
                f" {python_version}"
            )

        paths = [
            filepath
            for filepath in [
                build.source_pex_path,
                build.deps_pex_path,
            ]
            if filepath is not None
        ]
        if not paths:
            raise ui.error("No built files for {build.location.name}.")
        print_built_pex_details(build)
        ui.print(f"Uploading Python executable for {build.location.name}.")
        pex_builder.pex_registry.upload_files(url, api_token, paths)

        # if a --deps-cache-to cache_tag is specified, set or update the cached deps details
        if deps_cache_tags.deps_cache_to_tag:
            # could be either a newly built pex or an published pex name copied from another tag
            deps_pex_name = (
                os.path.basename(build.deps_pex_path)
                if build.deps_pex_path
                else build.published_deps_pex
            )
            if not deps_pex_name:
                raise ui.error(
                    "Failed to build or find the Python executable dependencies (deps.pex)."
                )
            if not build.dagster_version:
                raise ui.error("Dagster not found in project's dependencies.")

            pex_builder.pex_registry.set_cached_deps_details(
                url,
                api_token,
                build.deps_requirements.hash,
                deps_cache_tags.deps_cache_to_tag,
                deps_pex_name,
                dagster_version=build.dagster_version,
            )
            ui.print(
                f"Updated cached deps.pex for requirements_hash {build.deps_requirements.hash}, cache_tag {deps_cache_tags.deps_cache_from_tag}.",
            )

    return kwargs


def print_built_pex_details(location_build: pex_builder.deploy.LocationBuild):
    ui.print(
        f"Built {location_build.source_pex_path} ({get_file_size(location_build.source_pex_path)})"
        " from:"
    )
    ui.print(f" - {location_build.location.directory}")
    for local_path in location_build.local_packages.local_package_paths:
        ui.print(f" - {local_path}")

    if location_build.deps_pex_path:
        ui.print(
            f"Built {location_build.deps_pex_path} ({get_file_size(location_build.deps_pex_path)})"
            f" with Dagster {location_build.dagster_version}"
        )
        ui.print("Included dependencies:")
        for line in sorted(
            location_build.deps_requirements.requirements_txt.splitlines(keepends=False)
        ):
            print(f" - {line}")  # noqa: T201
    elif location_build.published_deps_pex:
        ui.print(f"Reusing cached dependencies: {location_build.published_deps_pex}")

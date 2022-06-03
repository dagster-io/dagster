import contextlib
import os
from typing import Callable, Dict, Iterator, List, NamedTuple, Optional

import yaml

import dagster._check as check

from ..git import git_repo_root
from .ecr import ecr_image, get_aws_account_id, get_aws_region
from .utils import (
    execute_docker_build,
    execute_docker_push,
    execute_docker_tag,
    python_version_image_tag,
)

# Default repository prefix used for local images
DEFAULT_LOCAL_PREFIX = "dagster"

# Location of the template assets used here
IMAGES_PATH = os.path.join(os.path.dirname(__file__), "images")


@contextlib.contextmanager
def do_nothing(_cwd: str) -> Iterator[None]:
    yield


def default_images_path():
    return os.path.join(
        git_repo_root(),
        "python_modules",
        "automation",
        "automation",
        "docker",
        "images",
    )


class DagsterDockerImage(
    NamedTuple(
        "_DagsterDockerImage",
        [
            ("image", str),
            ("images_path", str),
            ("build_cm", Callable),
        ],
    )
):
    """Represents a Dagster image.

    Properties:
        image (str): Name of the image
        images_path (Optional(str)): The base folder for the images.
        build_cm (function): function that is a context manager for build (e.g. for populating a
            build cache)
    """

    def __new__(
        cls,
        image: str,
        images_path: Optional[str] = None,
        build_cm: Callable = do_nothing,
    ):
        return super(DagsterDockerImage, cls).__new__(
            cls,
            check.str_param(image, "image"),
            check.opt_str_param(
                images_path,
                "images_path",
                default_images_path(),
            ),
            check.callable_param(build_cm, "build_cm"),
        )

    @property
    def path(self) -> str:
        return os.path.join(self.images_path, self.image)

    @property
    def python_versions(self) -> List[str]:
        """List of Python versions supported for this image."""
        with open(os.path.join(self.path, "versions.yaml"), "r", encoding="utf8") as f:
            versions = yaml.safe_load(f.read())
        return list(versions.keys())

    def _get_last_updated_for_python_version(self, python_version: str) -> str:
        """Retrieve the last_updated timestamp for a particular python_version of this image."""
        check.str_param(python_version, "python_version")
        with open(os.path.join(self.path, "last_updated.yaml"), "r", encoding="utf8") as f:
            last_updated = yaml.safe_load(f.read())
            return last_updated[python_version]

    def _set_last_updated_for_python_version(self, timestamp: str, python_version: str) -> None:
        """Update the last_updated timestamp for a particular python_version of this image."""
        check.str_param(timestamp, "timestamp")
        check.str_param(python_version, "python_version")

        last_updated = {}

        last_updated_path = os.path.join(self.path, "last_updated.yaml")
        if os.path.exists(last_updated_path):
            with open(last_updated_path, "r", encoding="utf8") as f:
                last_updated = yaml.safe_load(f.read())

        last_updated[python_version] = timestamp

        with open(os.path.join(self.path, "last_updated.yaml"), "w", encoding="utf8") as f:
            yaml.dump(last_updated, f, default_flow_style=False)

    def local_image(self, python_version: str) -> str:
        """Generates the local image name, like: "dagster/foo:some-tag" """
        check.str_param(python_version, "python_version")

        last_updated = self._get_last_updated_for_python_version(python_version)
        tag = python_version_image_tag(python_version, last_updated)
        return "{}/{}:{}".format(DEFAULT_LOCAL_PREFIX, self.image, tag)

    def aws_image(
        self, python_version: Optional[str] = None, custom_tag: Optional[str] = None
    ) -> str:
        """Generates the AWS ECR image name, like:
        "1234567890.dkr.ecr.us-west-1.amazonaws.com/foo:some-tag"
        """
        check.invariant(not (python_version and custom_tag))
        check.opt_str_param(python_version, "python_version")
        check.opt_str_param(custom_tag, "custom_tag")

        tag: Optional[str]
        if python_version:
            last_updated = self._get_last_updated_for_python_version(python_version)
            tag = python_version_image_tag(python_version, last_updated)
        else:
            tag = custom_tag

        return ecr_image(
            self.image,
            tag,
            aws_account_id=get_aws_account_id(),
            aws_region=get_aws_region(),
        )

    def _get_docker_args(self, dagster_version: str, python_version: str) -> Dict[str, str]:
        """Retrieve Docker arguments from this image's versions.yaml, and update with latest Dagster
        version.

        Also, we allow references in the image versions.yaml to another Dagster image to use as a
        base image. If defined, set the BASE_IMAGE Docker arg from the full name of the parent
        image.
        """
        with open(os.path.join(self.path, "versions.yaml"), "r", encoding="utf8") as f:
            versions = yaml.safe_load(f.read())
            image_info = versions.get(python_version, {})

        docker_args = image_info.get("docker_args", {})

        if "base_image" in image_info:
            check.invariant(
                "BASE_IMAGE" not in docker_args, "Cannot override an existing BASE_IMAGE"
            )

            base_image = DagsterDockerImage(
                image_info["base_image"]["name"], images_path=self.images_path
            )
            source = image_info["base_image"]["source"]

            if source == "aws":
                docker_args["BASE_IMAGE"] = base_image.aws_image(python_version)
            elif source == "local":
                docker_args["BASE_IMAGE"] = base_image.local_image(python_version)
            else:
                raise Exception("Unrecognized source {}".format(source))

        # Set Dagster version
        docker_args["DAGSTER_VERSION"] = dagster_version
        return docker_args

    def build(
        self, timestamp, dagster_version: str, python_version: str, platform: Optional[str] = None
    ) -> None:
        check.str_param(timestamp, "timestamp")
        check.str_param(python_version, "python_version")
        check.opt_str_param(platform, "platform")
        with self.build_cm(self.path):
            self._set_last_updated_for_python_version(timestamp, python_version)

            execute_docker_build(
                self.local_image(python_version),
                docker_args=self._get_docker_args(dagster_version, python_version),
                cwd=self.path,
                platform=platform,
            )

    def push(self, python_version: str, custom_tag: Optional[str] = None) -> None:
        """Push this image to ECR."""

        if custom_tag:
            execute_docker_tag(
                self.local_image(python_version),
                self.aws_image(python_version=None, custom_tag=custom_tag),
            )
            execute_docker_push(self.aws_image(python_version=None, custom_tag=custom_tag))
        else:
            execute_docker_tag(self.local_image(python_version), self.aws_image(python_version))
            execute_docker_push(self.aws_image(python_version))

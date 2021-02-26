import contextlib
import os
from collections import namedtuple

import yaml
from dagster import __version__ as current_dagster_version
from dagster import check

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
def do_nothing(_cwd):
    yield


class DagsterDockerImage(namedtuple("_DagsterDockerImage", "image build_cm")):
    """Represents a Dagster image.

    Properties:
        image (str): Name of the image
        build_cm (function): function that is a context manager for build (e.g. for populating a
            build cache)
    """

    def __new__(cls, image, build_cm=do_nothing):
        return super(DagsterDockerImage, cls).__new__(
            cls,
            check.str_param(image, "image"),
            check.callable_param(build_cm, "build_cm"),
        )

    @property
    def python_versions(self):
        """List of Python versions supported for this image."""
        with open(os.path.join(self.path, "versions.yaml"), "r") as f:
            versions = yaml.safe_load(f.read())
        return list(versions.keys())

    @property
    def path(self):
        """Image Dockerfiles are located at docker/images/<IMAGE NAME>"""
        return os.path.join(os.path.dirname(__file__), "images", self.image)

    def _get_last_updated_for_python_version(self, python_version):
        """Retrieve the last_updated timestamp for a particular python_version of this image."""
        check.str_param(python_version, "python_version")
        with open(os.path.join(self.path, "last_updated.yaml"), "r") as f:
            last_updated = yaml.safe_load(f.read())
            return last_updated[python_version]

    def _set_last_updated_for_python_version(self, timestamp, python_version):
        """Update the last_updated timestamp for a particular python_version of this image."""
        check.str_param(timestamp, "timestamp")
        check.str_param(python_version, "python_version")

        last_updated = {}

        last_updated_path = os.path.join(self.path, "last_updated.yaml")
        if os.path.exists(last_updated_path):
            with open(last_updated_path, "r") as f:
                last_updated = yaml.safe_load(f.read())

        last_updated[python_version] = timestamp

        with open(os.path.join(self.path, "last_updated.yaml"), "w") as f:
            yaml.dump(last_updated, f, default_flow_style=False)

    def local_image(self, python_version):
        """Generates the local image name, like: "dagster/foo:some-tag" """
        check.str_param(python_version, "python_version")

        last_updated = self._get_last_updated_for_python_version(python_version)
        tag = python_version_image_tag(python_version, last_updated)
        return "{}/{}:{}".format(DEFAULT_LOCAL_PREFIX, self.image, tag)

    def aws_image(self, python_version=None, custom_tag=None):
        """Generates the AWS ECR image name, like:
        "1234567890.dkr.ecr.us-west-1.amazonaws.com/foo:some-tag"
        """
        check.invariant(not (python_version and custom_tag))
        check.opt_str_param(python_version, "python_version")
        check.opt_str_param(custom_tag, "custom_tag")

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

    def _get_docker_args(self, python_version):
        """Retrieve Docker arguments from this image's versions.yaml, and update with latest Dagster
        version.

        Also, we allow references in the image versions.yaml to another Dagster image to use as a
        base image. If defined, set the BASE_IMAGE Docker arg from the full name of the parent
        image.
        """
        with open(os.path.join(self.path, "versions.yaml"), "r") as f:
            versions = yaml.safe_load(f.read())
            image_info = versions.get(python_version, {})

        docker_args = image_info.get("docker_args", {})

        if "base_image" in image_info:
            check.invariant(
                "BASE_IMAGE" not in docker_args, "Cannot override an existing BASE_IMAGE"
            )

            base_image = DagsterDockerImage(image_info["base_image"]["name"])
            source = image_info["base_image"]["source"]

            if source == "aws":
                docker_args["BASE_IMAGE"] = base_image.aws_image(python_version)
            elif source == "local":
                docker_args["BASE_IMAGE"] = base_image.local_image(python_version)
            else:
                raise Exception("Unrecognized source {}".format(source))

        # Set Dagster version
        docker_args["DAGSTER_VERSION"] = current_dagster_version
        return docker_args

    def build(self, timestamp, dagster_version, python_version):
        check.str_param(timestamp, "timestamp")
        check.str_param(python_version, "python_version")
        check.invariant(
            dagster_version == current_dagster_version,
            desc="Current dagster version ({}) does not match provided arg ({})".format(
                current_dagster_version, dagster_version
            ),
        )
        with self.build_cm(self.path):
            self._set_last_updated_for_python_version(timestamp, python_version)

            execute_docker_build(
                self.local_image(python_version),
                docker_args=self._get_docker_args(python_version),
                cwd=self.path,
            )

    def push(self, python_version, custom_tag=None):
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

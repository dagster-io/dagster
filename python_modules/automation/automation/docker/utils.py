# pylint: disable=print-call
import subprocess
import sys
from datetime import datetime, timezone

from dagster import check


def execute_docker_build(image, docker_args=None, cwd=None):
    check.str_param(image, "image")
    docker_args = check.opt_dict_param(docker_args, "docker_args", key_type=str, value_type=str)

    print("Building image {}".format(image))

    args = ["docker", "build", "."]

    for arg, value in docker_args.items():
        args += ["--build-arg", "{arg}={value}".format(arg=arg, value=value)]

    args += ["-t", image]

    print(" ".join(args))

    retval = subprocess.call(args, stderr=sys.stderr, stdout=sys.stdout, cwd=cwd)
    check.invariant(retval == 0, "Process must exit successfully")


def execute_docker_push(image):
    check.str_param(image, "image")

    print("Pushing image {}".format(image))
    retval = subprocess.call(["docker", "push", image], stderr=sys.stderr, stdout=sys.stdout)
    check.invariant(retval == 0, "docker push must succeed")


def execute_docker_tag(local_image, remote_image):
    """Re-tag an existing image"""
    check.str_param(local_image, "local_image")
    check.str_param(remote_image, "remote_image")

    print("Tagging local image {} as remote image {}".format(local_image, remote_image))
    retval = subprocess.call(
        ["docker", "tag", local_image, remote_image], stderr=sys.stderr, stdout=sys.stdout
    )
    check.invariant(retval == 0, "docker tag must succeed")


def python_version_image_tag(python_version, image_version):
    """Dagster images are typically tagged as py<PYTHON VERSION>-<IMAGE VERSION>"""
    check.str_param(python_version, "python_version")
    check.str_param(image_version, "image_version")
    return "py{}-{}".format(python_version, image_version)


def current_time_str():
    """Should be UTC date string like 2020-07-11T035005"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")

import base64
import importlib.resources
import os
import subprocess
import sys
import uuid
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from typing import Optional

from dagster_cloud_cli import ui
from dagster_cloud_cli.utils import DEFAULT_PYTHON_VERSION


def verify_docker() -> None:
    if subprocess.call("docker -v", shell=True) != 0:
        raise ui.error("Docker must be installed locally to deploy to Dagster Cloud Serverless")


@contextmanager
def _template_dockerfile(env_vars, custom_base_image=None) -> Generator[bytes, None, None]:
    DOCKERFILE_TEMPLATE = str(
        importlib.resources.files("dagster_cloud_cli") / "commands/serverless/Dockerfile"
    )
    base_image_command = (
        f"FROM {custom_base_image}"
        if custom_base_image
        else f"FROM public.ecr.aws/docker/library/python:{DEFAULT_PYTHON_VERSION}-slim"
    )
    with open(DOCKERFILE_TEMPLATE, encoding="utf-8") as template:
        dockerfile_content = "\n".join(
            [base_image_command, template.read(), *[f"ENV {env_var}" for env_var in env_vars]]
        )

        yield bytes(dockerfile_content, "utf-8")


def build_image(
    source_directory,
    image: str,
    registry_info,
    env_vars: list[str],
    base_image: Optional[str],
    use_editable_dagster: bool,
    dockerfile_path: Optional[str] = None,
) -> int:
    registry = registry_info["registry_url"]

    with ExitStack() as stack:
        if dockerfile_path:
            file_path = dockerfile_path
            build_input = None
        else:
            file_path = "-"
            build_input = stack.enter_context(_template_dockerfile(env_vars, base_image))

        cmd = [
            "docker",
            "build",
            source_directory,
            "-t",
            f"{registry}:{image}",
            "-f",
            file_path,
            "--platform",
            "linux/amd64",
        ]
        if use_editable_dagster:
            cmd += [
                "--build-context",
                f"oss={os.environ['DAGSTER_GIT_REPO_DIR']}",
                "--build-context",
                f"internal={os.environ['DAGSTER_INTERNAL_GIT_REPO_DIR']}",
            ]
        return subprocess.run(cmd, input=build_input, check=True).returncode


def upload_image(image, registry_info) -> int:
    registry = registry_info["registry_url"]
    aws_token = registry_info["aws_auth_token"]
    if not registry or not aws_token:
        raise ui.error(
            "No registry found. You may need to wait for your Dagster serverless deployment to"
            " activate."
        )

    username, password = base64.b64decode(aws_token).decode("utf-8").split(":")
    subprocess.check_output(
        f"echo {password} | docker login --username {username} --password-stdin {registry}",
        shell=True,
    )
    return subprocess.call(
        ["docker", "push", f"{registry}:{image}"], stderr=sys.stderr, stdout=sys.stdout
    )


def default_image_tag(deployment: str, location_name: str, commit_hash: Optional[str]) -> str:
    commit_hash = commit_hash if commit_hash else str(uuid.uuid4().hex)
    return f"{deployment}-{location_name}-{commit_hash}"

# ruff: noqa: T201
import contextlib
import os
import shutil
from typing import Callable, Dict, Iterator, List, Optional

import dagster._check as check

from automation.git import git_repo_root

from .dagster_docker import DagsterDockerImage, default_images_path


def get_dagster_repo() -> str:
    return git_repo_root()


@contextlib.contextmanager
def copy_directories(
    paths: List[str], cwd: str, destination: str = "build_cache"
) -> Iterator[None]:
    check.invariant(os.path.exists(cwd), "Image directory does not exist")
    build_cache_dir = os.path.join(cwd, destination)

    try:
        os.mkdir(build_cache_dir)

        paths_to_copy = []
        for path in paths:
            src_path = os.path.join(git_repo_root(cwd), path)
            check.invariant(
                os.path.exists(src_path), "Path for copying to image build does not exist"
            )

            _, dest_name = os.path.split(path)
            dest_path = os.path.join(build_cache_dir, dest_name)

            paths_to_copy.append((src_path, dest_path))

        for src_path, dest_path in paths_to_copy:
            print("Syncing {} to build dir {}...".format(src_path, dest_path))
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path)
            else:
                shutil.copy(src_path, dest_path)
        yield

    finally:
        shutil.rmtree(build_cache_dir)


@contextlib.contextmanager
def k8s_example_cm(cwd: str) -> Iterator[None]:
    with copy_directories(
        [
            "examples/deploy_k8s/example_project",
        ],
        cwd,
    ):
        yield


def get_core_celery_k8s_dirs() -> List[str]:
    return [
        "python_modules/dagster",
        "python_modules/libraries/dagster-postgres",
        "python_modules/libraries/dagster-celery",
        "python_modules/libraries/dagster-k8s",
        "python_modules/libraries/dagster-celery-k8s",
    ]


def get_core_k8s_dirs() -> List[str]:
    return [
        "python_modules/dagster",
        "python_modules/libraries/dagster-postgres",
        "python_modules/libraries/dagster-k8s",
    ]


@contextlib.contextmanager
def k8s_example_editable_cm(cwd: str) -> Iterator[None]:
    with copy_directories(
        get_core_celery_k8s_dirs()
        + [
            "python_modules/libraries/dagster-aws",
        ],
        cwd,
    ):
        with copy_directories(
            ["examples/deploy_k8s/example_project"], cwd, destination="example_project"
        ):
            yield


@contextlib.contextmanager
def k8s_dagit_editable_cm(cwd: str) -> Iterator[None]:
    print("!!!!! WARNING: You must call `make rebuild_dagit` after making changes to Dagit !!!!\n")
    with copy_directories(
        get_core_celery_k8s_dirs()
        + [
            "python_modules/dagster-graphql",
            "python_modules/dagit",
        ],
        cwd,
    ):
        yield


@contextlib.contextmanager
def k8s_dagit_example_cm(cwd: str) -> Iterator[None]:
    with copy_directories(
        get_core_celery_k8s_dirs()
        + [
            "python_modules/libraries/dagster-aws",
            "python_modules/dagster-graphql",
            "python_modules/dagit",
        ],
        cwd,
    ):
        with copy_directories(
            ["examples/deploy_k8s/example_project"], cwd, destination="example_project"
        ):
            yield


@contextlib.contextmanager
def k8s_celery_worker_editable_cm(cwd: str) -> Iterator[None]:
    with copy_directories(
        get_core_celery_k8s_dirs(),
        cwd,
    ):
        yield


@contextlib.contextmanager
def user_code_example_cm(cwd: str) -> Iterator[None]:
    with copy_directories(
        [
            "examples/deploy_k8s/example_project",
        ],
        cwd,
    ):
        yield


@contextlib.contextmanager
def user_code_example_editable_cm(cwd: str) -> Iterator[None]:
    with copy_directories(
        get_core_celery_k8s_dirs() + ["python_modules/libraries/dagster-aws"],
        cwd,
    ):
        with copy_directories(
            ["examples/deploy_k8s/example_project"], cwd, destination="example_project"
        ):
            yield


@contextlib.contextmanager
def dagster_k8s_editable_cm(cwd: str) -> Iterator[None]:
    print("!!!!! WARNING: You must call `make rebuild_dagit` after making changes to Dagit !!!!\n")
    with copy_directories(
        get_core_k8s_dirs()
        + [
            "python_modules/dagster-graphql",
            "python_modules/dagit",
            "python_modules/libraries/dagster-aws",
        ],
        cwd,
    ):
        yield


@contextlib.contextmanager
def dagster_celery_k8s_editable_cm(cwd: str) -> Iterator[None]:
    print("!!!!! WARNING: You must call `make rebuild_dagit` after making changes to Dagit !!!!\n")
    with copy_directories(
        get_core_celery_k8s_dirs()
        + [
            "python_modules/dagster-graphql",
            "python_modules/dagit",
            "python_modules/libraries/dagster-aws",
        ],
        cwd,
    ):
        yield


# Some images have custom build context manager functions, listed here
CUSTOM_BUILD_CONTEXTMANAGERS: Dict[str, Callable] = {
    "k8s-example": k8s_example_cm,
    "k8s-example-editable": k8s_example_editable_cm,
    "k8s-dagit-editable": k8s_dagit_editable_cm,
    "k8s-dagit-example": k8s_dagit_example_cm,
    "k8s-celery-worker-editable": k8s_celery_worker_editable_cm,
    "user-code-example": user_code_example_cm,
    "user-code-example-editable": user_code_example_editable_cm,
    "dagster-k8s-editable": dagster_k8s_editable_cm,
    "dagster-celery-k8s-editable": dagster_celery_k8s_editable_cm,
}


def list_images(images_path: Optional[str] = None) -> List[DagsterDockerImage]:
    """List all images that we manage.

    Returns:
        List[DagsterDockerImage]: A list of all images managed by this tool.
    """
    images_path = images_path or default_images_path()
    image_folders = [f.name for f in os.scandir(images_path) if f.is_dir()]

    images = []
    for image in image_folders:
        img = DagsterDockerImage(image, images_path=images_path)
        if image in CUSTOM_BUILD_CONTEXTMANAGERS:
            img = img._replace(build_cm=CUSTOM_BUILD_CONTEXTMANAGERS[image])
        images.append(img)
    return images


def get_image(name: str, images_path: Optional[str] = None) -> DagsterDockerImage:
    """Retrieve the image information from the list defined above."""
    image = next((img for img in list_images(images_path=images_path) if img.image == name), None)
    return check.not_none(image, "could not find image {}".format(name))

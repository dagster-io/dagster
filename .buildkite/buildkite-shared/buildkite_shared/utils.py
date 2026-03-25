import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import yaml


@contextmanager
def pushd(path: Path) -> Iterator[None]:
    prev_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_dir)


def dump_pipeline_yaml(pipeline_dict: dict[str, object]) -> str:
    return yaml.dump(pipeline_dict, default_flow_style=False, Dumper=QuotedStrDumper)


class QuotedStrDumper(yaml.Dumper):
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


QuotedStrDumper.add_representer(str, _str_representer)


_OSS_ROOT = Path(__file__).resolve().parents[3]
_IMAGES_ROOT = _OSS_ROOT / "python_modules" / "automation" / "automation" / "docker" / "images"


def get_image_version(image_name: str) -> str:
    """Returns the image timestamp version. All Python versions must use the same timestamp."""
    with open(_IMAGES_ROOT / image_name / "last_updated.yaml", encoding="utf8") as f:
        versions = set(yaml.safe_load(f).values())
        assert len(versions) == 1
        return versions.pop()


BUILDKITE_TEST_IMAGE_VERSION: str = get_image_version("buildkite-test")


def discover_git_repo_root() -> str:
    # Walk up the directory tree until we find a .git directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(current_dir, ".git")):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise Exception("Could not find git repository root")
        current_dir = parent_dir


GIT_REPO_ROOT = discover_git_repo_root()
_INTERNAL_OSS_PREFIX = "dagster-oss"
_IS_INTERNAL = (Path(GIT_REPO_ROOT) / _INTERNAL_OSS_PREFIX).is_dir()


def oss_path(path: str) -> Path:
    """Convert an OSS-relative path to a repo-relative path."""
    if _IS_INTERNAL:
        return Path(_INTERNAL_OSS_PREFIX) / path
    return Path(path)

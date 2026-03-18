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

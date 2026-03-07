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

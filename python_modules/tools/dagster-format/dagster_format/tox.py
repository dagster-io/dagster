import re
from functools import reduce
from glob import glob
from typing import IO, Callable, Dict, List, Optional, Sequence, Union

from typing_extensions import TypeAlias

from .utils import discover_repo_root, in_cwd, index_with_default, not_none, read_file, write_file

SECTION_ORDER = [
    "tox",
    "testenv",
]

KEY_ORDER = [
    "envlist",
    "skipsdist",
    "skipinstall",
    "usedevelop",
    "extras",
    "setenv",
    "passenv",
    "deps",
    "allowlist_externals",
    "commands",
]

ToxfileSection: TypeAlias = Dict[str, List[str]]
Toxfile: TypeAlias = Dict[str, ToxfileSection]
ToxfileTransform: TypeAlias = Callable[[Toxfile], Toxfile]

def gather_toxfiles(pattern: str = r".*") -> Sequence[str]:
    repo_root = discover_repo_root()
    tox_files: List[str] = []
    with in_cwd(repo_root):
        tox_files.extend(glob("**/tox.ini", recursive=True))
    return [tf for tf in tox_files if re.search(pattern, tf)]


def transform_toxfile(
    toxfile_path: str,
    transforms: Sequence[ToxfileTransform],
    output: Optional[Union[str, IO[str]]] = None,
    *,
    audit: bool = False,
) -> bool:
    output = output or toxfile_path
    toxfile_orig_str = read_file(toxfile_path)
    toxfile = parse_toxfile(toxfile_orig_str)
    transformed_toxfile = reduce(lambda acc, transform: transform(acc), transforms, toxfile)
    toxfile_str = serialize_toxfile(transformed_toxfile)
    if toxfile_str == toxfile_orig_str:
        return False
    else:
        if not audit:
            write_file(output, toxfile_str)
        return True


def parse_toxfile(toxfile_str: str) -> Toxfile:
    lines = toxfile_str.split("\n")
    section: Optional[str] = None
    param: Optional[str] = None
    toxfile: Toxfile = {}
    for line in lines:
        if m := re.match(r"^\[(\S+)\]$", line):
            section = not_none(m.group(1))
            toxfile[section] = {}
        elif section is not None:
            if m := re.search(r"^(\S+) ?= ?", line):
                param = not_none(m.group(1))
                toxfile[section][param] = []
            if param is not None:
                toxfile[section][param].append(line)
    return toxfile


def sort_toxfile(toxfile: Toxfile) -> Toxfile:
    sorted_toxfile: Toxfile = {}
    for k in sorted(toxfile.keys(), key=_toxfile_section_sort_key):
        sorted_toxfile[k] = _sort_toxfile_section(toxfile[k])
    return sorted_toxfile


def _toxfile_section_sort_key(section: str) -> str:
    for i, k in enumerate(SECTION_ORDER):
        if section.startswith(k):
            return f"{i}{section}"
    return section


def _sort_toxfile_section(toxfile_section: ToxfileSection):
    sorted_section: ToxfileSection = {}
    for k in sorted(toxfile_section, key=lambda k: index_with_default(KEY_ORDER, k, default=100)):
        sorted_section[k] = toxfile_section[k]
    return sorted_section


def serialize_toxfile(toxfile: Toxfile):
    lines = []
    for k, v in toxfile.items():
        lines.append(f"[{k}]")
        for line_set in v.values():
            lines.extend(line_set)
        lines.append("")
    toxstr = "\n".join(lines)
    return re.sub(r"\n\n\n+", "\n\n", toxstr).strip() + "\n"

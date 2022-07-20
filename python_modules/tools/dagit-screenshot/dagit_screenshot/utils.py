import os
import re
from glob import glob
from typing import List, Sequence, cast

import yaml
from typing_extensions import NotRequired, TypeAlias, TypedDict


class RawScreenshotSpec(TypedDict):
    id: str
    base_url: NotRequired[str]
    route: NotRequired[str]
    workspace: NotRequired[str]
    steps: NotRequired[List[str]]
    vetted: NotRequired[bool]
    width: NotRequired[int]
    height: NotRequired[int]

class ScreenshotSpec(TypedDict):
    id: str
    base_url: str
    route: str
    workspace: NotRequired[str]
    steps: NotRequired[List[str]]
    vetted: NotRequired[bool]
    width: NotRequired[int]
    height: NotRequired[int]



SpecDB: TypeAlias = Sequence[ScreenshotSpec]


def spec_id_to_relative_path(spec_id: str):
    return spec_id if re.search(r"\.\S+$", spec_id) else f"{spec_id}.png"


def normalize_output_path(path: str, output_root: str):
    return _normalize_path(path, output_root)


def normalize_workspace_path(path: str, workspace_root: str):
    return _normalize_path(path, workspace_root)


def _normalize_path(path: str, root: str):
    return path if os.path.isabs(path) else os.path.join(root, path)


def load_spec(spec_id: str, spec_db_path: str) -> ScreenshotSpec:

    if _is_single_file_spec_db(spec_db_path):
        raw_spec = _load_spec_from_yaml(spec_id, spec_db_path)
    else:
        id_parts = spec_id.split("/")
        db_nested_path = os.path.join(spec_db_path, *id_parts[:-1]) + ".yaml"
        if os.path.exists(db_nested_path):
            relative_id = id_parts[-1]
            raw_spec =_load_spec_from_yaml(relative_id, db_nested_path)
        else:
            db_index_path = os.path.join(spec_db_path, "index.yaml")
            raw_spec = _load_spec_from_yaml(spec_id, db_index_path)

    return _apply_defaults(raw_spec)


def load_spec_db(spec_db_path: str) -> SpecDB:
    db: List[ScreenshotSpec] = []
    if _is_single_file_spec_db(spec_db_path):
        db += _load_yaml(spec_db_path)
    else:
        yaml_files = [
            os.path.relpath(p, start=spec_db_path)
            for p in glob(f"{spec_db_path}/**/*.yaml", recursive=True)
        ]

        for p in yaml_files:
            specs = _load_yaml(os.path.join(spec_db_path, p))
            for raw_spec in specs:
                db.append(_normalize_spec(raw_spec, p))

    return db

def _normalize_spec(raw_spec: RawScreenshotSpec, filepath: str) -> ScreenshotSpec:
    if filepath != '_global.yaml':
        raw_id_parts = os.path.splitext(filepath)[0]
        id_parts = os.path.dirname(raw_id_parts) if os.path.basename(raw_id_parts) == 'index' else raw_id_parts
        raw_spec["id"] = os.path.join(id_parts, raw_spec["id"])

    spec = _apply_defaults(raw_spec)
    return spec

def _is_single_file_spec_db(spec_db_path: str) -> bool:
    return not os.path.isdir(spec_db_path)


def _load_yaml(path: str):
    with open(path, "r", encoding="utf8") as f:
        return yaml.safe_load(f)

<<<<<<< HEAD
def _load_spec_from_yaml(spec_id: str, yaml_path: str) -> RawScreenshotSpec:
=======

def _load_spec_from_yaml(spec_id: str, yaml_path: str) -> ScreenshotSpec:
>>>>>>> 8b0fdb435b ([dagit-screenshot] formatting)
    specs = _load_yaml(yaml_path)
    matches = [spec for spec in specs if spec["id"] == spec_id]
    if len(matches) == 0:
        raise Exception(f"No match for spec [{spec_id}] found in {yaml_path}.")
    elif len(matches) > 1:
        raise Exception(f"Multiple matches for spec [{spec_id}] found in {yaml_path}.")
    return matches[0]

def _apply_defaults(raw_spec: RawScreenshotSpec) -> ScreenshotSpec:
    raw_spec.setdefault("base_url", "http://localhost:3000")
    raw_spec.setdefault("route", "/")
    return cast(ScreenshotSpec, raw_spec)

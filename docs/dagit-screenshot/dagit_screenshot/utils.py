import os
import re
from glob import glob
from typing import List, Sequence

import yaml
from typing_extensions import NotRequired, TypeAlias, TypedDict


class ScreenshotSpec(TypedDict):
    id: str
    workspace: str
    route: str
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
        return _load_spec_from_yaml(spec_id, spec_db_path)
    else:
        id_parts = spec_id.split("/")
        db_nested_path = os.path.join(spec_db_path, *id_parts[:-1]) + ".yaml"
        if os.path.exists(db_nested_path):
            relative_id = id_parts[-1]
            return _load_spec_from_yaml(relative_id, db_nested_path)
        else:
            db_index_path = os.path.join(spec_db_path, "index.yaml")
            return _load_spec_from_yaml(spec_id, db_index_path)


def load_spec_db(spec_db_path: str) -> SpecDB:
    if _is_single_file_spec_db(spec_db_path):
        db = _load_yaml(spec_db_path)
    else:
        yaml_files = [
            os.path.relpath(p, start=spec_db_path) for p in glob(f"{spec_db_path}/**/*.yaml", recursive=True)
        ]
        db: List[ScreenshotSpec] = []
        if "_global.yaml" in yaml_files:
            yaml_files.remove("_global.yaml")
            db.extend(_load_yaml(os.path.join(spec_db_path, "_global.yaml")))

        for p in yaml_files:
            specs = _load_yaml(os.path.join(spec_db_path, p))
            raw_id_parts = os.path.splitext(p)[0]
            id_parts = os.path.dirname(raw_id_parts) if os.path.basename(raw_id_parts) == 'index' else raw_id_parts
            for spec in specs:
                spec["id"] = os.path.join(id_parts, spec["id"])
                db.append(spec)

    return db


def _is_single_file_spec_db(spec_db_path: str) -> bool:
    return not os.path.isdir(spec_db_path)

def _load_yaml(path: str):
    with open(path, "r", encoding="utf8") as f:
        return yaml.safe_load(f)

def _load_spec_from_yaml(spec_id: str, yaml_path: str) -> ScreenshotSpec:
    specs = _load_yaml(yaml_path)
    matches = [spec for spec in specs if spec["id"] == spec_id]
    if len(matches) == 0:
        raise Exception(f"No match for spec [{spec_id}] found in {yaml_path}.")
    elif len(matches) > 1:
        raise Exception(f"Multiple matches for spec [{spec_id}] found in {yaml_path}.")
    return matches[0]

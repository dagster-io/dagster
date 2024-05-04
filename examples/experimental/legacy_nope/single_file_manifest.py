from pathlib import Path
from typing import Any, Sequence

import dagster._check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._manifest.project import NopeProject

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import yaml


def check_key_exists(manifest_obj, key) -> None:
    check.invariant(
        key in manifest_obj,
        f"Expected '{key}' key in invocation manifest {manifest_obj}",
    )


def ensure_key_exists(manifest_obj, key) -> Any:
    check_key_exists(manifest_obj, key)
    return manifest_obj[key]


def get_single_yaml_file(path: Path) -> Path:
    yaml_files = {}
    for file_path in path.iterdir():
        # python_files = {}
        if file_path.suffix == ".yaml":
            yaml_files[file_path.stem] = file_path

    if len(yaml_files) != 1:
        raise Exception(f"Expected exactly one yaml file in {path}, found {yaml_files}")
    return next(iter(yaml_files.values()))


class SingleFileManifestNopeProject(NopeProject):
    @classmethod
    def make_assets_defs(cls, defs_path: Path) -> Sequence[AssetsDefinition]:
        # TODO iterate over groups
        group_manifest_path = get_single_yaml_file(defs_path)
        group_name = group_manifest_path.stem

        full_manifest = yaml.load(group_manifest_path.read_text(), Loader=Loader)
        target_map = cls.invocation_target_map()

        assets_defs = []
        for invocation_manifest in ensure_key_exists(full_manifest, "invocations"):
            target_type = ensure_key_exists(invocation_manifest, "target")
            target_cls = target_map[target_type]
            rel_script_path = ensure_key_exists(invocation_manifest, "script")
            op_name = rel_script_path.split(".")[0]
            script_path = group_manifest_path.parent / Path(rel_script_path)
            script_instance = target_cls(
                target_cls.invocation_target_manifest_class()(
                    op_name=op_name,
                    group_name=group_name,
                    asset_manifest_class=target_cls.asset_manifest_class(),
                    full_manifest_obj=invocation_manifest,
                    full_manifest_path=None,
                    python_script_path=script_path,
                )
            )
            assets_defs.append(script_instance.to_assets_def())

        return assets_defs


defs = SingleFileManifestNopeProject.make_definitions(
    defs_path=Path(__file__).resolve().parent / Path("single_file_defs")
)


if __name__ == "__main__":
    defs.get_implicit_global_asset_job_def().execute_in_process()

# from ast import Dict
# from collections import defaultdict
# from genericpath import isdir
# from typing import List
# from pathlib import Path
#
# from dagster._nope.definitions import ManifestSource, definitions_from_manifest
# from pydantic import BaseModel
#
# class AutofileAssetManifest(BaseModel):
#     asset_key: str
#     deps: List[str]
#
# class AutofileExecutionManifest(BaseModel):
#     script_path: str
#     assets: List[AutofileAssetManifest]
#
# class AutofileManifest(BaseModel):
#     executions: List[AutofileExecutionManifest]
#     ...
#
#
# class AutofileManifestSource(ManifestSource):
#     def __init__(self, defs_path: Path):
#         self.defs_path = defs_path
#
#     def get_manifest(self) -> AutofileManifest:
#         yaml_files = defaultdict(list)
#         for file_path in self.defs_path.iterdir():
#             if file_path.is_dir():
#                 group_name = file_path.stem
#                 for potential_yaml_file in file_path.iterdir():
#                     if potential_yaml_file.suffix == ".yaml":
#                         yaml_files[group_name].append(potential_yaml_file)
#
#
#         for yaml_file in yaml_files.values():
#             ...
#
#         return next(iter(yaml_files.values())
#
# make_nope_definitions(
#
# )
#
# defs = NopeProject.make_definitions(
#     defs_path=Path(__file__).resolve().parent / Path("by_file_defs")
# )
#
# if __name__ == "__main__":
#     defs.get_implicit_global_asset_job_def().execute_in_process()
#

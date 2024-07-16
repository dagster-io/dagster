import os
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Set, Tuple, Union

import pandas as pd
from dagster import AssetKey, AssetOut, Nothing, TableColumn, TableSchema
from dagster._core.definitions.metadata import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
    TableColumnConstraints,
    TableMetadataSet,
)
from dagster._core.definitions.tags import StorageKindTagSet
from pydantic import BaseModel, DirectoryPath

from .asset_utils import dagster_name_fn, default_asset_key_fn
from .constants import (
    DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
    SDF_INFORMATION_SCHEMA_TABLES,
    SDF_TARGET_DIR,
)
from .errors import DagsterSdfInformationSchemaNotFoundError


class LazyDataFrameDict:
    def __init__(
        self,
        information_schema_dir: Union[Path, str],
    ):
        if isinstance(information_schema_dir, str):
            information_schema_dir = Path(information_schema_dir)
        self.information_schema_dir = information_schema_dir
        self.data = {}
        self.loaded = {}

    def add(self, key: str, dataframe: pd.DataFrame):
        self.data[key] = dataframe
        self.loaded[key] = True

    def get(self, key: str) -> pd.DataFrame:
        if key not in SDF_INFORMATION_SCHEMA_TABLES:
            raise ValueError(f"Table {key} not valid information schema table.")
        if key not in self.loaded:
            self.data[key] = self._load_dataframe(key)
            self.loaded[key] = True
        return self.data[key]

    def _load_dataframe(self, key: str) -> pd.DataFrame:
        # Load the parquet file from disk
        df_list = [
            pd.read_parquet(f, engine="pyarrow")
            for f in self.information_schema_dir.joinpath(key).glob("*.parquet")
        ]
        return pd.concat(df_list, ignore_index=True)

    def to_dict(self):
        # Convert to a serializable dictionary format
        return {k: v.to_dict() for k, v in self.data.items() if self.loaded[k]}

    @classmethod
    def from_dict(cls, dict_data):
        instance = cls()
        for key, data in dict_data.items():
            instance.data[key] = pd.DataFrame(data)
            instance.loaded[key] = True
        return instance


class SdfInformationSchema(BaseModel):
    workspace_dir: DirectoryPath
    target_dir: DirectoryPath
    information_schema_dir: DirectoryPath
    information_schema: LazyDataFrameDict

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        workspace_dir: Union[Path, str],
        target_dir: Union[Path, str],
        environment: str = DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
        **data,
    ):
        workspace_dir = Path(workspace_dir) if isinstance(workspace_dir, str) else workspace_dir
        target_dir = Path(target_dir) if isinstance(target_dir, str) else target_dir
        information_schema_dir = target_dir.joinpath(
            SDF_TARGET_DIR, environment, "data", "system", "information_schema::sdf"
        )
        if not information_schema_dir.exists():
            raise DagsterSdfInformationSchemaNotFoundError(
                f"Information schema directory {information_schema_dir} does not exist."
            )
        super().__init__(
            workspace_dir=workspace_dir,
            target_dir=target_dir,
            information_schema_dir=information_schema_dir,
            information_schema=LazyDataFrameDict(information_schema_dir),
            **data,
        )

    def is_hydrated(self) -> bool:
        for table in SDF_INFORMATION_SCHEMA_TABLES:
            if not any(self.information_schema_dir.joinpath(table).iterdir()):
                return False
        return True

    def get_dependencies(self) -> Dict[str, Tuple[List[str], List[str]]]:
        tables = self.information_schema.get("tables")[
            ["table_id", "purpose", "depends_on", "depended_on_by"]
        ]
        dependencies = {}
        for _, row in tables.iterrows():
            if row["purpose"] in ["system", "external_system"]:
                continue
            dependencies[row["table_id"]] = (
                row["depends_on"].tolist(),
                row["depended_on_by"].tolist(),
            )
        return dependencies

    def get_columns(self) -> Dict[str, List[TableColumn]]:
        columns = self.information_schema.get("columns")[
            ["table_id", "column_id", "classifiers", "column_name", "datatype", "description"]
        ]
        table_columns: Dict[str, List[TableColumn]] = {}
        for _, row in columns.iterrows():
            if row["table_id"] not in table_columns:
                table_columns[row["table_id"]] = []
            table_columns[row["table_id"]].append(
                TableColumn(
                    name=row["column_name"],
                    type=row["datatype"],
                    description=row["description"],
                    constraints=TableColumnConstraints(other=row["classifiers"].tolist()),
                )
            )
        return table_columns

    def get_outs_and_internal_deps(
        self, io_manager_key: Optional[str]
    ) -> Tuple[Mapping[str, AssetOut], Dict[str, Set[AssetKey]]]:
        outs: Dict[str, AssetOut] = {}
        internal_asset_deps: Dict[str, Set[AssetKey]] = {}
        tables = self.information_schema.get("tables")[
            [
                "table_id",
                "purpose",
                "dialect",
                "origin",
                "description",
                "depends_on",
                "depended_on_by",
                "source_locations",
            ]
        ]
        table_columns = self.get_columns()
        for _, row in tables.iterrows():
            if row["purpose"] in ["system", "external-system"]:
                continue
            if row["origin"] == "remote":
                continue
            code_references = None
            for source_location in row["source_locations"]:
                if source_location.endswith(".sql"):
                    code_references = CodeReferencesMetadataSet(
                        code_references=CodeReferencesMetadataValue(
                            code_references=[
                                LocalFileCodeReference(
                                    file_path=os.fspath(
                                        self.workspace_dir.joinpath(source_location)
                                    )
                                )
                            ]
                        )
                    )
            asset_key = default_asset_key_fn(row["table_id"])
            metadata = {
                **TableMetadataSet(
                    column_schema=TableSchema(
                        columns=table_columns.get(row["table_id"], []),
                    ),
                    relation_identifier=row["table_id"],
                ),
                **(code_references if code_references else {}),
            }
            outs[dagster_name_fn(row["table_id"])] = AssetOut(
                key=asset_key,
                dagster_type=Nothing,
                io_manager_key=io_manager_key,
                description=row["description"],
                is_required=False,
                metadata=metadata,
                owners=[],
                tags={
                    **(StorageKindTagSet(storage_kind=row["dialect"])),
                },
                group_name=None,
                code_version=None,
                freshness_policy=None,
                auto_materialize_policy=None,
            )
            internal_asset_deps[dagster_name_fn(row["table_id"])] = set(
                [default_asset_key_fn(dep) for dep in row["depends_on"]]
            )
        return outs, internal_asset_deps

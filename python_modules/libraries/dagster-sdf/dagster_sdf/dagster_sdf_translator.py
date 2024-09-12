from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from dagster import (
    AssetCheckKey,
    AssetKey,
    _check as check,
)
from dagster._annotations import public

from dagster_sdf.asset_utils import (
    default_asset_check_key_fn,
    default_asset_key_fn,
    default_description_fn,
)


@dataclass(frozen=True)
class DagsterSdfTranslatorSettings:
    """Settings to enable Dagster features for your sdf project.

    Args:
        enable_asset_checks (bool): Whether to load sdf table tests as Dagster asset checks.
            Defaults to False.
        enable_code_references (bool): Whether to enable Dagster code references for sdf tables.
            Defaults to False.
        enable_raw_sql_description (bool): Whether to display sdf raw sql in Dagster descriptions.
            Defaults to True.
        enable_materialized_sql_description (bool): Whether to display sdf materialized sql in
            Dagster descriptions. Defaults to True.

    """

    enable_asset_checks: bool = False
    enable_code_references: bool = False
    enable_raw_sql_description: bool = True
    enable_materialized_sql_description: bool = True


class DagsterSdfTranslator:
    """Holds a set of methods that derive Dagster asset definition metadata given a representation
    of an sdf resource (models, tests, sources, etc).

    This class is exposed so that methods can be overriden to customize how Dagster asset metadata
    is derived.
    """

    def __init__(self, settings: Optional[DagsterSdfTranslatorSettings] = None):
        """Initialize the translator.

        Args:
            settings (Optional[DagsterSdfTranslatorSettings]): Settings for the translator.
        """
        self._settings = settings or DagsterSdfTranslatorSettings()

    @property
    def settings(self) -> DagsterSdfTranslatorSettings:
        if not hasattr(self, "_settings"):
            self._settings = DagsterSdfTranslatorSettings()

        return self._settings

    @public
    def get_asset_key(self, catalog: str, schema: str, table: str) -> AssetKey:
        return default_asset_key_fn(catalog, schema, table)

    @public
    def get_check_key_for_test(self, catalog: str, schema: str, table: str) -> AssetCheckKey:
        return default_asset_check_key_fn(catalog, schema, table)

    @public
    def get_description(
        self, table_row: Dict[str, Any], workspace_dir: Optional[Path], output_dir: Optional[Path]
    ) -> str:
        """A function that takes a dictionary representing columns of an sdf table row in sdf's
        information schema and returns the Dagster description for that table.

        This method can be overridden to provide a custom description for an sdf resource.

        Args:
            table_row (Dict[str, Any]): A dictionary representing columns of an sdf table row.
            workspace_dir (Optional[Path]): The path to the workspace directory.

        Returns:
            str: The description for the dbt resource.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_sdf import DagsterSdfTranslator


                class CustomDagsterSdfTranslator(DagsterSdfTranslator):
                    def get_description(self, table_row: Dict[str, Any], workspace_dir: Optiona[Path], output_dir: Optional[Path]) -> str:
                        return "custom description"
        """
        return default_description_fn(
            table_row,
            workspace_dir,
            output_dir,
            self.settings.enable_raw_sql_description,
            self.settings.enable_materialized_sql_description,
        )


def validate_translator(dagster_sdf_translator: DagsterSdfTranslator) -> DagsterSdfTranslator:
    return check.inst_param(
        dagster_sdf_translator,
        "dagster_sdf_translator",
        DagsterSdfTranslator,
        additional_message=(
            "Ensure that the argument is an instantiated class that subclasses"
            " DagsterSdfTranslator."
        ),
    )


def validate_opt_translator(
    dagster_sdf_translator: Optional[DagsterSdfTranslator],
) -> Optional[DagsterSdfTranslator]:
    return check.opt_inst_param(
        dagster_sdf_translator,
        "dagster_sdf_translator",
        DagsterSdfTranslator,
        additional_message=(
            "Ensure that the argument is an instantiated class that subclasses"
            " DagsterSdfTranslator."
        ),
    )

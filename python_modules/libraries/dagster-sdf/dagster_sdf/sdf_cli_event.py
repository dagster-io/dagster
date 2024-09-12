from dataclasses import dataclass
from typing import AbstractSet, Any, Dict, Iterator, Optional

from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetMaterialization,
    OpExecutionContext,
    Output,
)
from dagster._annotations import public

from dagster_sdf.asset_utils import dagster_name_fn, exists_in_selected
from dagster_sdf.constants import (
    DAGSTER_SDF_CATALOG_NAME,
    DAGSTER_SDF_DIALECT,
    DAGSTER_SDF_PURPOSE,
    DAGSTER_SDF_SCHEMA_NAME,
    DAGSTER_SDF_TABLE_ID,
    DAGSTER_SDF_TABLE_NAME,
)
from dagster_sdf.dagster_sdf_translator import DagsterSdfTranslator
from dagster_sdf.sdf_event_iterator import SdfDagsterEventType


@dataclass
class SdfCliEventMessage:
    """The representation of an sdf CLI event.

    Args:
        raw_event (Dict[str, Any]): The raw event dictionary.
    """

    raw_event: Dict[str, Any]

    @property
    def is_result_event(self) -> bool:
        return (
            bool(self.raw_event.get("ev_tb"))
            and bool(self.raw_event.get("ev_tb_catalog"))
            and bool(self.raw_event.get("ev_tb_schema"))
            and bool(self.raw_event.get("ev_tb_table"))
            and bool(self.raw_event.get("st_code"))
            and bool(self.raw_event.get("st_done"))
            and bool(self.raw_event.get("st_dur_ms"))
        )

    @public
    def to_default_asset_events(
        self,
        dagster_sdf_translator: DagsterSdfTranslator = DagsterSdfTranslator(),
        context: Optional[OpExecutionContext] = None,
    ) -> Iterator[SdfDagsterEventType]:
        """Convert an sdf CLI event to a set of corresponding Dagster events.

        Args:
            context (Optional[OpExecutionContext]): The execution context.

        Returns:
            Iterator[Union[Output, AssetMaterialization]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models)

                In a Dagster op definition, the following are yielded:
                - AssetMaterialization for refables (e.g. models)
        """
        if not self.is_result_event:
            return

        is_success = self.raw_event["st_code"] == "succeeded"
        if not is_success:
            return

        selected_output_names: AbstractSet[str] = (
            context.selected_output_names if context else set()
        )

        catalog = self.raw_event["ev_tb_catalog"]
        schema = self.raw_event["ev_tb_schema"]
        table = self.raw_event["ev_tb_table"]
        purpose = self.raw_event["ev_tb_purpose"]
        dialect = self.raw_event["ev_tb_dialect"]

        # If assets are selected, only yield events for selected assets
        if len(selected_output_names) > 0:
            exists = exists_in_selected(
                catalog,
                schema,
                table,
                purpose,
                dialect,
                selected_output_names,
                dagster_sdf_translator.settings.enable_asset_checks,
            )
            if not exists:
                return

        table_id = self.raw_event["ev_tb"]
        default_metadata = {
            DAGSTER_SDF_TABLE_ID: table_id,
            DAGSTER_SDF_CATALOG_NAME: catalog,
            DAGSTER_SDF_SCHEMA_NAME: schema,
            DAGSTER_SDF_TABLE_NAME: table,
            DAGSTER_SDF_PURPOSE: purpose,
            DAGSTER_SDF_DIALECT: dialect,
            "Execution Duration": self.raw_event["st_dur_ms"] / 1000,
            "Materialized From Cache": True if self.raw_event["st_done"] == "cached" else False,
        }
        asset_key = dagster_sdf_translator.get_asset_key(catalog, schema, table)
        if purpose == "model":
            has_asset_def = bool(context and context.has_assets_def)
            event = (
                Output(
                    value=None,
                    output_name=dagster_name_fn(
                        catalog,
                        schema,
                        table,
                    ),
                    metadata=default_metadata,
                )
                if has_asset_def
                else AssetMaterialization(
                    asset_key=asset_key,
                    metadata=default_metadata,
                )
            )

            yield event
        elif purpose == "test" and dagster_sdf_translator.settings.enable_asset_checks:
            passed = self.raw_event["st_verdict"] == "passed"
            asset_check_key = dagster_sdf_translator.get_check_key_for_test(catalog, schema, table)
            # if the asset key is the same as the asset check key, then the test is not a table / column test
            if asset_key == asset_check_key.asset_key:
                return
            metadata = {
                **default_metadata,
                "status_verdict": self.raw_event["st_verdict"],
            }
            yield AssetCheckResult(
                passed=passed,
                asset_key=asset_check_key.asset_key,
                check_name=asset_check_key.name,
                metadata=metadata,
                severity=AssetCheckSeverity.ERROR,
            )
        else:
            return

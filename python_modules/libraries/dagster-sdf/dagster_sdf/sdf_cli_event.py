from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional

from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetMaterialization,
    OpExecutionContext,
    Output,
)
from dagster._annotations import public

from .asset_utils import dagster_name_fn
from .dagster_sdf_translator import DagsterSdfTranslator
from .sdf_event_iterator import SdfDagsterEventType


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
            bool(self.raw_event.get("ev_table"))
            and bool(self.raw_event.get("status_type"))
            and bool(self.raw_event.get("status_code"))
            and self.raw_event["ev_type"] == "close"
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

        is_success = self.raw_event["status_code"] == "succeeded"
        if not is_success:
            return

        table_id = self.raw_event["ev_table"]
        default_metadata = {
            "table_id": table_id,
            "Execution Duration": self.raw_event["ev_dur_ms"] / 1000,
        }
        asset_key = dagster_sdf_translator.get_asset_key(table_id)
        if self.raw_event["ev_table_purpose"] == "model":
            has_asset_def = bool(context and context.has_assets_def)
            event = (
                Output(
                    value=None,
                    output_name=dagster_name_fn(table_id),
                    metadata=default_metadata,
                )
                if has_asset_def
                else AssetMaterialization(
                    asset_key=asset_key,
                    metadata=default_metadata,
                )
            )

            yield event
        elif (
            self.raw_event["ev_table_purpose"] == "test"
            and dagster_sdf_translator.settings.enable_asset_checks
        ):
            passed = self.raw_event["status_verdict"] == "Passed"
            asset_check_key = dagster_sdf_translator.get_check_key_for_test(table_id)
            # if the asset key is the same as the asset check key, then the test is not a table / column test
            if asset_key == asset_check_key.asset_key:
                return
            metadata = {
                **default_metadata,
                "status_verdict": self.raw_event["status_verdict"],
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

from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional

from dagster import AssetMaterialization, OpExecutionContext, Output
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
            self.raw_event["ev"] == "cmd.do.derived"
            and self.raw_event["ev_type"] == "close"
            and bool(self.raw_event.get("status"))
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

        is_success = self.raw_event["status"] == "succeeded"
        if not is_success:
            return

        table_id = self.raw_event["table"]
        default_metadata = {
            "table_id": table_id,
            "Execution Duration": self.raw_event["ev_dur_ms"] / 1000,
        }

        has_asset_def = bool(context and context.has_assets_def)
        event = (
            Output(
                value=None,
                output_name=dagster_name_fn(table_id),
                metadata=default_metadata,
            )
            if has_asset_def
            else AssetMaterialization(
                asset_key=dagster_sdf_translator.get_asset_key(table_id),
                metadata=default_metadata,
            )
        )

        yield event

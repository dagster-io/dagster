from collections.abc import Mapping
from typing import Any

from dagster_components import component_type
from dagster_components.lib import SlingReplicationCollectionComponent

import dagster as dg


@component_type(name="custom_subclass")
class SubclassWithScope(SlingReplicationCollectionComponent):
    def get_additional_scope(self) -> Mapping[str, Any]:
        def _custom_cron(cron_schedule: str) -> dg.AutomationCondition:
            return (
                dg.AutomationCondition.on_cron(cron_schedule)
                & ~dg.AutomationCondition.in_progress()
            )

        return {"custom_cron": _custom_cron}

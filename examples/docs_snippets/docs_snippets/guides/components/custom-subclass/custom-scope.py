from collections.abc import Mapping
from typing import Any

from dagster_sling import SlingReplicationCollectionComponent

import dagster as dg


class SubclassWithScope(SlingReplicationCollectionComponent):
    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        def _custom_cron(cron_schedule: str) -> dg.AutomationCondition:
            return (
                dg.AutomationCondition.on_cron(cron_schedule)
                & ~dg.AutomationCondition.in_progress()
            )

        return {"custom_cron": _custom_cron}

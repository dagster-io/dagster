from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class SchedulingInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for scheduling operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    # Storage access
    @property
    def schedule_storage(self):
        return self._instance._schedule_storage  # noqa: SLF001

    @property
    def run_storage(self):
        return self._instance._run_storage  # noqa: SLF001

    @property
    def scheduler(self):
        return self._instance._scheduler  # noqa: SLF001

    # Instance methods used by scheduling operations
    def get_instigator_state(self, origin_id: str, selector_id: str):
        return self._instance.get_instigator_state(origin_id, selector_id)

    def add_instigator_state(self, state):
        return self._instance.add_instigator_state(state)

    def update_instigator_state(self, state):
        return self._instance.update_instigator_state(state)

    def delete_instigator_state(self, origin_id: str, selector_id: str):
        return self._instance.delete_instigator_state(origin_id, selector_id)

    def all_instigator_state(
        self,
        repository_origin_id=None,
        repository_selector_id=None,
        instigator_type=None,
        instigator_statuses=None,
    ):
        return self._instance.all_instigator_state(
            repository_origin_id, repository_selector_id, instigator_type, instigator_statuses
        )

    @property
    def supports_batch_tick_queries(self):
        return self._instance.supports_batch_tick_queries

    def get_settings(self, key):
        return self._instance.get_settings(key)

    def info_str_for_component(self, component_name, component):
        return self._instance._info_str_for_component(component_name, component)  # noqa: SLF001

    @property
    def instance(self):
        """Get the underlying instance for methods that need full access."""
        return self._instance

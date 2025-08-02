from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class EventInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for event operations."""

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    # Storage access
    @property
    def event_storage(self):
        return self._instance._event_storage  # noqa: SLF001

    @property
    def run_storage(self):
        return self._instance._run_storage  # noqa: SLF001

    @property
    def subscribers(self):
        return self._instance._subscribers  # noqa: SLF001

    @property
    def event_buffer(self):
        return self._instance._event_buffer  # noqa: SLF001

    @property
    def run_retries_enabled(self):
        return self._instance.run_retries_enabled

    # Run operations
    def get_run_by_id(self, run_id):
        return self._instance.get_run_by_id(run_id)

    def add_run_tags(self, run_id, tags):
        return self._instance.add_run_tags(run_id, tags)

    def should_retry_run(self, run, run_failure_reason):
        from dagster._daemon.auto_run_reexecution.auto_run_reexecution import (
            auto_reexecution_should_retry_run,
        )

        return auto_reexecution_should_retry_run(self._instance, run, run_failure_reason)

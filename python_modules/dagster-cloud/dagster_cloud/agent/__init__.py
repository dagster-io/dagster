from typing import NamedTuple

from dagster._serdes import whitelist_for_serdes
from dagster_cloud_cli.core.agent_queue import AgentQueue


@whitelist_for_serdes
class AgentQueuesConfig(NamedTuple):
    include_default_queue: bool = True
    additional_queues: list[AgentQueue] | None = None

    @staticmethod
    def default_queues() -> list[AgentQueue]:
        return [None]

    @property
    def queues(self) -> list[AgentQueue]:
        if self.additional_queues:
            queues = self.additional_queues.copy()
        else:
            queues = []
        if self.include_default_queue:
            for queue in AgentQueuesConfig.default_queues():
                queues.append(queue)
        return queues

    def matches(self, queue: AgentQueue):
        return queue in self.queues

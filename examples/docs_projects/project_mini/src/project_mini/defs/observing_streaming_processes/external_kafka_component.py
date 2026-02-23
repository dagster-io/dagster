import dagster as dg


class ExternalKafkaAsset(dg.Component, dg.Model, dg.Resolvable):
    """Reusable component for external Kafka/Event Hub streams."""

    asset_key: str
    topic: str
    broker: str | None = None
    event_hub_namespace: str | None = None
    description: str | None = None
    group_name: str = "default"

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        external_asset = dg.AssetSpec(
            key=self.asset_key,
            description=self.description or f"External stream: {self.topic}",
            group_name=self.group_name,
            kinds={"kafka", "streaming"},
            metadata={
                "source": "External Kafka/Azure Event Hub",
                "topic": self.topic,
                "broker": self.broker or "N/A",
                "event_hub_namespace": self.event_hub_namespace or "N/A",
                "managed_by": "External Infrastructure Team",
            },
        )
        return dg.Definitions(assets=[external_asset])

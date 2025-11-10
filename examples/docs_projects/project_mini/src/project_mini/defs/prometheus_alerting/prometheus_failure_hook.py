import time
from typing import TYPE_CHECKING, Optional

import dagster as dg
from prometheus_client import CollectorRegistry, Counter, Gauge, push_to_gateway

if TYPE_CHECKING:
    from dagster_prometheus import PrometheusResource


# start_failure_hook_factory
def create_prometheus_failure_hook(
    prometheus_resource_key: str = "prometheus",
) -> dg.failure_hook:
    # end_failure_hook_factory

    # start_failure_hook_implementation
    @dg.failure_hook(required_resource_keys={prometheus_resource_key})
    def prometheus_failure_hook(context: dg.HookContext):
        """Report asset failures to Prometheus with metadata."""
        prometheus: PrometheusResource = getattr(context.resources, prometheus_resource_key)

        # Get asset owner from materialization metadata
        asset_owner: Optional[str] = None
        asset_key_str = context.op.name if context.op else "unknown"

        # Get owner from latest materialization metadata
        try:
            instance = context.instance
            asset_key = dg.AssetKey.from_user_string(asset_key_str)

            latest_materialization = instance.get_latest_materialization_event(asset_key)
            if latest_materialization and latest_materialization.asset_materialization:
                metadata = latest_materialization.asset_materialization.metadata
                owner_metadata = metadata.get("owner")
                if owner_metadata:
                    # Handle both MetadataValue and raw string
                    asset_owner = (
                        owner_metadata.value if hasattr(owner_metadata, "value") else owner_metadata
                    )
                    context.log.info(f"[HOOK] Found owner from metadata: {asset_owner}")
            else:
                context.log.info(f"[HOOK] No previous materialization found for {asset_key_str}")
        except Exception as e:
            context.log.warning(f"[HOOK] Could not retrieve owner from materialization: {e}")

        asset_key = asset_key_str

        # Get current timestamp
        failure_timestamp = time.time()

        context.log.info(
            f"[HOOK] Recording asset failure in Prometheus: {asset_key} "
            f"(owner: {asset_owner or 'unknown'})"
        )

        # start_prometheus_metrics_creation
        # Create a custom registry for this push
        registry = CollectorRegistry()

        # Create metrics with labels
        failure_counter = Counter(
            "dagster_asset_failures_total",
            "Total number of Dagster asset failures",
            labelnames=["asset_name", "asset_owner", "job_name"],
            registry=registry,
        )

        failure_timestamp_gauge = Gauge(
            "dagster_asset_last_failure_timestamp",
            "Timestamp of last asset failure",
            labelnames=["asset_name", "asset_owner", "job_name"],
            registry=registry,
        )
        # end_prometheus_metrics_creation

        # Set the label values and increment/set the metrics
        failure_counter.labels(
            asset_name=asset_key,
            asset_owner=asset_owner or "unknown",
            job_name=context.job_name or "unknown",
        ).inc()

        failure_timestamp_gauge.labels(
            asset_name=asset_key,
            asset_owner=asset_owner or "unknown",
            job_name=context.job_name or "unknown",
        ).set(failure_timestamp)

        # start_push_to_gateway
        # Push to gateway using the custom registry
        try:
            push_to_gateway(
                prometheus.gateway,
                job="dagster_asset_failures",
                registry=registry,
            )
            context.log.info("Successfully pushed metrics to Prometheus gateway")
        except Exception as e:
            context.log.warning(f"Failed to push metrics to Prometheus: {e}")
        # end_push_to_gateway

        context.log.warning(f"Asset {asset_key} failed (owner: {asset_owner or 'unknown'})")

    # end_failure_hook_implementation

    return prometheus_failure_hook


# start_hook_usage_example
# Create the default instance
prometheus_failure_hook = create_prometheus_failure_hook()


@dg.asset(op_tags={"dagster/failure_hook": "prometheus_failure_hook"})
def prometheus_failure_hook_asset():
    pass


# end_hook_usage_example

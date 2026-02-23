"""Health monitoring asset that aggregates status of all Tier-0 assets."""

from datetime import datetime
from typing import Any

import dagster as dg
from dagster._core.events import DagsterEventType


# start_health_check_function
def get_asset_health(
    context: dg.AssetExecutionContext, asset_key: dg.AssetKey
) -> tuple[str, dict[str, Any]]:
    instance = context.instance
    details: dict[str, Any] = {
        "materialization_status": "unknown",
        "asset_checks": [],
        "freshness_status": "unknown",
        "last_materialized": None,
    }
    has_errors = False
    has_warnings = False

    try:
        latest_mat = instance.get_latest_materialization_event(asset_key)
        if latest_mat:
            details["last_materialized"] = datetime.fromtimestamp(latest_mat.timestamp).isoformat()
            details["materialization_status"] = "success"
        else:
            details["materialization_status"] = "never_materialized"
            has_warnings = True
    except Exception as e:
        details["materialization_status"] = f"error: {e!s}"
        has_errors = True

    try:
        from dagster._core.storage.event_log.base import EventRecordsFilter

        records = instance.get_event_records(
            event_records_filter=EventRecordsFilter(
                event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
                asset_key=asset_key,
            ),
            limit=100,
            ascending=False,
        )
        for record in records:
            if not record.event_log_entry or not record.event_log_entry.dagster_event:
                continue
            event = record.event_log_entry.dagster_event
            check_data = event.asset_check_evaluation_data
            if any(c["check_name"] == check_data.check_name for c in details["asset_checks"]):
                continue
            check_info = {
                "check_name": check_data.check_name,
                "passed": check_data.passed,
                "severity": str(getattr(check_data, "severity", "ERROR")),
            }
            details["asset_checks"].append(check_info)
            if not check_data.passed:
                if check_info["severity"] == "AssetCheckSeverity.WARN":
                    has_warnings = True
                else:
                    has_errors = True
    except Exception as e:
        details["asset_checks"] = [{"error": str(e)}]
        context.log.warning(f"Error checking asset checks for {asset_key}: {e}")

    try:
        asset_graph = context.repository_def.asset_graph
        if asset_graph.has(asset_key):
            node = asset_graph.get(asset_key)
            if hasattr(node, "freshness_policy") and node.freshness_policy:
                policy = node.freshness_policy
                if latest_mat and hasattr(policy, "fail_window") and policy.fail_window:
                    lag = datetime.now().timestamp() - latest_mat.timestamp
                    fail_secs = policy.fail_window.total_seconds()
                    warn_secs = policy.warn_window.total_seconds() if policy.warn_window else None
                    if lag > fail_secs:
                        details["freshness_status"] = (
                            f"stale (lag: {lag / 60:.1f}m > fail: {fail_secs / 60:.1f}m)"
                        )
                        has_errors = True
                    elif warn_secs and lag > warn_secs:
                        details["freshness_status"] = f"warning (lag: {lag / 60:.1f}m)"
                        has_warnings = True
                    else:
                        details["freshness_status"] = f"fresh (lag: {lag / 60:.1f}m)"
                elif not latest_mat:
                    details["freshness_status"] = "no_materialization"
                    has_errors = True
                else:
                    details["freshness_status"] = "policy_present"
            else:
                details["freshness_status"] = "no_policy"
    except Exception as e:
        details["freshness_status"] = f"error: {e!s}"
        context.log.warning(f"Error checking freshness for {asset_key}: {e}")

    status = "UNHEALTHY" if has_errors else ("WARNING" if has_warnings else "HEALTHY")
    return status, details


# end_health_check_function


# start_health_monitoring_asset
TIER0_ASSETS = [
    dg.AssetKey("market_risk_data"),
    dg.AssetKey("security_master_data"),
    dg.AssetKey("credit_risk_data"),
]


@dg.asset(
    description="Aggregated health status of all Tier-0 critical assets",
    group_name="monitoring",
)
def tier0_health_status(context: dg.AssetExecutionContext) -> dict[str, Any]:
    context.log.info("=" * 60)
    context.log.info("TIER-0 ASSET HEALTH REPORT")
    context.log.info("=" * 60)

    health_results: dict[str, str] = {}
    unhealthy_assets: list[str] = []
    warning_assets: list[str] = []
    asset_details: dict[str, dict[str, Any]] = {}

    for asset_key in TIER0_ASSETS:
        name = asset_key.to_user_string()
        status, details = get_asset_health(context, asset_key)

        health_results[name] = status
        asset_details[name] = details

        if status == "UNHEALTHY":
            unhealthy_assets.append(name)
            context.log.error(f"❌ {name}: {status}")
            if details["materialization_status"] != "success":
                context.log.error(f"   └─ Materialization: {details['materialization_status']}")
            for check in details["asset_checks"]:
                if not check.get("passed", True):
                    context.log.error(f"   └─ Check '{check['check_name']}': FAILED")
        elif status == "WARNING":
            warning_assets.append(name)
            context.log.warning(f"⚠️  {name}: {status}")
        else:
            context.log.info(f"✅ {name}: {status}")
            if details["last_materialized"]:
                context.log.info(f"   └─ Last materialized: {details['last_materialized']}")

    context.log.info("=" * 60)
    context.log.info(
        f"Healthy: {len(health_results) - len(unhealthy_assets) - len(warning_assets)}"
    )
    context.log.info(f"Warnings: {len(warning_assets)}")
    context.log.info(f"Unhealthy: {len(unhealthy_assets)}")

    if unhealthy_assets:
        context.log.error("Action Required: Review asset health in Dagster UI")

    return {
        "timestamp": datetime.now().isoformat(),
        "total_assets": len(TIER0_ASSETS),
        "healthy": len(health_results) - len(unhealthy_assets) - len(warning_assets),
        "warnings": len(warning_assets),
        "unhealthy": len(unhealthy_assets),
        "unhealthy_assets": unhealthy_assets,
        "warning_assets": warning_assets,
        "health_results": health_results,
        "asset_details": asset_details,
        "overall_status": "DEGRADED"
        if unhealthy_assets
        else ("WARNING" if warning_assets else "HEALTHY"),
    }


# end_health_monitoring_asset


# start_schedules
tier0_health_check_job = dg.define_asset_job(
    name="tier0_health_check_job",
    selection=dg.AssetSelection.assets(tier0_health_status),
    description="Checks the health of all Tier-0 critical assets",
)

start_of_day_health_check = dg.ScheduleDefinition(
    name="start_of_day_health_check",
    job=tier0_health_check_job,
    cron_schedule="0 8 * * *",
    description="Start-of-day health check for all Tier-0 assets",
)

end_of_day_health_check = dg.ScheduleDefinition(
    name="end_of_day_health_check",
    job=tier0_health_check_job,
    cron_schedule="0 18 * * *",
    description="End-of-day health check for all Tier-0 assets",
)

hourly_health_check = dg.ScheduleDefinition(
    name="hourly_health_check",
    job=tier0_health_check_job,
    cron_schedule="0 * * * *",
    description="Hourly health check for all Tier-0 assets",
)
# end_schedules

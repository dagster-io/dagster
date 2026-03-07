"""Tier-0 critical assets with freshness policies and asset checks."""

import random
from datetime import datetime, timedelta

import dagster as dg


# start_critical_asset_with_freshness
@dg.asset(
    group_name="risk",
    tags={"tier": "tier-0", "criticality": "high"},
    description="Market risk calculations and exposure metrics",
    freshness_policy=dg.FreshnessPolicy.time_window(
        fail_window=timedelta(hours=1),
        warn_window=timedelta(minutes=45),
    ),
)
def market_risk_data(context: dg.AssetExecutionContext) -> dict:
    data = {
        "timestamp": datetime.now().isoformat(),
        "var_95": random.uniform(1_000_000, 5_000_000),
        "portfolio_value": random.uniform(100_000_000, 500_000_000),
    }
    context.log.info(f"Market risk VaR: ${data['var_95']:,.2f}")
    return data


@dg.asset_check(asset=market_risk_data, description="Validates market risk data quality")
def market_risk_data_quality(context: dg.AssetExecutionContext) -> dg.AssetCheckResult:
    passed = random.random() > 0.1
    if passed:
        return dg.AssetCheckResult(
            passed=True,
            metadata={
                "validation_time": datetime.now().isoformat(),
                "checks_passed": "VaR within limits, positions validated",
            },
        )
    else:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            metadata={
                "validation_time": datetime.now().isoformat(),
                "error": "VaR exceeds risk limits",
            },
        )


# end_critical_asset_with_freshness


# start_multiple_tier0_assets
@dg.asset(
    group_name="security_master",
    tags={"tier": "tier-0", "criticality": "high"},
    description="Security master data - pricing and reference data for all instruments",
    freshness_policy=dg.FreshnessPolicy.time_window(
        fail_window=timedelta(minutes=30),
        warn_window=timedelta(minutes=20),
    ),
)
def security_master_data(context: dg.AssetExecutionContext) -> dict:
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_securities": random.randint(10_000, 50_000),
        "updated_prices": random.randint(8_000, 45_000),
    }
    context.log.info(f"Security master updated: {data['total_securities']} securities")
    return data


@dg.asset_check(asset=security_master_data, description="Validates security master completeness")
def security_master_completeness(context: dg.AssetExecutionContext) -> dg.AssetCheckResult:
    passed = random.random() > 0.15
    if passed:
        return dg.AssetCheckResult(
            passed=True,
            metadata={
                "validation_time": datetime.now().isoformat(),
                "coverage": "99.8%",
            },
        )
    else:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            metadata={
                "validation_time": datetime.now().isoformat(),
                "error": "Missing critical security prices",
                "coverage": "94.2%",
            },
        )


@dg.asset(
    group_name="risk",
    tags={"tier": "tier-0", "criticality": "high"},
    description="Credit risk metrics and counterparty exposures",
    freshness_policy=dg.FreshnessPolicy.time_window(
        fail_window=timedelta(minutes=90),
        warn_window=timedelta(hours=1),
    ),
)
def credit_risk_data(context: dg.AssetExecutionContext) -> dict:
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_exposure": random.uniform(50_000_000, 200_000_000),
        "high_risk_counterparties": random.randint(0, 5),
    }
    context.log.info(f"Credit exposure: ${data['total_exposure']:,.2f}")
    return data


@dg.asset_check(asset=credit_risk_data, description="Validates credit risk calculations")
def credit_risk_limits(context: dg.AssetExecutionContext) -> dg.AssetCheckResult:
    passed = random.random() > 0.12
    if passed:
        return dg.AssetCheckResult(
            passed=True,
            metadata={
                "validation_time": datetime.now().isoformat(),
                "exposure_within_limits": True,
            },
        )
    else:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            metadata={
                "validation_time": datetime.now().isoformat(),
                "error": "Counterparty exposure exceeds limits",
            },
        )


# end_multiple_tier0_assets

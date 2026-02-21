"""Native Python asset checks covering all 7 data quality dimensions.

Data Quality Dimensions:
1. Accuracy - Data correctly represents real-world entities
2. Completeness - All required data is present
3. Consistency - Data is uniform across datasets
4. Timeliness - Data is up-to-date (see freshness.py)
5. Validity - Data conforms to formats and rules
6. Uniqueness - No unwanted duplicates
7. Integrity - Relationships between data are maintained
"""

import dagster as dg
import pandas as pd

from data_quality_patterns.defs.assets.raw_data import raw_customers, raw_orders
from data_quality_patterns.lib.quality_metrics import (
    calculate_completeness,
    calculate_uniqueness,
    calculate_validity,
)
from data_quality_patterns.lib.validators import (
    check_age_range,
    check_uniqueness,
    validate_email_format,
)

# ============================================================================
# ACCURACY CHECKS - Data correctly represents real-world entities
# ============================================================================


@dg.asset_check(asset=raw_customers, name="check_accuracy_names")
def check_accuracy_names(
    context: dg.AssetCheckExecutionContext,
    raw_customers: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that customer names appear to be real names (accuracy).

    Accuracy issues detected:
    - Placeholder names like "TEST USER", "N/A", "Unknown"
    - Generic names that may be fake data
    - Invalid patterns
    """
    suspicious_patterns = ["TEST", "XXXX", "N/A", "Unknown", "Placeholder"]

    suspicious_names = raw_customers["name"].apply(
        lambda x: (
            any(pattern in str(x).upper() for pattern in suspicious_patterns)
            if pd.notna(x)
            else False
        )
    )
    suspicious_count = suspicious_names.sum()
    total = len(raw_customers)

    if suspicious_count > 0:
        rate = suspicious_count / total
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description=f"Found {suspicious_count} records with suspicious names ({rate:.1%})",
            metadata={
                "suspicious_count": int(suspicious_count),
                "total_records": total,
                "examples": raw_customers[suspicious_names]["name"].head(5).tolist(),
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description="All customer names appear valid",
        metadata={"total_records": total},
    )


@dg.asset_check(asset=raw_customers, name="check_accuracy_age")
def check_accuracy_age(
    context: dg.AssetCheckExecutionContext,
    raw_customers: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that ages are within reasonable human range (accuracy).

    Valid age range: 0-120 years
    """
    invalid_records, warnings = check_age_range(
        raw_customers, "age", min_age=0, max_age=120, id_column="customer_id"
    )

    if not invalid_records.empty:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description=warnings[0]
            if warnings
            else f"Found {len(invalid_records)} records with invalid ages",
            metadata={
                "invalid_count": len(invalid_records),
                "invalid_ages": invalid_records["age"].tolist(),
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description="All ages within valid range (0-120)",
    )


# ============================================================================
# COMPLETENESS CHECKS - All required data is present
# ============================================================================


@dg.asset_check(asset=raw_customers, name="check_completeness_email")
def check_completeness_email(
    context: dg.AssetCheckExecutionContext,
    raw_customers: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that email addresses are present (completeness).

    Threshold: 95% of records must have email addresses.
    """
    completeness_rate = calculate_completeness(raw_customers, "email")
    threshold = 0.95
    missing_count = raw_customers["email"].isna().sum()

    if completeness_rate < threshold:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description=f"Email completeness {completeness_rate:.1%} below threshold {threshold:.0%}",
            metadata={
                "completeness_rate": float(completeness_rate),
                "missing_count": int(missing_count),
                "threshold": threshold,
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description=f"Email completeness acceptable: {completeness_rate:.1%}",
        metadata={"completeness_rate": float(completeness_rate)},
    )


@dg.asset_check(asset=raw_orders, name="check_completeness_amount")
def check_completeness_amount(
    context: dg.AssetCheckExecutionContext,
    raw_orders: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that order amounts are present (completeness)."""
    completeness_rate = calculate_completeness(raw_orders, "amount")
    threshold = 0.98
    missing_count = raw_orders["amount"].isna().sum()

    if completeness_rate < threshold:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description=f"Amount completeness {completeness_rate:.1%} below threshold {threshold:.0%}",
            metadata={
                "completeness_rate": float(completeness_rate),
                "missing_count": int(missing_count),
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description=f"Amount completeness acceptable: {completeness_rate:.1%}",
        metadata={"completeness_rate": float(completeness_rate)},
    )


# ============================================================================
# CONSISTENCY CHECKS - Data is uniform across datasets
# ============================================================================


@dg.asset_check(asset=raw_customers, name="check_consistency_region")
def check_consistency_region(
    context: dg.AssetCheckExecutionContext,
    raw_customers: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that region codes use consistent format (consistency).

    Valid regions: US, EU, APAC, LATAM
    Invalid: USA, Europe, Asia-Pacific, LA (inconsistent naming)
    """
    valid_regions = {"US", "EU", "APAC", "LATAM"}
    actual_regions = set(raw_customers["region"].dropna().unique())
    invalid_regions = actual_regions - valid_regions

    if invalid_regions:
        invalid_count = raw_customers["region"].isin(invalid_regions).sum()
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description=f"Found {len(invalid_regions)} non-standard region codes",
            metadata={
                "invalid_regions": list(invalid_regions),
                "valid_regions": list(valid_regions),
                "invalid_record_count": int(invalid_count),
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description="All region codes use consistent format",
        metadata={"regions_found": list(actual_regions)},
    )


# ============================================================================
# VALIDITY CHECKS - Data conforms to formats and rules
# ============================================================================


@dg.asset_check(asset=raw_customers, name="check_validity_email")
def check_validity_email(
    context: dg.AssetCheckExecutionContext,
    raw_customers: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that email addresses have valid format (validity)."""
    validity_rate = calculate_validity(raw_customers, "email")
    threshold = 0.90

    invalid_records, errors = validate_email_format(raw_customers, "email")

    if validity_rate < threshold:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description=errors[0]
            if errors
            else f"Email validity {validity_rate:.1%} below threshold {threshold:.0%}",
            metadata={
                "validity_rate": float(validity_rate),
                "invalid_count": len(invalid_records),
                "examples": invalid_records["email"].head(5).tolist()
                if not invalid_records.empty
                else [],
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description=f"Email validity acceptable: {validity_rate:.1%}",
        metadata={"validity_rate": float(validity_rate)},
    )


@dg.asset_check(asset=raw_orders, name="check_validity_amount")
def check_validity_amount(
    context: dg.AssetCheckExecutionContext,
    raw_orders: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that order amounts are positive (validity)."""
    amounts = raw_orders["amount"].dropna()
    negative_amounts = amounts[amounts < 0]

    if len(negative_amounts) > 0:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description=f"Found {len(negative_amounts)} orders with negative amounts",
            metadata={
                "negative_count": len(negative_amounts),
                "examples": [float(x) for x in negative_amounts.head(5).tolist()],
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description="All order amounts are non-negative",
    )


# ============================================================================
# UNIQUENESS CHECKS - No unwanted duplicates
# ============================================================================


@dg.asset_check(asset=raw_customers, name="check_uniqueness_customer_id")
def check_uniqueness_customer_id(
    context: dg.AssetCheckExecutionContext,
    raw_customers: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that customer IDs are unique (uniqueness)."""
    uniqueness_rate = calculate_uniqueness(raw_customers, "customer_id")
    duplicate_records, errors = check_uniqueness(raw_customers, ["customer_id"])

    if not duplicate_records.empty:
        duplicate_ids = duplicate_records["customer_id"].unique().tolist()
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description=errors[0]
            if errors
            else f"Found {len(duplicate_ids)} duplicate customer IDs",
            metadata={
                "uniqueness_rate": float(uniqueness_rate),
                "duplicate_ids": duplicate_ids[:10],  # First 10
                "total_duplicate_records": len(duplicate_records),
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description="All customer IDs are unique",
        metadata={"uniqueness_rate": float(uniqueness_rate)},
    )


@dg.asset_check(asset=raw_orders, name="check_uniqueness_order_id")
def check_uniqueness_order_id(
    context: dg.AssetCheckExecutionContext,
    raw_orders: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that order IDs are unique (uniqueness)."""
    uniqueness_rate = calculate_uniqueness(raw_orders, "order_id")
    duplicate_records, errors = check_uniqueness(raw_orders, ["order_id"])

    if not duplicate_records.empty:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description=errors[0] if errors else "Found duplicate order IDs",
            metadata={
                "uniqueness_rate": float(uniqueness_rate),
                "duplicate_count": len(duplicate_records),
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description="All order IDs are unique",
        metadata={"uniqueness_rate": float(uniqueness_rate)},
    )


# ============================================================================
# INTEGRITY CHECKS - Relationships between data are maintained
# ============================================================================


@dg.asset_check(
    asset=raw_orders,
    name="check_integrity_customer_ref",
    additional_ins={"raw_customers": dg.AssetIn("raw_customers")},
)
def check_integrity_customer_ref(
    context: dg.AssetCheckExecutionContext,
    raw_orders: pd.DataFrame,
    raw_customers: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Check that all order customer_ids reference valid customers (integrity).

    This validates referential integrity between orders and customers.
    """
    valid_customer_ids = set(raw_customers["customer_id"].unique())
    order_customer_ids = set(raw_orders["customer_id"].unique())

    invalid_refs = order_customer_ids - valid_customer_ids

    if invalid_refs:
        invalid_count = raw_orders["customer_id"].isin(invalid_refs).sum()
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description=f"Found {len(invalid_refs)} invalid customer references",
            metadata={
                "invalid_customer_ids": list(invalid_refs)[:10],
                "invalid_order_count": int(invalid_count),
                "total_orders": len(raw_orders),
            },
        )

    return dg.AssetCheckResult(
        passed=True,
        description="All orders reference valid customers",
        metadata={"unique_customers_referenced": len(order_customer_ids)},
    )

"""Great Expectations asset checks covering multiple quality dimensions.

This module uses Great Expectations to validate data quality
across multiple dimensions:
- Uniqueness: expect_column_values_to_be_unique
- Completeness: expect_column_values_to_not_be_null
- Validity: expect_column_values_to_match_regex
- Consistency: expect_column_values_to_be_in_set
- Accuracy: expect_column_values_to_be_between
"""

import dagster as dg
import pandas as pd

from data_quality_patterns.defs.assets.raw_data import raw_products
from data_quality_patterns.lib.expectations import GE_AVAILABLE, create_ge_dataset


@dg.asset_check(asset=raw_products, name="ge_check_sku_unique")
def ge_check_sku_unique(
    context: dg.AssetCheckExecutionContext,
    raw_products: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Great Expectations check: SKU values are unique."""
    if not GE_AVAILABLE:
        return dg.AssetCheckResult(
            passed=True,
            severity=dg.AssetCheckSeverity.WARN,
            description="Great Expectations not installed, skipping check",
        )

    ge_df = create_ge_dataset(raw_products)
    if ge_df is None:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description="Failed to create Great Expectations dataset",
        )

    result = ge_df.expect_column_values_to_be_unique("sku")

    if result["success"]:
        return dg.AssetCheckResult(
            passed=True,
            description="All SKU values are unique",
        )

    return dg.AssetCheckResult(
        passed=False,
        severity=dg.AssetCheckSeverity.ERROR,
        description="Duplicate SKU values found",
        metadata={
            "unexpected_count": result["result"].get("unexpected_count", 0),
            "unexpected_percent": result["result"].get("unexpected_percent", 0),
        },
    )


@dg.asset_check(asset=raw_products, name="ge_check_name_not_null")
def ge_check_name_not_null(
    context: dg.AssetCheckExecutionContext,
    raw_products: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Great Expectations check: Product names are not null (completeness)."""
    if not GE_AVAILABLE:
        return dg.AssetCheckResult(
            passed=True,
            severity=dg.AssetCheckSeverity.WARN,
            description="Great Expectations not installed, skipping check",
        )

    ge_df = create_ge_dataset(raw_products)
    if ge_df is None:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description="Failed to create Great Expectations dataset",
        )

    result = ge_df.expect_column_values_to_not_be_null("name")

    if result["success"]:
        return dg.AssetCheckResult(
            passed=True,
            description="All product names are present",
        )

    return dg.AssetCheckResult(
        passed=False,
        severity=dg.AssetCheckSeverity.ERROR,
        description="Missing product names found",
        metadata={
            "unexpected_count": result["result"].get("unexpected_count", 0),
        },
    )


@dg.asset_check(asset=raw_products, name="ge_check_price_positive")
def ge_check_price_positive(
    context: dg.AssetCheckExecutionContext,
    raw_products: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Great Expectations check: Prices are positive (validity/accuracy)."""
    if not GE_AVAILABLE:
        return dg.AssetCheckResult(
            passed=True,
            severity=dg.AssetCheckSeverity.WARN,
            description="Great Expectations not installed, skipping check",
        )

    ge_df = create_ge_dataset(raw_products)
    if ge_df is None:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description="Failed to create Great Expectations dataset",
        )

    result = ge_df.expect_column_values_to_be_between(
        "price", min_value=0.01, max_value=10000, mostly=0.9
    )

    if result["success"]:
        return dg.AssetCheckResult(
            passed=True,
            description="Product prices within valid range",
        )

    return dg.AssetCheckResult(
        passed=False,
        severity=dg.AssetCheckSeverity.ERROR,
        description="Invalid prices found (negative, zero, or extremely high)",
        metadata={
            "unexpected_count": result["result"].get("unexpected_count", 0),
        },
    )


@dg.asset_check(asset=raw_products, name="ge_check_category_valid")
def ge_check_category_valid(
    context: dg.AssetCheckExecutionContext,
    raw_products: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Great Expectations check: Categories are from valid set (consistency)."""
    if not GE_AVAILABLE:
        return dg.AssetCheckResult(
            passed=True,
            severity=dg.AssetCheckSeverity.WARN,
            description="Great Expectations not installed, skipping check",
        )

    ge_df = create_ge_dataset(raw_products)
    if ge_df is None:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description="Failed to create Great Expectations dataset",
        )

    valid_categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
    result = ge_df.expect_column_values_to_be_in_set("category", valid_categories)

    if result["success"]:
        return dg.AssetCheckResult(
            passed=True,
            description="All categories are valid",
        )

    return dg.AssetCheckResult(
        passed=False,
        severity=dg.AssetCheckSeverity.WARN,
        description="Invalid categories found",
        metadata={
            "unexpected_values": result["result"].get("unexpected_list", [])[:5],
        },
    )

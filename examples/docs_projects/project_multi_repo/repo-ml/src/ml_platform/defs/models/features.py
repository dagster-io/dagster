import os
from pathlib import Path

import numpy as np
import pandas as pd
from dagster import AssetKey, asset

# Simple shared file system approach - no IO managers needed
SHARED_DATA_PATH = Path(
    os.getenv("SHARED_ASSETS_PATH", "~/Documents/dagster_shared_assets")
).expanduser()


# start_load_external_asset
def load_external_asset(asset_name: str) -> pd.DataFrame:
    """Simple utility to load external assets from shared storage."""
    file_path = SHARED_DATA_PATH / f"{asset_name}.parquet"
    if not file_path.exists():
        raise FileNotFoundError(f"External asset {asset_name} not found at {file_path}")
    return pd.read_parquet(file_path)


# end_load_external_asset


# start_customer_features
@asset(
    deps=[AssetKey("customer_order_summary")],  # Just declares dependency
    group_name="ml_features",
)
def customer_features() -> pd.DataFrame:
    """Features for customer behavior prediction models."""
    # Load external asset manually - simple and explicit
    customer_order_summary = load_external_asset("customer_order_summary")

    features = customer_order_summary.copy()

    # Calculate days since last order (simulated current date)
    current_date = pd.Timestamp("2023-07-15")
    features["days_since_last_order"] = (
        current_date - pd.to_datetime(features["last_order"])
    ).dt.days
    features["days_since_first_order"] = (
        current_date - pd.to_datetime(features["first_order"])
    ).dt.days

    # Create feature ratios
    features["order_frequency"] = (
        features["total_orders"] / (features["days_since_first_order"] + 1) * 30
    )  # orders per month

    # One-hot encode tier
    features["is_premium"] = (features["tier"] == "premium").astype(int)

    # Create RFM-style features (Recency, Frequency, Monetary)
    features["recency_score"] = pd.cut(features["days_since_last_order"], bins=3, labels=[3, 2, 1])
    features["frequency_score"] = pd.cut(features["total_orders"], bins=3, labels=[1, 2, 3])
    features["monetary_score"] = pd.cut(features["total_spent"], bins=3, labels=[1, 2, 3])

    # Convert scores to numeric
    features["recency_score"] = features["recency_score"].astype(int)
    features["frequency_score"] = features["frequency_score"].astype(int)
    features["monetary_score"] = features["monetary_score"].astype(int)

    # Select final feature columns
    feature_columns = [
        "customer_id",
        "total_orders",
        "total_spent",
        "avg_order_value",
        "days_since_last_order",
        "days_since_first_order",
        "order_frequency",
        "is_premium",
        "recency_score",
        "frequency_score",
        "monetary_score",
    ]

    return features[feature_columns]


# end_customer_features


# start_cross_repo_dependency
@asset(
    deps=[AssetKey("product_performance")],  # Just declares dependency
    group_name="ml_features",
)
def product_features() -> pd.DataFrame:
    """Features for product recommendation and demand forecasting models."""
    # Load external asset manually - simple and explicit
    product_performance = load_external_asset("product_performance")

    features = product_performance.copy()

    # Calculate velocity metrics
    features["revenue_per_order"] = features["revenue"] / features["orders"]
    features["units_per_order"] = features["units_sold"] / features["orders"]

    # Create category encoding
    category_dummies = pd.get_dummies(features["category"], prefix="category")
    features = pd.concat([features, category_dummies], axis=1)

    # Calculate performance percentiles
    features["revenue_percentile"] = features["revenue"].rank(pct=True)
    features["profit_percentile"] = features["profit"].rank(pct=True)
    features["units_percentile"] = features["units_sold"].rank(pct=True)

    # Create performance tiers
    def performance_tier(row):
        if row["revenue_percentile"] >= 0.8 and row["profit_percentile"] >= 0.8:
            return "high_performer"
        elif row["revenue_percentile"] >= 0.5 and row["profit_percentile"] >= 0.5:
            return "medium_performer"
        else:
            return "low_performer"

    features["performance_tier"] = features.apply(performance_tier, axis=1)

    return features


# end_cross_repo_dependency


@asset(group_name="ml_features")
def synthetic_market_data() -> pd.DataFrame:
    """Synthetic market and seasonal data for ML models."""
    # Create synthetic market data
    np.random.seed(42)

    dates = pd.date_range("2023-01-01", "2023-07-15", freq="D")
    n_days = len(dates)

    # Create seasonal patterns
    day_of_year = dates.dayofyear
    seasonal_trend = np.sin(2 * np.pi * day_of_year / 365.25)

    # Create weekly patterns
    day_of_week = dates.dayofweek
    weekend_effect = np.where(day_of_week >= 5, 1.2, 1.0)  # Weekend boost

    # Generate synthetic metrics
    data = {
        "date": dates,
        "market_index": 100 + np.cumsum(np.random.normal(0, 1, n_days)) + seasonal_trend * 10,
        "competitor_price_index": 100 + np.cumsum(np.random.normal(0, 0.5, n_days)),
        "seasonal_factor": seasonal_trend,
        "weekend_factor": weekend_effect,
        "advertising_spend": np.random.gamma(2, 50, n_days) * weekend_effect,
        "economic_confidence": 50 + np.random.normal(0, 5, n_days) + seasonal_trend * 5,
    }

    df = pd.DataFrame(data)
    return df

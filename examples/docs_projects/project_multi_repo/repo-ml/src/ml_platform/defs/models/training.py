import numpy as np
import pandas as pd
from dagster import AssetIn, asset
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


# start_customer_churn_model
@asset(ins={"customer_features": AssetIn()}, group_name="ml_models")
def customer_churn_model(customer_features: pd.DataFrame) -> dict:
    """Train a model to predict customer churn based on behavior."""
    # Create synthetic churn labels for demonstration
    # In reality, this would come from historical data
    np.random.seed(42)

    # Create churn probability based on recency and monetary scores
    churn_prob = (
        (5 - customer_features["recency_score"]) * 0.3  # Higher recency = more likely to churn
        + (4 - customer_features["monetary_score"]) * 0.2  # Lower spending = more likely to churn
        + (customer_features["days_since_last_order"] > 60) * 0.4  # Long time since last order
        + np.random.random(len(customer_features)) * 0.1  # Add some randomness
    )

    # Convert to binary labels
    y = (churn_prob > 0.5).astype(int)

    # Ensure we have both classes in the data (fix for small datasets)
    unique_classes = np.unique(y)
    if len(unique_classes) < 2:
        # If all samples are the same class, artificially create some diversity
        if unique_classes[0] == 0:
            # All no-churn, make some churn
            y[np.random.choice(len(y), size=max(1, len(y) // 4), replace=False)] = 1
        else:
            # All churn, make some no-churn
            y[np.random.choice(len(y), size=max(1, len(y) // 4), replace=False)] = 0

    # Select features for model
    feature_cols = [
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

    X = customer_features[feature_cols]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Make predictions
    y_pred = model.predict(X_test)

    # Calculate metrics - with safe error handling
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # Feature importance
    feature_importance = dict(zip(feature_cols, model.feature_importances_))

    # Safe metric extraction
    model_results = {
        "model": model,
        "accuracy": report.get("accuracy", 0.0),
        "precision": report.get("1", {}).get("precision", 0.0),
        "recall": report.get("1", {}).get("recall", 0.0),
        "f1_score": report.get("1", {}).get("f1-score", 0.0),
        "feature_importance": feature_importance,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "classes_learned": list(model.classes_),
        "class_distribution": dict(zip(*np.unique(y, return_counts=True))),
    }

    return model_results


# end_customer_churn_model


# start_demand_forecast_model
@asset(ins={"product_features": AssetIn()}, group_name="ml_models")
def demand_forecast_model(product_features: pd.DataFrame) -> dict:
    """Train a model to forecast product demand."""
    # Create synthetic demand data for demonstration
    np.random.seed(42)

    # Base demand influenced by various factors
    base_demand = (
        product_features["units_sold"] * 0.7  # Historical sales
        + product_features["profit_percentile"] * 20  # Profitability
        + (product_features["performance_tier"] == "high_performer") * 15  # Performance tier
        + np.random.normal(0, 5, len(product_features))  # Random noise
    ).clip(0, None)  # No negative demand

    # Select features for model
    feature_cols = [
        "orders",
        "units_sold",
        "revenue",
        "profit_margin",
        "revenue_per_order",
        "units_per_order",
        "revenue_percentile",
        "profit_percentile",
        "units_percentile",
    ]

    # Add category features (one-hot encoded)
    category_cols = [col for col in product_features.columns if col.startswith("category_")]
    feature_cols.extend(category_cols)

    X = product_features[feature_cols]
    y = base_demand

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Make predictions
    y_pred = model.predict(X_test)

    # Calculate metrics
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Feature importance
    feature_importance = dict(zip(feature_cols, model.feature_importances_))

    model_results = {
        "model": model,
        "mse": mse,
        "rmse": np.sqrt(mse),
        "r2_score": r2,
        "feature_importance": feature_importance,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "mean_actual_demand": float(y_test.mean()),
        "mean_predicted_demand": float(y_pred.mean()),
    }

    return model_results


# end_demand_forecast_model


# start_customer_risk_scores
@asset(
    ins={"customer_churn_model": AssetIn(), "customer_features": AssetIn()},
    group_name="ml_predictions",
)
def customer_risk_scores(
    customer_churn_model: dict, customer_features: pd.DataFrame
) -> pd.DataFrame:
    """Generate churn risk scores for all customers."""
    model = customer_churn_model["model"]

    # Select same features used in training
    feature_cols = [
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

    X = customer_features[feature_cols]

    # Get churn probabilities - safe prediction handling
    proba = model.predict_proba(X)
    if proba.shape[1] == 2:
        churn_probabilities = proba[:, 1]  # Get positive class probability
    else:
        # Only one class learned - use appropriate probability
        churn_probabilities = proba[:, 0] if model.classes_[0] == 1 else 1 - proba[:, 0]

    # Create risk scores dataframe
    risk_scores = customer_features[["customer_id"]].copy()
    risk_scores["churn_probability"] = churn_probabilities
    risk_scores["risk_tier"] = pd.cut(
        churn_probabilities,
        bins=[0, 0.3, 0.7, 1.0],
        labels=["Low Risk", "Medium Risk", "High Risk"],
    )

    # Add recommendations
    def get_recommendation(row):
        if row["risk_tier"] == "High Risk":
            return "Immediate intervention needed - contact customer"
        elif row["risk_tier"] == "Medium Risk":
            return "Send targeted retention offer"
        else:
            return "Continue normal engagement"

    risk_scores["recommendation"] = risk_scores.apply(get_recommendation, axis=1)

    return risk_scores


# end_customer_risk_scores


@asset(
    ins={"demand_forecast_model": AssetIn(), "product_features": AssetIn()},
    group_name="ml_predictions",
)
def product_demand_forecasts(
    demand_forecast_model: dict, product_features: pd.DataFrame
) -> pd.DataFrame:
    """Generate demand forecasts for all products."""
    model = demand_forecast_model["model"]

    # Select same features used in training
    feature_cols = [
        "orders",
        "units_sold",
        "revenue",
        "profit_margin",
        "revenue_per_order",
        "units_per_order",
        "revenue_percentile",
        "profit_percentile",
        "units_percentile",
    ]

    # Add category features
    category_cols = [col for col in product_features.columns if col.startswith("category_")]
    feature_cols.extend(category_cols)

    X = product_features[feature_cols]

    # Generate forecasts
    forecasted_demand = model.predict(X)

    # Create forecasts dataframe
    forecasts = product_features[["product"]].copy()
    forecasts["current_demand"] = product_features["units_sold"]
    forecasts["forecasted_demand"] = forecasted_demand.round(0)
    forecasts["demand_change"] = forecasts["forecasted_demand"] - forecasts["current_demand"]
    forecasts["demand_change_pct"] = (
        forecasts["demand_change"] / forecasts["current_demand"] * 100
    ).round(1)

    # Add recommendations
    def get_inventory_recommendation(row):
        if row["demand_change_pct"] > 20:
            return "Increase inventory - high demand growth expected"
        elif row["demand_change_pct"] < -20:
            return "Reduce inventory - demand decline expected"
        else:
            return "Maintain current inventory levels"

    forecasts["inventory_recommendation"] = forecasts.apply(get_inventory_recommendation, axis=1)

    return forecasts

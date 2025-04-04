import statistics
from datetime import datetime
from typing import Any

import jsonschema
import numpy as np
import pandas as pd
from dagster import (
    AssetCheckResult,
    AssetKey,
    DagsterEventType,
    EventRecordsFilter,
    FreshnessPolicy,
    MetadataValue,
    asset_check,
    build_column_schema_change_checks,
)
from git import Optional
from sklearn.linear_model import LinearRegression

# Schema for validating check DSL entries
CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "asset": {"type": "string"},
        "check_name": {"type": "string"},
        "type": {"type": "string"},
        "metric": {"type": "string"},
        "min": {"type": "number"},
        "max": {"type": "number"},
        "threshold": {"type": "number"},
        "threshold_pct": {"type": "number"},
        "confidence": {"type": "number"},
        "history": {"type": "integer"},
        "where": {"type": "string"},
        "group_by": {"type": "string"},
        "allowed_failures": {"type": "integer"},
        "assets": {"type": "array", "items": {"type": "string"}},
        "maximum_lag_minutes": {"type": "number"},
        "maximum_lag_minutes_by_partition": {"type": "number"},
    },
    "required": ["type"],
}


# Utility to validate a single check config
def validate_check_config(config: dict[str, Any]) -> None:
    jsonschema.validate(instance=config, schema=CHECK_SCHEMA)


# Function to handle schema_change check from YAML
def handle_schema_change_check(check: dict[str, Any]) -> list:
    seen = set()
    unique_asset_keys = []
    for asset in check.get("assets", []):
        key = tuple(asset.split("."))
        if key not in seen:
            seen.add(key)
            unique_asset_keys.append(AssetKey(key))

    return build_column_schema_change_checks(assets=unique_asset_keys)  # type: ignore (probably a bug)


# Function to handle freshness checks from YAML
def handle_freshness_check(check: dict):
    checks = []
    assets = check.get("assets", [])

    for asset in assets:
        asset_key = AssetKey(asset.split("."))

        if "maximum_lag_minutes" in check:
            policy = FreshnessPolicy(maximum_lag_minutes=check["maximum_lag_minutes"])
            safe_name = f"{'_'.join(asset_key.path)}_freshness_check"

            @asset_check(asset=asset_key, name=safe_name)
            def freshness_check(context, _):
                # Dagster will evaluate freshness policy behind the scenes
                return context.freshness_policy_evaluation_result().as_asset_check_result()

            checks.append(freshness_check)

        if "maximum_lag_minutes_by_partition" in check:
            policy = FreshnessPolicy(  # noqa
                maximum_lag_minutes=check["maximum_lag_minutes_by_partition"],
                cron_schedule="* * * * *",
            )  # cron required for partition
            safe_name = f"{'_'.join(asset_key.path)}_partition_freshness_check"

            @asset_check(asset=asset_key, name=safe_name)
            def partition_freshness_check(context, _):
                return context.freshness_policy_evaluation_result().as_asset_check_result()

            checks.append(partition_freshness_check)

    return checks


# Utility to apply optional where and group_by filtering
def apply_filters(
    df: pd.DataFrame, where: Optional[str] = None, group_by: Optional[str] = None
) -> dict[str, pd.DataFrame]:
    if where:
        df = df.query(where)
    if group_by:
        return dict(tuple(df.groupby(group_by)))  # type: ignore (probably a bug)
    return {"__all__": df}


# Evaluation logic for non-grouped checks


def evaluate_anomaly_detection(
    context, asset: str, metric: str, history: int, threshold: float, latest_value: float
) -> AssetCheckResult:
    records = context.instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
            asset_key=AssetKey(asset),
        ),
        limit=history,
    )
    historical_values = []
    for record in records:
        check_result = record.asset_check_evaluation
        if metric in check_result.metadata:
            historical_values.append(check_result.metadata[metric].value)

    if len(historical_values) < history:
        return AssetCheckResult(
            passed=True, metadata={"note": "Not enough history", metric: latest_value}
        )

    mean = statistics.mean(historical_values)
    stdev = statistics.stdev(historical_values)
    passed = abs(latest_value - mean) < threshold * stdev

    return AssetCheckResult(
        passed=passed,
        metadata={"mean": mean, "stdev": stdev, "latest": latest_value, "threshold": threshold},
    )


def evaluate_static_threshold(
    latest_value: float, min_value: Optional[float] = None, max_value: Optional[float] = None
) -> AssetCheckResult:
    passed = True

    latest_value_metadata = None

    if isinstance(latest_value, datetime):
        latest_value_metadata = MetadataValue.timestamp(latest_value)
    else:
        latest_value_metadata = float(latest_value)  # For numeric consistency

    if isinstance(latest_value_metadata, pd.Timestamp):
        latest_value_metadata = latest_value_metadata.to_pydatetime()

    if isinstance(min_value, str):
        min_value_metadata = datetime.fromisoformat(min_value)
    else:
        min_value_metadata = min_value

    if isinstance(max_value, str):
        max_value_metadata = datetime.fromisoformat(max_value)
    else:
        max_value_metadata = max_value

    if min_value is not None and latest_value < min_value:
        passed = False
    if max_value is not None and latest_value > max_value:
        passed = False
    return AssetCheckResult(
        passed=passed,
        metadata={
            "min_threshold": min_value_metadata,
            "max_threshold": max_value_metadata,
            "latest": latest_value_metadata,
        },
    )


def evaluate_percent_delta(
    context, asset: str, metric: str, threshold_pct: float, latest_value: float
) -> AssetCheckResult:
    records = context.instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
            asset_key=AssetKey(asset),
        ),
        limit=1,
    )
    if not records:
        return AssetCheckResult(
            passed=True, metadata={"note": "No prior value", metric: latest_value}
        )

    prev_value = records[0].asset_check_evaluation.metadata.get(metric)
    delta_pct = (
        abs(latest_value - prev_value) / prev_value * 100 if prev_value != 0 else float("inf")
    )
    passed = delta_pct <= threshold_pct
    return AssetCheckResult(
        passed=passed,
        metadata={
            "previous": prev_value,
            "latest": latest_value,
            "delta_pct": delta_pct,
            "threshold_pct": threshold_pct,
        },
    )


def evaluate_prediction_check(
    context, asset: str, metric: str, history: int, confidence: float, latest_value: float
) -> AssetCheckResult:
    records = context.instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
            asset_key=AssetKey(asset),
        ),
        limit=history,
    )
    values = []
    for record in records:
        check_result = record.asset_check_evaluation
        if metric in check_result.metadata:
            values.append(check_result.metadata[metric].value)

    if len(values) < history:
        return AssetCheckResult(
            passed=True, metadata={"note": "Not enough history", metric: latest_value}
        )

    # Train simple regression model on time series
    X = np.arange(len(values)).reshape(-1, 1)
    y = np.array(values)
    model = LinearRegression().fit(X, y)

    # Predict next value
    next_index = np.array([[len(values)]])
    prediction = model.predict(next_index)[0]
    stdev = statistics.stdev(values)
    z = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence, 1.96)
    lower = prediction - z * stdev
    upper = prediction + z * stdev
    passed = lower <= latest_value <= upper

    return AssetCheckResult(
        passed=passed,
        metadata={
            "predicted": prediction,
            "lower": lower,
            "upper": upper,
            "latest": latest_value,
            "confidence": confidence,
        },
    )


def compute_group_metric(df: pd.DataFrame, metric: str) -> Optional[float]:
    import re

    if metric == "num_rows":
        return len(df)

    if ":" not in metric:
        raise ValueError(f"Unsupported metric format: {metric}")

    metric_type, column = metric.split(":", 1)

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataframe")

    if metric_type == "mean":
        return df[column].mean()
    elif metric_type == "median":
        return df[column].median()
    elif metric_type == "mode":
        return df[column].mode().iloc[0] if not df[column].mode().empty else None
    elif metric_type == "sum":
        return df[column].sum()
    elif metric_type == "min":
        return df[column].min()
    elif metric_type == "max":
        return df[column].max()
    elif metric_type == "stddev":
        return df[column].std()
    elif metric_type == "variance":
        return df[column].var()  # type: ignore (probably a bug)
    elif metric_type == "range":
        return df[column].max() - df[column].min()
    elif metric_type == "distinct_count":
        return df[column].nunique()
    elif metric_type == "null_pct":
        return df[column].isnull().mean() * 100
    elif metric_type == "empty_string_pct":
        return (df[column] == "").mean() * 100
    elif metric_type == "zero_pct":
        return (df[column] == 0).mean() * 100
    elif metric_type == "positive_pct":
        return (df[column] > 0).mean() * 100
    elif metric_type == "negative_pct":
        return (df[column] < 0).mean() * 100
    elif metric_type == "max_length":
        return df[column].astype(str).map(len).max()
    elif metric_type == "min_length":
        return df[column].astype(str).map(len).min()
    elif metric_type == "avg_length":
        return df[column].astype(str).map(len).mean()
    elif metric_type == "pattern_match_pct":
        pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")  # default to email
        return df[column].astype(str).map(lambda x: bool(pattern.match(x))).mean() * 100
    elif metric_type == "duplicate_pct":
        return (df[column].duplicated(keep=False)).mean() * 100
    else:
        raise ValueError(f"Unsupported metric type: {metric_type}")


def evaluate_grouped_static_threshold(
    df_map: dict[str, pd.DataFrame],
    metric: str,
    min_value: float,
    max_value: float,
    allowed_failures: int,
) -> AssetCheckResult:
    failures = []
    metadata = {}

    for group_key, df in df_map.items():
        value = compute_group_metric(df, metric)

        passed = True
        if (min_value is not None and value is not None) and value < min_value:
            passed = False
        if (max_value is not None and value is not None) and value > max_value:
            passed = False

        metadata[group_key] = {
            "value": value,
            "min_threshold": min_value,
            "max_threshold": max_value,
            "passed": passed,
        }

        if not passed:
            failures.append(group_key)

    passed = len(failures) <= allowed_failures
    return AssetCheckResult(
        passed=passed,
        metadata={
            "group_results": metadata,
            "failures": failures,
            "allowed_failures": allowed_failures,
        },
    )


def evaluate_grouped_percent_delta(
    context,
    asset: str,
    df_map: dict[str, pd.DataFrame],
    metric: str,
    threshold_pct: float,
    allowed_failures: int,
) -> AssetCheckResult:
    failures = []
    metadata = {}

    for group_key, df in df_map.items():
        latest_value = compute_group_metric(df, metric)

        records = context.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
                asset_key=AssetKey(asset),
            ),
            limit=1,
        )

        if not records:
            continue

        prev_value = records[0].asset_check_evaluation.metadata.get(group_key, {}).get("value")
        if prev_value is None:
            continue

        delta_pct = (
            abs(latest_value - prev_value) / prev_value * 100 if prev_value != 0 else float("inf")
        )
        passed = delta_pct <= threshold_pct

        metadata[group_key] = {
            "previous": prev_value,
            "latest": latest_value,
            "delta_pct": delta_pct,
            "passed": passed,
        }

        if not passed:
            failures.append(group_key)

    passed = len(failures) <= allowed_failures
    return AssetCheckResult(
        passed=passed,
        metadata={
            "group_results": metadata,
            "failures": failures,
            "allowed_failures": allowed_failures,
        },
    )


def evaluate_grouped_prediction_check(
    context,
    asset: str,
    df_map: dict[str, pd.DataFrame],
    metric: str,
    history: int,
    confidence: float,
    allowed_failures: int,
) -> AssetCheckResult:
    failures = []
    metadata = {}
    z = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence, 1.96)

    for group_key, df in df_map.items():
        value = compute_group_metric(df, metric)

        # Fetch historical values for this group/metric
        records = context.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
                asset_key=AssetKey(asset),
            ),
            limit=history,
        )
        values = []
        for record in records:
            check_result = record.asset_check_evaluation
            if group_key in check_result.metadata and metric in check_result.metadata[group_key]:
                values.append(check_result.metadata[group_key][metric])

        if len(values) < history:
            continue

        # ML prediction with Linear Regression
        X = np.arange(len(values)).reshape(-1, 1)
        y = np.array(values)
        model = LinearRegression().fit(X, y)
        next_index = np.array([[len(values)]])
        prediction = model.predict(next_index)[0]
        stdev = statistics.stdev(values)
        lower = prediction - z * stdev
        upper = prediction + z * stdev
        passed = lower <= value <= upper

        metadata[group_key] = {
            "predicted": prediction,
            "lower": lower,
            "upper": upper,
            "latest": value,
            "passed": passed,
        }
        if not passed:
            failures.append(group_key)

    passed = len(failures) <= allowed_failures
    return AssetCheckResult(
        passed=passed,
        metadata={
            "group_results": metadata,
            "failures": failures,
            "allowed_failures": allowed_failures,
        },
    )


def evaluate_grouped_anomaly_detection(
    context,
    asset: str,
    df_map: dict[str, pd.DataFrame],
    metric: str,
    threshold: float,
    history: int,
    allowed_failures: int,
) -> AssetCheckResult:
    failures = []
    metadata = {}

    for group_key, df in df_map.items():
        latest_value = compute_group_metric(df, metric)

        records = context.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
                asset_key=AssetKey(asset),
            ),
            limit=history,
        )

        historical_values = []
        for record in records:
            check_result = record.asset_check_evaluation
            if group_key in check_result.metadata and metric in check_result.metadata[group_key]:
                historical_values.append(check_result.metadata[group_key][metric])

        if len(historical_values) < history:
            continue

        mean = statistics.mean(historical_values)
        stdev = statistics.stdev(historical_values)
        lower = mean - threshold * stdev
        upper = mean + threshold * stdev
        passed = lower <= latest_value <= upper

        metadata[group_key] = {
            "mean": mean,
            "stdev": stdev,
            "latest": latest_value,
            "lower": lower,
            "upper": upper,
            "passed": passed,
        }

        if not passed:
            failures.append(group_key)

    passed = len(failures) <= allowed_failures
    return AssetCheckResult(
        passed=passed,
        metadata={
            "group_results": metadata,
            "failures": failures,
            "allowed_failures": allowed_failures,
        },
    )


def evaluate_grouped_distribution_metric(
    context,
    asset: str,
    df_map: dict[str, pd.DataFrame],
    column: str,
    check_type: str,
    threshold: float,
    threshold_pct: float,
    confidence: float,
    history: int,
    allowed_failures: int,
) -> AssetCheckResult:
    import statistics

    from dagster import AssetCheckResult, AssetKey, DagsterEventType, EventRecordsFilter

    failures = []
    metadata = {}
    z = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence, 1.96)

    for group_key, df in df_map.items():
        current_dist = df[column].value_counts(normalize=True)

        records = context.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
                asset_key=AssetKey(asset),
            ),
            limit=history,
        )

        historical = []
        for record in records:
            check_result = record.asset_check_evaluation
            if group_key in check_result.metadata and column in check_result.metadata[group_key]:
                hist = check_result.metadata[group_key][column]
                if isinstance(hist, dict):
                    historical.append(pd.Series(hist))

        if not historical:
            continue

        avg_hist = sum(historical) / len(historical)
        all_keys = current_dist.index.union(avg_hist.index)  # type: ignore  (probably a bug)
        tvd = (
            current_dist.reindex(all_keys, fill_value=0) - avg_hist.reindex(all_keys, fill_value=0)  # type: ignore (probably a bug)
        ).abs().sum() / 2.0

        passed = True
        if check_type == "static_threshold":
            passed = tvd <= threshold
        elif check_type == "percent_delta":
            prev_tvd = historical[-1].sum() / 2.0
            pct_delta = abs(tvd - prev_tvd) / prev_tvd * 100 if prev_tvd != 0 else float("inf")
            passed = pct_delta <= threshold_pct
            metadata[group_key] = {"tvd": tvd, "pct_delta": pct_delta}
        elif check_type == "predicted_range":
            tvd_values = [s.sum() / 2.0 for s in historical]
            mean = statistics.mean(tvd_values)
            stdev = statistics.stdev(tvd_values) if len(tvd_values) > 1 else 0
            lower = mean - z * stdev
            upper = mean + z * stdev
            passed = lower <= tvd <= upper
            metadata[group_key] = {
                "tvd": tvd,
                "predicted_lower": lower,
                "predicted_upper": upper,
            }

        if not passed:
            failures.append(group_key)

        if group_key not in metadata:
            metadata[group_key] = {}
        metadata[group_key].update({"tvd": tvd, "distribution": current_dist.to_dict()})

    passed = len(failures) <= allowed_failures
    return AssetCheckResult(
        passed=passed,
        metadata={
            "failures": failures,
            "threshold": threshold,
            "tvd_by_group": metadata,
            "allowed_failures": allowed_failures,
        },
    )


def evaluate_grouped_check(
    context,
    asset: str,
    df_map: dict[str, pd.DataFrame],
    check_type: str,
    metric: str,
    history: int,
    threshold: float,
    threshold_pct: float,
    confidence: float,
    allowed_failures: int,
) -> AssetCheckResult:
    if metric.startswith("distribution_change:"):
        column = metric.split(":")[1]
        return evaluate_grouped_distribution_metric(
            context=context,
            asset=asset,
            df_map=df_map,
            column=column,
            check_type=check_type,
            threshold=threshold,
            threshold_pct=threshold_pct,
            confidence=confidence,
            history=history,
            allowed_failures=allowed_failures,
        )
    elif check_type == "static_threshold":
        return evaluate_grouped_static_threshold(
            df_map, metric, threshold, threshold, allowed_failures
        )
    elif check_type == "percent_delta":
        return evaluate_grouped_percent_delta(
            context, asset, df_map, metric, threshold_pct, allowed_failures
        )
    elif check_type == "predicted_range":
        return evaluate_grouped_prediction_check(
            context, asset, df_map, metric, history, confidence, allowed_failures
        )
    elif check_type == "anomaly_detection":
        return evaluate_grouped_anomaly_detection(
            context, asset, df_map, metric, threshold, history, allowed_failures
        )
    else:
        raise ValueError(f"Unsupported grouped check type: {check_type}")


# Automatically validated check generator
def generate_asset_check_function(parsed_check: dict[str, Any]):
    print(f"🔪 Registering check '{parsed_check['check_name']}' for asset: {parsed_check['asset']}")  # noqa: T201
    validate_check_config(parsed_check)

    asset = parsed_check["asset"]
    check_name = parsed_check["check_name"]
    metric = parsed_check["metric"]
    check_type = parsed_check.get("type", "anomaly_detection")
    history = parsed_check.get("history", 10)
    threshold = parsed_check.get("threshold", 2)
    min_value = parsed_check.get("min")
    max_value = parsed_check.get("max")
    threshold_pct = parsed_check.get("threshold_pct")
    confidence = parsed_check.get("confidence", 0.95)
    where = parsed_check.get("where")
    group_by = parsed_check.get("group_by")
    allowed_failures = parsed_check.get("allowed_failures", 0)
    pattern = parsed_check.get("pattern")

    print(f"📎 Registering check: {check_name}, AssetKey: {asset}")  # noqa: T201

    @asset_check(
        name=check_name, asset=AssetKey(asset.split(".")) if "." in asset else AssetKey(asset)
    )
    def dynamic_check(context, asset_data):
        df_map = apply_filters(asset_data, where=where, group_by=group_by)
        result = None
        value = None

        if group_by:
            result = evaluate_grouped_check(
                context=context,
                asset=asset,
                df_map=df_map,
                check_type=check_type,
                metric=metric,
                history=history,
                threshold=threshold,
                threshold_pct=threshold_pct,
                confidence=confidence,
                allowed_failures=allowed_failures,
            )
        else:
            if metric == "num_rows":
                value = len(asset_data)
            elif metric.startswith("null_pct:"):
                column = metric.split(":")[1]
                value = float(asset_data[column].isnull().mean() * 100)
            elif metric.startswith("min:"):
                column = metric.split(":")[1]
                value = asset_data[column].min()
                if isinstance(value, pd.Timestamp) and value.tzinfo is None:
                    value = value.tz_localize("UTC")
            elif metric.startswith("max:"):
                column = metric.split(":")[1]
                value = asset_data[column].max()
                if isinstance(value, pd.Timestamp) and value.tzinfo is None:
                    value = value.tz_localize("UTC")
            elif metric.startswith("mean:"):
                column = metric.split(":")[1]
                value = asset_data[column].mean()
            elif metric.startswith("sum:"):
                column = metric.split(":")[1]
                value = asset_data[column].sum()
            elif metric.startswith("stddev:"):
                column = metric.split(":")[1]
                value = asset_data[column].std()
            elif metric.startswith("variance:"):
                column = metric.split(":")[1]
                value = asset_data[column].var()
            elif metric.startswith("range:"):
                column = metric.split(":")[1]
                value = asset_data[column].max() - asset_data[column].min()
            elif metric.startswith("median:"):
                column = metric.split(":")[1]
                value = asset_data[column].median()
            elif metric.startswith("mode:"):
                column = metric.split(":")[1]
                mode_series = asset_data[column].mode()
                value = mode_series.iloc[0] if not mode_series.empty else None
            elif metric.startswith("empty_string_pct:"):
                column = metric.split(":")[1]
                total = len(asset_data)
                empty_count = asset_data[column].fillna("").eq("").sum()
                value = (empty_count / total) * 100 if total else 0
            elif metric.startswith("zero_pct:"):
                column = metric.split(":")[1]
                total = len(asset_data)
                zero_count = asset_data[column].fillna(0).eq(0).sum()
                value = (zero_count / total) * 100 if total else 0
            elif metric.startswith("positive_pct:"):
                column = metric.split(":")[1]
                total = len(asset_data)
                count = asset_data[column].gt(0).sum()
                value = (count / total) * 100 if total else 0
            elif metric.startswith("negative_pct:"):
                column = metric.split(":")[1]
                total = len(asset_data)
                count = asset_data[column].lt(0).sum()
                value = (count / total) * 100 if total else 0
            elif metric.startswith("max_length:"):
                column = metric.split(":")[1]
                value = int(asset_data[column].astype(str).str.len().max())
            elif metric.startswith("min_length:"):
                column = metric.split(":")[1]
                value = int(asset_data[column].astype(str).str.len().min())
            elif metric.startswith("avg_length:"):
                column = metric.split(":")[1]
                value = float(asset_data[column].astype(str).str.len().mean())
            elif metric.startswith("pattern_match_pct:"):
                column = metric.split(":")[1]
                if not pattern:
                    raise ValueError("pattern_match_pct requires a 'pattern' field in YAML.")
                total = len(asset_data)
                match_count = asset_data[column].astype(str).str.match(pattern).sum()
                value = (match_count / total) * 100 if total else 0
            elif metric.startswith("duplicate_pct:"):
                column = metric.split(":")[1]
                total = len(asset_data)
                duplicates = asset_data[column].duplicated(keep=False).sum()
                value = (duplicates / total) * 100 if total else 0
            elif metric.startswith("distribution_change:"):
                column = metric.split(":")[1]
                current_dist = asset_data[column].value_counts(normalize=True)
                records = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_CHECK_EVALUATION,
                        asset_key=AssetKey(asset.split(".")) if "." in asset else AssetKey(asset),
                    ),
                    limit=history,
                )
                historical = []
                for record in records:
                    check_result = record.asset_check_evaluation
                    if column in check_result.metadata:
                        hist = check_result.metadata[column].value
                        if isinstance(hist, dict):
                            historical.append(pd.Series(hist))
                if not historical:
                    value = 0.0
                else:
                    avg_hist = sum(historical) / len(historical)
                    all_keys = current_dist.index.union(avg_hist.index)
                    diff = (
                        current_dist.reindex(all_keys, fill_value=0)
                        - avg_hist.reindex(all_keys, fill_value=0)
                    ).abs()
                    value = diff.sum() / 2.0  # total variation distance
                context.log.info(f"[{check_name}] TVD (distribution change) = {value}")
                result = AssetCheckResult(
                    passed=True, metadata={column: current_dist.to_dict(), metric: value}
                )

            if result is None and value is not None:
                context.log.info(f"Evaluating {check_name} with value: {value}")
                if check_type == "anomaly_detection":
                    result = evaluate_anomaly_detection(
                        context, asset, metric, history, threshold, value
                    )
                elif check_type == "static_threshold":
                    result = evaluate_static_threshold(value, min_value, max_value)
                elif check_type == "percent_delta":
                    result = evaluate_percent_delta(context, asset, metric, threshold_pct, value)
                elif check_type == "predicted_range":
                    result = evaluate_prediction_check(
                        context, asset, metric, history, confidence, value
                    )
                else:
                    raise ValueError(f"Unsupported check type: {check_type}")

            if (
                result is not None
                and value is not None
                and not metric.startswith("distribution_change")
            ):
                if isinstance(value, pd.Timestamp):
                    if value.tzinfo is None:
                        value = value.tz_localize("UTC")
                    result.metadata[metric] = MetadataValue.timestamp(value)
                else:
                    # Before setting metadata
                    if (
                        result is not None
                        and value is not None
                        and not metric.startswith("distribution_change")
                    ):
                        if isinstance(value, pd.Timestamp):
                            result.metadata[metric] = MetadataValue.timestamp(value)
                        elif isinstance(value, (np.integer, np.floating)):
                            result.metadata[metric] = float(value)  # Cast to native Python float
                        else:
                            result.metadata[metric] = value

        return result

    print(f"✅ Finished defining check: {check_name}")  # noqa: T201
    return dynamic_check

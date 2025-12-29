"""Quality metrics calculation for data quality scoring."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd

from data_quality_patterns.lib.validators import EMAIL_PATTERN


@dataclass
class QualityMetrics:
    """Data quality metrics for a dataset."""

    completeness: float
    validity: float
    uniqueness: float
    timeliness: float
    quality_score: float
    record_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "completeness": self.completeness,
            "validity": self.validity,
            "uniqueness": self.uniqueness,
            "timeliness": self.timeliness,
            "quality_score": self.quality_score,
            "record_count": self.record_count,
        }


def calculate_completeness(df: pd.DataFrame, required_column: str = "email") -> float:
    """Calculate completeness metric (percentage of non-null values).

    Args:
        df: DataFrame to evaluate
        required_column: Column to check for completeness

    Returns:
        Completeness score between 0.0 and 1.0
    """
    if required_column not in df.columns:
        return 0.0

    total_records = len(df)
    if total_records == 0:
        return 0.0

    non_null_count = df[required_column].notna().sum()
    return non_null_count / total_records


def calculate_validity(df: pd.DataFrame, email_column: str = "email") -> float:
    """Calculate validity metric (percentage of valid email formats).

    Args:
        df: DataFrame to evaluate
        email_column: Column containing email addresses

    Returns:
        Validity score between 0.0 and 1.0
    """
    if email_column not in df.columns:
        return 0.0

    total_records = len(df)
    if total_records == 0:
        return 0.0

    valid_count = df[email_column].str.match(EMAIL_PATTERN, na=False).sum()
    return valid_count / total_records


def calculate_uniqueness(df: pd.DataFrame, unique_column: str = "customer_id") -> float:
    """Calculate uniqueness metric (percentage of unique values).

    Args:
        df: DataFrame to evaluate
        unique_column: Column that should contain unique values

    Returns:
        Uniqueness score between 0.0 and 1.0
    """
    if unique_column not in df.columns:
        return 0.0

    total_records = len(df)
    if total_records == 0:
        return 0.0

    unique_count = df[unique_column].nunique()
    return unique_count / total_records


def calculate_timeliness(
    df: pd.DataFrame, date_column: str = "created_at", days_threshold: int = 30
) -> float:
    """Calculate timeliness metric (percentage of recent records).

    Args:
        df: DataFrame to evaluate
        date_column: Column containing dates
        days_threshold: Number of days to consider "recent"

    Returns:
        Timeliness score between 0.0 and 1.0
    """
    if date_column not in df.columns:
        return 0.0

    total_records = len(df)
    if total_records == 0:
        return 0.0

    try:
        dates = pd.to_datetime(df[date_column], errors="coerce")
        cutoff = datetime.now() - timedelta(days=days_threshold)
        recent_count = (dates >= cutoff).sum()
        return recent_count / total_records
    except Exception:
        return 0.0


def calculate_quality_score(
    df: pd.DataFrame,
    weights: Optional[dict[str, float]] = None,
    email_column: str = "email",
    date_column: str = "created_at",
    unique_column: str = "customer_id",
    days_threshold: int = 30,
) -> QualityMetrics:
    """Calculate overall quality score based on multiple dimensions.

    Args:
        df: DataFrame to evaluate
        weights: Optional custom weights for each dimension
        email_column: Column containing email addresses
        date_column: Column containing dates
        unique_column: Column that should be unique
        days_threshold: Days threshold for timeliness

    Returns:
        QualityMetrics object with all metrics and overall score
    """
    if weights is None:
        weights = {
            "completeness": 0.3,
            "validity": 0.3,
            "uniqueness": 0.2,
            "timeliness": 0.2,
        }

    completeness = calculate_completeness(df, email_column)
    validity = calculate_validity(df, email_column)
    uniqueness = calculate_uniqueness(df, unique_column)
    timeliness = calculate_timeliness(df, date_column, days_threshold)

    quality_score = (
        completeness * weights.get("completeness", 0.0)
        + validity * weights.get("validity", 0.0)
        + uniqueness * weights.get("uniqueness", 0.0)
        + timeliness * weights.get("timeliness", 0.0)
    )

    return QualityMetrics(
        completeness=completeness,
        validity=validity,
        uniqueness=uniqueness,
        timeliness=timeliness,
        quality_score=quality_score,
        record_count=len(df),
    )


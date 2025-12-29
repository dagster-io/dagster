"""Reusable validation functions for data quality checks."""

import pandas as pd

EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def validate_email_format(
    df: pd.DataFrame, email_column: str = "email"
) -> tuple[pd.DataFrame, list[str]]:
    """Validate email format in a DataFrame column.

    Args:
        df: DataFrame to validate
        email_column: Name of the email column

    Returns:
        Tuple of (invalid_records, list of error messages)
    """
    if email_column not in df.columns:
        return pd.DataFrame(), [f"Email column '{email_column}' not found"]

    invalid_mask = df[email_column].notna() & ~df[email_column].str.match(EMAIL_PATTERN, na=False)
    invalid_records = df[invalid_mask]

    errors = []
    if not invalid_records.empty:
        if "customer_id" in invalid_records.columns:
            invalid_ids = invalid_records["customer_id"].tolist()
            errors.append(
                f"Invalid email format: {len(invalid_records)} records (IDs: {invalid_ids})"
            )
        else:
            errors.append(f"Invalid email format: {len(invalid_records)} records")

    return invalid_records, errors


def validate_date_format(
    df: pd.DataFrame, date_column: str = "created_at", id_column: str = "customer_id"
) -> tuple[list[str], list[str]]:
    """Validate date format in a DataFrame column.

    Args:
        df: DataFrame to validate
        date_column: Name of the date column
        id_column: Name of the ID column for error reporting

    Returns:
        Tuple of (list of invalid IDs, list of error messages)
    """
    if date_column not in df.columns:
        return [], [f"Date column '{date_column}' not found"]

    invalid_ids = []
    for idx, row in df.iterrows():
        try:
            pd.to_datetime(row[date_column])
        except (ValueError, TypeError):
            if id_column in row:
                invalid_ids.append(str(row[id_column]))
            else:
                invalid_ids.append(str(idx))

    errors = []
    if invalid_ids:
        errors.append(f"Invalid date format: {len(invalid_ids)} records (IDs: {invalid_ids})")

    return invalid_ids, errors


def check_required_fields(df: pd.DataFrame, required_fields: list[str]) -> list[str]:
    """Check that required fields are present in the DataFrame.

    Args:
        df: DataFrame to check
        required_fields: List of required field names

    Returns:
        List of error messages for missing fields
    """
    missing = [f for f in required_fields if f not in df.columns]
    errors = []
    if missing:
        errors.append(f"Missing required fields: {missing}")
    return errors


def check_uniqueness(
    df: pd.DataFrame, unique_columns: list[str] | None = None
) -> tuple[pd.DataFrame, list[str]]:
    """Check for duplicate values in specified columns.

    Args:
        df: DataFrame to check
        unique_columns: List of column names that should be unique

    Returns:
        Tuple of (duplicate records, list of error messages)
    """
    if unique_columns is None:
        unique_columns = ["customer_id"]

    missing_cols = [col for col in unique_columns if col not in df.columns]
    if missing_cols:
        return pd.DataFrame(), [f"Columns not found for uniqueness check: {missing_cols}"]

    duplicates = df.duplicated(subset=unique_columns, keep=False)
    duplicate_records = df[duplicates]

    errors = []
    if not duplicate_records.empty:
        if "customer_id" in duplicate_records.columns:
            duplicate_ids = duplicate_records["customer_id"].unique().tolist()
            errors.append(
                f"Duplicate values found: {len(duplicate_records)} records (IDs: {duplicate_ids})"
            )
        else:
            errors.append(f"Duplicate values found: {len(duplicate_records)} records")

    return duplicate_records, errors


def check_age_range(
    df: pd.DataFrame,
    age_column: str = "age",
    min_age: int = 0,
    max_age: int = 150,
    id_column: str = "customer_id",
) -> tuple[pd.DataFrame, list[str]]:
    """Check that age values are within a reasonable range.

    Args:
        df: DataFrame to check
        age_column: Name of the age column
        min_age: Minimum valid age
        max_age: Maximum valid age
        id_column: Name of the ID column for error reporting

    Returns:
        Tuple of (invalid records, list of warning messages)
    """
    if age_column not in df.columns:
        return pd.DataFrame(), []

    invalid_mask = df[age_column].notna() & (
        (df[age_column] < min_age) | (df[age_column] > max_age)
    )
    invalid_records = df[invalid_mask]

    warnings = []
    if not invalid_records.empty:
        if id_column in invalid_records.columns:
            invalid_ids = invalid_records[id_column].tolist()
            warnings.append(
                f"Age out of reasonable range ({min_age}-{max_age}): "
                f"{len(invalid_records)} records (IDs: {invalid_ids})"
            )
        else:
            warnings.append(
                f"Age out of reasonable range ({min_age}-{max_age}): {len(invalid_records)} records"
            )

    return invalid_records, warnings


def clean_dataframe(
    df: pd.DataFrame,
    email_column: str = "email",
    date_column: str = "created_at",
    unique_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Clean a DataFrame by removing invalid records.

    Removes:
    - Invalid email formats
    - Invalid date formats
    - Duplicate records (keeps first occurrence)

    Args:
        df: DataFrame to clean
        email_column: Name of the email column
        date_column: Name of the date column
        unique_columns: Columns to use for duplicate detection

    Returns:
        Cleaned DataFrame
    """
    if unique_columns is None:
        unique_columns = ["customer_id"]

    df_clean = df.copy()

    if email_column in df_clean.columns:
        valid_email_mask = df_clean[email_column].str.match(EMAIL_PATTERN, na=False)
        df_clean = df_clean[valid_email_mask]

    if date_column in df_clean.columns:
        valid_dates = pd.to_datetime(df_clean[date_column], errors="coerce").notna()
        df_clean = df_clean[valid_dates]
        df_clean[date_column] = pd.to_datetime(df_clean[date_column])

    if all(col in df_clean.columns for col in unique_columns):
        df_clean = df_clean.drop_duplicates(subset=unique_columns, keep="first")

    return df_clean

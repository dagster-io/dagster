"""Tests for random data generators."""

from data_quality_patterns.defs.resources.data_generator import (
    generate_customers,
    generate_orders,
    generate_products,
)


def test_generate_customers_basic():
    """Test that customer generator produces expected columns."""
    df = generate_customers(n=10, failure_rate=0.0, seed=42)

    assert len(df) == 10
    assert "customer_id" in df.columns
    assert "email" in df.columns
    assert "name" in df.columns
    assert "region" in df.columns
    assert "created_at" in df.columns
    assert "age" in df.columns
    assert "status" in df.columns


def test_generate_customers_with_issues():
    """Test that customer generator introduces quality issues at expected rate."""
    # High failure rate to ensure issues are introduced
    df = generate_customers(n=100, failure_rate=0.5, seed=42)

    # Should have some null emails (completeness issues)
    null_emails = df["email"].isna().sum()
    assert null_emails > 0, "Expected some null emails with high failure rate"

    # Should have some duplicate IDs (uniqueness issues)
    unique_count = df["customer_id"].nunique()
    assert unique_count < len(df), "Expected some duplicate IDs with high failure rate"


def test_generate_customers_reproducible():
    """Test that seeded generator produces reproducible results for non-time fields."""
    df1 = generate_customers(n=50, failure_rate=0.15, seed=123)
    df2 = generate_customers(n=50, failure_rate=0.15, seed=123)

    # Compare non-time columns (created_at has timestamps that differ)
    compare_cols = ["customer_id", "email", "name", "region", "age", "status"]
    assert df1[compare_cols].equals(df2[compare_cols]), "Same seed should produce identical data"


def test_generate_orders_basic():
    """Test that order generator produces expected columns."""
    df = generate_orders(n=10, failure_rate=0.0, seed=42)

    assert len(df) == 10
    assert "order_id" in df.columns
    assert "customer_id" in df.columns
    assert "amount" in df.columns
    assert "order_date" in df.columns
    assert "status" in df.columns


def test_generate_orders_with_invalid_refs():
    """Test that order generator introduces integrity issues."""
    valid_customer_ids = ["CUST-00001", "CUST-00002"]
    df = generate_orders(n=50, customer_ids=valid_customer_ids, failure_rate=0.5, seed=42)

    # Should have some invalid customer references
    invalid_refs = ~df["customer_id"].isin(valid_customer_ids)
    assert invalid_refs.sum() > 0, "Expected some invalid customer references"


def test_generate_products_basic():
    """Test that product generator produces expected columns."""
    df = generate_products(n=10, failure_rate=0.0, seed=42)

    assert len(df) == 10
    assert "sku" in df.columns
    assert "name" in df.columns
    assert "price" in df.columns
    assert "category" in df.columns
    assert "in_stock" in df.columns

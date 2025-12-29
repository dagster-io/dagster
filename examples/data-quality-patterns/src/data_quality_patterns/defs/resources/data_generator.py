"""Random data generators with configurable quality issues.

This module generates test data with intentional quality problems
to demonstrate data quality validation across all 7 dimensions:
- Accuracy: Incorrect data values
- Completeness: Missing values
- Consistency: Inconsistent formats/values
- Timeliness: Stale data
- Validity: Invalid formats
- Uniqueness: Duplicate records
- Integrity: Broken references
"""

import random
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd


def generate_customers(
    n: int = 100,
    failure_rate: float = 0.15,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Generate customer data with random quality issues.

    Args:
        n: Number of records to generate
        failure_rate: Probability of introducing issues (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        DataFrame with customer data containing various quality issues:
        - Duplicate customer_ids (uniqueness)
        - Missing emails (completeness)
        - Invalid email formats (validity)
        - Incorrect name patterns (accuracy)
        - Inconsistent region codes (consistency)
        - Old created_at dates (timeliness)
    """
    if seed is not None:
        random.seed(seed)

    data: list[dict] = []
    existing_ids: list[str] = []
    valid_regions = ["US", "EU", "APAC", "LATAM"]
    invalid_regions = ["USA", "Europe", "Asia-Pacific", "LA"]  # Inconsistent formats

    for i in range(n):
        # Determine which quality issues to introduce
        has_uniqueness_issue = random.random() < (failure_rate / 2) and existing_ids
        has_completeness_issue = random.random() < failure_rate
        has_validity_issue = random.random() < failure_rate
        has_accuracy_issue = random.random() < failure_rate
        has_consistency_issue = random.random() < failure_rate
        has_timeliness_issue = random.random() < failure_rate

        # Customer ID - may be duplicate (uniqueness)
        if has_uniqueness_issue:
            customer_id = random.choice(existing_ids)
        else:
            customer_id = f"CUST-{i:05d}"
            existing_ids.append(customer_id)

        # Email - may be missing (completeness) or invalid (validity)
        if has_completeness_issue:
            email = None
        elif has_validity_issue:
            # Various invalid email formats
            invalid_formats = [
                "invalid-email",
                "missing@domain",
                "@nodomain.com",
                "spaces in@email.com",
                "double@@at.com",
            ]
            email = random.choice(invalid_formats)
        else:
            email = f"customer{i}@example.com"

        # Name - may have accuracy issues
        if has_accuracy_issue:
            # Accuracy issues: wrong patterns, suspicious values
            accuracy_issues = [
                "TEST USER",
                "XXXXXX",
                "John Doe",  # Generic placeholder
                "N/A",
                "Unknown",
            ]
            name = random.choice(accuracy_issues)
        else:
            first_names = ["Alice", "Bob", "Carol", "David", "Emma", "Frank"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
            name = f"{random.choice(first_names)} {random.choice(last_names)}"

        # Region - may have consistency issues
        if has_consistency_issue:
            region = random.choice(invalid_regions)
        else:
            region = random.choice(valid_regions)

        # Created date - may be stale (timeliness)
        if has_timeliness_issue:
            # Create dates from 1-3 years ago
            days_ago = random.randint(365, 1095)
        else:
            # Recent dates within last 30 days
            days_ago = random.randint(1, 30)

        created_at = (datetime.now() - timedelta(days=days_ago)).isoformat()

        # Age - may have accuracy issues
        if has_accuracy_issue:
            age = random.choice([-5, 0, 150, 200, 999])  # Invalid ages
        else:
            age = random.randint(18, 80)

        record = {
            "customer_id": customer_id,
            "email": email,
            "name": name,
            "region": region,
            "created_at": created_at,
            "age": age,
            "status": random.choice(["active", "inactive"]),
        }
        data.append(record)

    return pd.DataFrame(data)


def generate_orders(
    n: int = 200,
    customer_ids: Optional[list[str]] = None,
    failure_rate: float = 0.15,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Generate order data with random quality issues.

    Args:
        n: Number of records to generate
        customer_ids: Valid customer IDs for referential integrity.
                     If None, generates random IDs.
        failure_rate: Probability of introducing issues (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        DataFrame with order data containing various quality issues:
        - Invalid customer_id references (integrity)
        - Duplicate order_ids (uniqueness)
        - Missing amounts (completeness)
        - Negative amounts (validity)
    """
    if seed is not None:
        random.seed(seed)

    if customer_ids is None:
        customer_ids = [f"CUST-{i:05d}" for i in range(50)]

    data: list[dict] = []
    existing_order_ids: list[str] = []

    for i in range(n):
        # Determine quality issues
        has_integrity_issue = random.random() < failure_rate
        has_uniqueness_issue = random.random() < (failure_rate / 2) and existing_order_ids
        has_completeness_issue = random.random() < failure_rate
        has_validity_issue = random.random() < failure_rate

        # Order ID - may be duplicate (uniqueness)
        if has_uniqueness_issue:
            order_id = random.choice(existing_order_ids)
        else:
            order_id = f"ORD-{i:06d}"
            existing_order_ids.append(order_id)

        # Customer ID - may reference non-existent customer (integrity)
        if has_integrity_issue:
            customer_id = f"CUST-INVALID-{random.randint(10000, 99999)}"
        else:
            customer_id = random.choice(customer_ids)

        # Amount - may be missing (completeness) or invalid (validity)
        if has_completeness_issue:
            amount = None
        elif has_validity_issue:
            amount = random.uniform(-100, -1)  # Negative amount
        else:
            amount = round(random.uniform(10, 1000), 2)

        # Order date
        days_ago = random.randint(1, 90)
        order_date = (datetime.now() - timedelta(days=days_ago)).isoformat()

        record = {
            "order_id": order_id,
            "customer_id": customer_id,
            "amount": amount,
            "order_date": order_date,
            "status": random.choice(["pending", "completed", "cancelled"]),
        }
        data.append(record)

    return pd.DataFrame(data)


def generate_products(
    n: int = 50,
    failure_rate: float = 0.10,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Generate product data with random quality issues.

    Args:
        n: Number of records to generate
        failure_rate: Probability of introducing issues (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        DataFrame with product data containing various quality issues
    """
    if seed is not None:
        random.seed(seed)

    categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
    data: list[dict] = []
    existing_skus: list[str] = []

    for i in range(n):
        has_uniqueness_issue = random.random() < (failure_rate / 2) and existing_skus
        has_completeness_issue = random.random() < failure_rate
        has_validity_issue = random.random() < failure_rate

        # SKU - may be duplicate
        if has_uniqueness_issue:
            sku = random.choice(existing_skus)
        else:
            sku = f"SKU-{i:04d}"
            existing_skus.append(sku)

        # Price - may be missing or invalid
        if has_completeness_issue:
            price = None
        elif has_validity_issue:
            price = random.choice([-10, 0, 999999])
        else:
            price = round(random.uniform(5, 500), 2)

        # Name - may be missing
        if has_completeness_issue:
            name = None
        else:
            name = f"Product {i}"

        record = {
            "sku": sku,
            "name": name,
            "price": price,
            "category": random.choice(categories),
            "in_stock": random.choice([True, False]),
        }
        data.append(record)

    return pd.DataFrame(data)


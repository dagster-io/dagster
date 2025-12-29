# Data Quality Patterns - Dagster Example Project

A comprehensive Dagster project demonstrating data quality validation across all 7 dimensions using native asset checks, Great Expectations, dbt tests, and freshness policies.

## Data Quality Dimensions

This project covers all 7 dimensions of data quality:

| Dimension        | Description                                   | Implementation                              |
| ---------------- | --------------------------------------------- | ------------------------------------------- |
| **Accuracy**     | Data correctly represents real-world entities | Python checks for name patterns, age ranges |
| **Completeness** | All required data is present                  | Python + dbt `not_null` tests               |
| **Consistency**  | Data is uniform across datasets               | Python checks for region code formats       |
| **Timeliness**   | Data is up-to-date and available              | `FreshnessPolicy` on assets                 |
| **Validity**     | Data conforms to formats and rules            | Python + Great Expectations checks          |
| **Uniqueness**   | No unwanted duplicates                        | Python + dbt `unique` tests                 |
| **Integrity**    | Relationships between data maintained         | Python + dbt `relationships` tests          |

## Project Structure

```
data-quality-patterns/
├── pyproject.toml                    # Project configuration (uv)
├── uv.lock                           # Lock file (generated)
├── README.md                         # This file
├── src/data_quality_patterns/        # Main Python package
│   ├── __init__.py
│   ├── definitions.py                # Dagster Definitions entry point
│   ├── project.py                    # dbt project configuration
│   ├── lib/                          # Reusable validation library
│   │   ├── validators.py             # Email, date, uniqueness validators
│   │   ├── quality_metrics.py        # Quality score calculations
│   │   └── expectations.py           # Great Expectations utilities
│   └── defs/
│       ├── assets/
│       │   ├── raw_data.py           # Raw data assets with random issues
│       │   ├── python_checks.py      # Native Dagster asset checks
│       │   ├── ge_checks.py          # Great Expectations checks
│       │   ├── dbt_assets.py         # dbt assets with test checks
│       │   └── freshness.py          # Freshness policies
│       └── resources/
│           └── data_generator.py     # Random data with quality issues
├── dbt_project/                      # dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/                  # Staging models with tests
│       │   ├── stg_customers.sql
│       │   ├── stg_orders.sql
│       │   ├── sources.yml
│       │   └── schema.yml            # dbt tests (unique, not_null, relationships)
│       └── marts/                    # Mart models with tests
│           ├── cleaned_customers.sql
│           ├── order_summary.sql
│           └── schema.yml
└── tests/                            # Test suite
    ├── conftest.py                   # Pytest fixtures
    ├── test_data_generator.py        # Data generator tests
    ├── test_validators.py            # Validator tests
    ├── test_asset_checks.py          # Asset check tests (including failures)
    └── test_definitions.py           # Definition loading tests
```

## Quick Start

### 1. Install Dependencies

```bash
cd examples/data-quality-patterns

# Install with uv (recommended)
uv sync --all-groups

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Compile dbt Project

```bash
cd dbt_project
dbt compile --profiles-dir .
cd ..
```

### 3. Start Dagster

```bash
dg dev
```

Open http://localhost:3000 to view the Dagster UI.

### 4. Materialize Assets

In the Dagster UI:

1. Navigate to the **Assets** page
2. Select `raw_customers`, `raw_orders`, and `raw_products`
3. Click **Materialize** to generate data with quality issues
4. View the asset checks to see which quality dimensions fail

## Quality Check Types

### Native Python Asset Checks

Located in `src/data_quality_patterns/defs/assets/python_checks.py`:

| Check                          | Dimension    | Description                                  |
| ------------------------------ | ------------ | -------------------------------------------- |
| `check_accuracy_names`         | Accuracy     | Detects placeholder/test names               |
| `check_accuracy_age`           | Accuracy     | Validates age ranges (0-120)                 |
| `check_completeness_email`     | Completeness | Requires 95% email coverage                  |
| `check_completeness_amount`    | Completeness | Requires 98% amount coverage                 |
| `check_consistency_region`     | Consistency  | Validates region codes (US, EU, APAC, LATAM) |
| `check_validity_email`         | Validity     | Validates email format                       |
| `check_validity_amount`        | Validity     | Validates positive amounts                   |
| `check_uniqueness_customer_id` | Uniqueness   | Detects duplicate customers                  |
| `check_uniqueness_order_id`    | Uniqueness   | Detects duplicate orders                     |
| `check_integrity_customer_ref` | Integrity    | Validates customer foreign keys              |

### Great Expectations Checks

Located in `src/data_quality_patterns/defs/assets/ge_checks.py`:

| Check                     | Dimension    | Description               |
| ------------------------- | ------------ | ------------------------- |
| `ge_check_sku_unique`     | Uniqueness   | Product SKU uniqueness    |
| `ge_check_name_not_null`  | Completeness | Product name presence     |
| `ge_check_price_positive` | Validity     | Price range validation    |
| `ge_check_category_valid` | Consistency  | Category value validation |

### dbt Tests as Asset Checks

Defined in `dbt_project/models/*/schema.yml`:

- `unique` - Uniqueness dimension
- `not_null` - Completeness dimension
- `relationships` - Integrity dimension
- `accepted_values` - Consistency dimension

### Freshness Policies

Raw data assets have `FreshnessPolicy` attached for timeliness monitoring:

- Fail window: 24 hours
- Warn window: 12 hours

## Random Data with Quality Issues

The data generator creates data with configurable quality issues:

```python
from data_quality_patterns.defs.resources.data_generator import generate_customers

# Generate 100 customers with 15% failure rate
df = generate_customers(n=100, failure_rate=0.15, seed=42)
```

Quality issues introduced:

- **Uniqueness**: Duplicate customer IDs
- **Completeness**: Missing email addresses
- **Validity**: Invalid email formats
- **Accuracy**: Placeholder names, invalid ages
- **Consistency**: Non-standard region codes
- **Timeliness**: Old creation dates
- **Integrity**: Invalid customer references in orders

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_asset_checks.py -v
```

Tests verify that:

- Quality checks correctly identify issues in random data
- Clean data passes all checks
- Validators work as expected
- Definitions load without errors

## Key Concepts Demonstrated

- **Native asset checks** with `@asset_check` decorator
- **Great Expectations integration** for comprehensive validation
- **dbt tests as asset checks** via `DagsterDbtTranslator`
- **Freshness policies** for timeliness monitoring
- **Random data generation** with configurable quality issues
- **Quality metrics calculation** for scoring
- **uv package management** with lock file

## Development

### Linting

```bash
ruff check . --isolated
ruff check . --fix --isolated  # Auto-fix issues
```

### Project Configuration

The project uses:

- `pyproject.toml` for dependency management (uv/hatch)
- `tool.dagster` for Dagster configuration
- `tool.dg` for dg CLI configuration

## Notes

- Data is stored in DuckDB (`data_quality.duckdb`)
- dbt models read from raw schema populated by Dagster
- Some checks are designed to fail to demonstrate detection capabilities
- Use `seed` parameter in generators for reproducible test data

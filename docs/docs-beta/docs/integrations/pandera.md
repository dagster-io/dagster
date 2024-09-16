---
layout: Integration
status: published
name: Pandera
title: Dagster & Pandera
sidebar_label: Pandera
excerpt: Generate Dagster Types from Pandera dataframe schemas.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-pandera
docslink: https://docs.dagster.io/integrations/pandera
partnerlink: https://pandera.readthedocs.io/en/stable/
logo: /integrations/Pandera.svg
categories:
  - Metadata
enabledBy:
enables:
---

### About this integration

The `dagster-pandera` integration library provides an API for generating Dagster Types from [Pandera DataFrame schemas](https://pandera.readthedocs.io/en/stable/dataframe_schemas.html).

Like all Dagster types, Dagster-Pandera-generated types can be used to annotate op inputs and outputs. This provides runtime type-checking with rich error reporting and allows Dagster UI to display information about a DataFrame's structure.

### Installation

```bash
pip install dagster-pandera
```

### Example

```python
import random
import pandas as pd
import pandera as pa
from dagster_pandera import pandera_schema_to_dagster_type
from pandera.typing import Series
from dagster import asset

APPLE_STOCK_PRICES = {
    "name": ["AAPL", "AAPL", "AAPL", "AAPL", "AAPL"],
    "date": ["2018-01-22", "2018-01-23", "2018-01-24", "2018-01-25", "2018-01-26"],
    "open": [177.3, 177.3, 177.25, 174.50, 172.0],
    "close": [177.0, 177.04, 174.22, 171.11, 171.51],
}


class StockPrices(pa.SchemaModel):
    """Open/close prices for one or more stocks by day."""

    name: Series[str] = pa.Field(description="Ticker symbol of stock")
    date: Series[str] = pa.Field(description="Date of prices")
    open: Series[float] = pa.Field(ge=0, description="Price at market open")
    close: Series[float] = pa.Field(ge=0, description="Price at market close")


@asset(dagster_type=pandera_schema_to_dagster_type(StockPrices))
def apple_stock_prices_dirty():
    prices = pd.DataFrame(APPLE_STOCK_PRICES)
    i = random.choice(prices.index)
    prices.loc[i, "open"] = pd.NA
    prices.loc[i, "close"] = pd.NA
    return prices
```

### About Pandera

**Pandera** is a statistical data testing toolkit, and a data validation library for scientists, engineers, and analysts seeking correctness.

---
title: Dagster & Patito
sidebar_label: Patito
description: Patito is a data validation framework for Polars, based on Pydantic.
tags: [community-supported, metadata]
source:
pypi:
sidebar_custom_props:
  logo: images/integrations/patito.png
  community: true
partnerlink: https://github.com/JakobGM/patito
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

For more information on how to use Dagster with Polars, see [dagster-polars documentation](/integrations/libraries/polars).

## Installation

<PackageInstallInstructions packageName="dagster-polars[patito]" />

## Usage

`dagster-polars` automatically recognizes Patito type annotations, performs data validation using the specified model, and infers table metadata such as column constraints, data types, and descriptions.

```python
import dagster as dg
import patito as pt
import polars as pl

class User(pt.Model):
    uid: str = pt.Field(unique=True, description="User ID")
    age: int | None = pt.Field(gt=18, description="User age")


@dg.asset(io_manager_key="polars_parquet_io_manager")
def my_asset() -> User.DataFrame:
    my_data = ...
    return User.DataFrame(my_data)
```

The specified `User` model will be used to validate the data returned by the `my_asset` asset. If the data does not conform to the model, an error will be raised.

Upstream assets can also be annotated with Patito models, ensuring that the input data is always validated.

Alternatively, the standalone `dagster_polars.patito.patito_model_to_dagster_type` function can be used to build a dagster type for a given Patito model, which can then be used with any IOManager. In this case, the type annotation can be a normal `pl.DataFrame`.

```python
from dagster_polars.patito import patito_model_to_dagster_type

user_type = patito_model_to_dagster_type(User)


@dg.asset(io_manager_key="polars_parquet_io_manager", dagster_type=user_type)
def my_asset() -> pl.DataFrame:
    my_data = ...
    return pl.DataFrame(my_data)  # <- you better behave, mr. data!
```

The same dagster type can be used when loading data into downstream assets, ensuring that the data is always validated.

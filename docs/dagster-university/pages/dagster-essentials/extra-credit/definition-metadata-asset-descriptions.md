---
title: 'Extra credit: Definition metadata - Asset descriptions'
module: 'dagster_essentials'
lesson: 'extra-credit'
---

# Definition metadata - Asset descriptions

When defined, asset descriptions will be displayed in the Dagster UI alongside the asset. There are two ways to add an asset description:

- Using Python docstrings
- Using the asset decorator’s `description` parameter

---

## Using docstrings

As you went through this course, you might have noticed that the assets all contain **docstrings.** A [Python docstring, or documentation string](https://www.datacamp.com/tutorial/docstrings-python), embeds documentation about a class, module, function, or method definition in the code itself. While code comments serve a similar purpose, docstrings support built-in Python functionality, like [`help`](https://docs.python.org/3/library/functions.html#help).

Docstrings are defined by including a string, surrounded by triple quotes (`”””`) as the first statement in an object’s definition. For example:

```python
from dagster import asset

@asset
def taxi_zones_file() -> None:
    """
      The raw CSV file for the taxi zones dataset. Sourced from the NYC Open Data portal.
    """
    raw_taxi_zones = requests.get(
        "https://data.cityofnewyork.us/api/views/755u-8jsi/rows.csv?accessType=DOWNLOAD"
    )

    with open(constants.TAXI_ZONES_FILE_PATH, "wb") as output_file:
        output_file.write(raw_taxi_zones.content)
```

---

## Using the description parameter

Another way to add a description to an asset is to use the asset decorator with the `description` parameter. **Note:** This will override any docstrings in the Dagster UI.

For example:

```python
from dagster import asset

@asset(
    description="The raw CSV file for the taxi zones dataset. Sourced from the NYC Open Data portal."
)
def taxi_zones_file() -> None:
    """
      This will not show in the Dagster UI
    """
    raw_taxi_zones = requests.get(
        "https://data.cityofnewyork.us/api/views/755u-8jsi/rows.csv?accessType=DOWNLOAD"
    )

    with open(constants.TAXI_ZONES_FILE_PATH, "wb") as output_file:
        output_file.write(raw_taxi_zones.content)
```

---

## Asset descriptions in the Dagster UI

Now that you understand how to define asset descriptions, let’s take a look at them in the Dagster UI.

{% table %}

- The Assets page

---

- {% width="60%" %}
  For each asset in the **Assets** tab, the description will display under each asset key.

- ![The Assets page in the Dagster UI](/images/dagster-essentials/extra-credit/ui-assets-page.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Global Asset Lineage

---

- {% width="60%" %}
  In the **Global Asset Lineage** page, the description will be included in each of the asset boxes in the DAG.

- ![The Global Asset Lineage page in the Dagster UI](/images/dagster-essentials/extra-credit/ui-global-asset-lineage.png) {% rowspan=2 %}

{% /table %}

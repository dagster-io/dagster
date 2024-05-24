---
title: 'Extra credit: Practice: Add metadata to taxi_zones_file'
module: 'dagster_essentials'
lesson: 'extra-credit'
---

# Practice: Add metadata to taxi_zones_file

To practice what you’ve learned, add the record counts to the metadata for `taxi_zones_file`.

---

## Check your work

The metadata you built should look similar to the code contained in the **View answer** toggle. Click to open it.

```python {% obfuscated="true" %}
from dagster import MaterializeResult


@asset(
    group_name="raw_files",
)
def taxi_zones_file() -> None:
    """
      The raw CSV file for the taxi zones dataset. Sourced from the NYC Open Data portal.
    """
    raw_taxi_zones = requests.get(
        "https://data.cityofnewyork.us/api/views/755u-8jsi/rows.csv?accessType=DOWNLOAD"
    )

    with open(constants.TAXI_ZONES_FILE_PATH, "wb") as output_file:
        output_file.write(raw_taxi_zones.content)
    num_rows = len(pd.read_csv(constants.TAXI_ZONES_FILE_PATH))

    return MaterializeResult(
        metadata={
            'Number of records': MetadataValue.int(num_rows)
        }
    )
```

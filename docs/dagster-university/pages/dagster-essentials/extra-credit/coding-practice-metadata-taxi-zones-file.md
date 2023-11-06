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
@asset(
    group_name="raw_files",
)
def taxi_zones_file(context):
  """
    The raw CSV file for the taxi zones dataset. Sourced from the NYC Open Data portal.
  """
  raw_taxi_zones = requests.get(
    "https://data.cityofnewyork.us/api/views/755u-8jsi/rows.csv?accessType=DOWNLOAD"
  )

  with open(constants.TAXI_ZONES_FILE_PATH, "wb") as output_file:
    output_file.write(raw_taxi_zones.content)
  num_rows = MetadataValue.int(len(pd.read_csv(constants.TAXI_ZONES_FILE_PATH)))
  context.add_output_metadata({'Number of records': num_rows})
```

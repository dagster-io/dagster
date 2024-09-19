---
title: 'Lesson 3: Practice: Create a taxi_zones_file asset'
module: 'dagster_essentials'
lesson: '3'
---

# Practice: Create a taxi_zones_file asset

To practice what you’ve learned, create an asset in `trips.py` that:

- Is named `taxi_zones_file`. This asset will contain a unique identifier and name for each part of NYC as a distinct taxi zone.
- Uses the `requests` library to obtain [NYC Taxi Zones](https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc) data from [this link](https://data.cityofnewyork.us/api/views/755u-8jsi/rows.csv?accessType=DOWNLOAD): `https://data.cityofnewyork.us/api/views/755u-8jsi/rows.csv?accessType=DOWNLOAD`
- Stores the data as a CSV in `data/raw/taxi_zones.csv`. This path is provided for you in `constants.TAXI_ZONES_FILE_PATH`.

---

## Check your work

The asset you built should look similar to the following code. Click **View answer** to view it.

**If there are differences**, compare what you wrote to the asset below and change them, as this asset will be used as-is in future lessons.

```python {% obfuscated="true" %}
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

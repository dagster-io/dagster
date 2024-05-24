---
title: 'Extra credit: Practice: Grouping assets'
module: 'dagster_essentials'
lesson: 'extra-credit'
---

# Practice: Grouping assets

To practice what you’ve learned about asset groups, organize the assets in your project by:

- **Using the asset decorator method to**:
  - Add `taxi_trips_file` to the `raw_files` group
  - Add the `taxi_zones` and `taxi_trips` assets into an `ingested` group
- **Using the asset submodule method**, add the `adhoc_request` asset into a `requests` group

---

## Check your work

The asset groups you built should look similar to the code contained in the **View answer** toggle. Click to open it.

### For the asset decorator method:

For the assets in the `raw_files` and `ingested` groups, your assets should look like this:

```python {% obfuscated="true" %}
@asset(
    group_name="GROUP_NAME"
)
def name_of_asset():
```

### For the asset submodule method:

For the `adhoc_request` asset, your code should look like this:

```python {% obfuscated="true" %}
request_assets = load_assets_from_modules(
    modules=[requests],
    group_name="requests",
)
```

### The Dagster UI:

After adding the assets to the groups, the asset graph should look like this:

![The updated asset graph in the Dagster UI](/images/dagster-essentials/extra-credit/ui-asset-groups-practice-answer.png)

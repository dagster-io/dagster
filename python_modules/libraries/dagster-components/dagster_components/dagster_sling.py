import importlib.util

_has_dagster_sling = importlib.util.find_spec("dagster_sling") is not None

if _has_dagster_sling:
    from dagster_sling import (
        SlingReplicationCollectionComponent as SlingReplicationCollectionComponent,
    )

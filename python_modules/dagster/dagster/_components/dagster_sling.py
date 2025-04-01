import importlib.util

_has_dagster_sling = importlib.util.find_spec("dagster_sling") is not None

if _has_dagster_sling:
    from dagster._components.lib.sling_replication_collection.component import (
        SlingReplicationCollectionComponent as SlingReplicationCollectionComponent,
    )

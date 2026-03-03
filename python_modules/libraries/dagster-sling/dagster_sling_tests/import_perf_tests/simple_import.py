"""Simple script that imports dagster-sling public APIs.

This is used by test_import_perf.py to verify that importing dagster-sling
does not eagerly import the sling package, which has expensive side effects.
"""

from dagster_sling import (
    DagsterSlingTranslator,
    SlingConnectionResource,
    SlingMode,
    SlingReplicationParam,
    SlingResource,
    sling_assets,
)

# Just verify we can access the imported objects
_ = SlingResource
_ = SlingConnectionResource
_ = SlingMode
_ = sling_assets
_ = DagsterSlingTranslator
_ = SlingReplicationParam

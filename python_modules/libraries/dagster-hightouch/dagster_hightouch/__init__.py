from dagster._core.libraries import DagsterLibraryRegistry

__version__ = "0.1.8"

DagsterLibraryRegistry.register(
    "dagster-hightouch", __version__, is_dagster_package=False
)

__all__ = [
    "ConfigurableHightouchResource",
    "HightouchResource",
    "hightouch_sync_op",
    "HightouchSyncComponent",
]
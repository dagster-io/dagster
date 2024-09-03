from dagster._core.libraries import DagsterLibraryRegistry

# Move back to version.py and edit setup.py once we are ready to publish.
__version__ = "1!0+dev"

DagsterLibraryRegistry.register("dagster-tableau", __version__)

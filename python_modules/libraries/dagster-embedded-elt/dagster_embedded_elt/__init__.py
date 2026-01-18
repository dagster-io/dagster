from dagster._utils.warnings import deprecation_warning
from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_embedded_elt.version import __version__

deprecation_warning(
    "The `dagster-embedded-elt` library",
    "0.26",
    additional_warn_text="Use `dagster-dlt` and `dagster-sling` instead.",
)

DagsterLibraryRegistry.register("dagster-embedded-elt", __version__)

from importlib import util as iutil

from dagster_airlift.version import __version__

is_dagster_installed = iutil.find_spec("dagster") is not None
# In the case of running CI/CD, where we have Dagster installed in the environment, we want to be able to register the library in our library registry. But we want
# to avoid taking an actual dependency on Dagster, so we need to gate this behind a check for the presence of the Dagster package in the environment.
if is_dagster_installed:
    from dagster_shared.libraries import DagsterLibraryRegistry

    DagsterLibraryRegistry.register("dagster-airlift", __version__)

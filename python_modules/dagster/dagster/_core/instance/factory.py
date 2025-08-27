"""Factory functions for creating DagsterInstance instances."""

import os
from collections.abc import Sequence
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.errors import DagsterHomeNotSetError, DagsterInvariantViolationError
from dagster._core.instance.config import DAGSTER_CONFIG_YAML_FILENAME
from dagster._core.instance.ref import InstanceRef
from dagster._core.instance.types import InstanceType

if TYPE_CHECKING:
    from dagster._core.debug import DebugRunPayload
    from dagster._core.instance.instance import DagsterInstance, DagsterInstanceOverrides


def create_ephemeral_instance(
    tempdir: Optional[str] = None,
    preload: Optional[Sequence["DebugRunPayload"]] = None,
    settings: Optional[dict] = None,
) -> "DagsterInstance":
    """Create a `DagsterInstance` suitable for ephemeral execution, useful in test contexts. An
    ephemeral instance uses mostly in-memory components. Use `local_temp` to create a test
    instance that is fully persistent.

    Args:
        tempdir (Optional[str]): The path of a directory to be used for local artifact storage.
        preload (Optional[Sequence[DebugRunPayload]]): A sequence of payloads to load into the
            instance's run storage. Useful for debugging.
        settings (Optional[Dict]): Settings for the instance.

    Returns:
        DagsterInstance: An ephemeral DagsterInstance.
    """
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
    from dagster._core.run_coordinator import DefaultRunCoordinator
    from dagster._core.storage.event_log import InMemoryEventLogStorage
    from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
    from dagster._core.storage.root import LocalArtifactStorage, TemporaryLocalArtifactStorage
    from dagster._core.storage.runs import InMemoryRunStorage

    if tempdir is not None:
        local_storage = LocalArtifactStorage(tempdir)
    else:
        local_storage = TemporaryLocalArtifactStorage()

    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=local_storage,
        run_storage=InMemoryRunStorage(preload=preload),
        event_storage=InMemoryEventLogStorage(preload=preload),
        compute_log_manager=NoOpComputeLogManager(),
        run_coordinator=DefaultRunCoordinator(),
        run_launcher=SyncInMemoryRunLauncher(),
        settings=settings,
    )


def create_instance_from_dagster_home() -> "DagsterInstance":
    """Get the current `DagsterInstance` as specified by the ``DAGSTER_HOME`` environment variable.

    Returns:
        DagsterInstance: The current DagsterInstance.
    """
    dagster_home_path = os.getenv("DAGSTER_HOME")

    if not dagster_home_path:
        raise DagsterHomeNotSetError(
            "The environment variable $DAGSTER_HOME is not set. \nDagster requires this"
            " environment variable to be set to an existing directory in your filesystem. This"
            " directory is used to store metadata across sessions, or load the dagster.yaml"
            " file which can configure storing metadata in an external database.\nYou can"
            " resolve this error by exporting the environment variable. For example, you can"
            " run the following command in your shell or include it in your shell configuration"
            ' file:\n\texport DAGSTER_HOME=~"/dagster_home"\nor PowerShell\n$env:DAGSTER_HOME'
            " = ($home + '\\dagster_home')or batchset"
            " DAGSTER_HOME=%UserProfile%/dagster_homeAlternatively, DagsterInstance.ephemeral()"
            " can be used for a transient instance.\n"
        )

    dagster_home_path = os.path.expanduser(dagster_home_path)

    if not os.path.isabs(dagster_home_path):
        raise DagsterInvariantViolationError(
            f'$DAGSTER_HOME "{dagster_home_path}" must be an absolute path. Dagster requires this '
            "environment variable to be set to an existing directory in your filesystem."
        )

    if not (os.path.exists(dagster_home_path) and os.path.isdir(dagster_home_path)):
        raise DagsterInvariantViolationError(
            f'$DAGSTER_HOME "{dagster_home_path}" is not a directory or does not exist. Dagster requires this'
            " environment variable to be set to an existing directory in your filesystem"
        )

    return create_instance_from_config(dagster_home_path)


def create_local_temp_instance(
    tempdir: Optional[str] = None,
    overrides: Optional["DagsterInstanceOverrides"] = None,
) -> "DagsterInstance":
    """Create a DagsterInstance that uses a temporary directory for local storage. This is a
    regular, fully persistent instance. Use `ephemeral` to get an ephemeral instance with
    in-memory components.

    Args:
        tempdir (Optional[str]): The path of a directory to be used for local artifact storage.
        overrides (Optional[DagsterInstanceOverrides]): Override settings for the instance.

    Returns:
        DagsterInstance
    """
    from dagster._core.instance.instance import DagsterInstance

    if tempdir is None:
        created_dir = TemporaryDirectory()
        i = create_instance_from_ref(InstanceRef.from_dir(created_dir.name, overrides=overrides))
        # Store the temp dir for cleanup when the instance is garbage collected
        DagsterInstance._TEMP_DIRS[i] = created_dir  # noqa: SLF001
        return i

    return create_instance_from_ref(InstanceRef.from_dir(tempdir, overrides=overrides))


def create_instance_from_config(
    config_dir: str,
    config_filename: str = DAGSTER_CONFIG_YAML_FILENAME,
) -> "DagsterInstance":
    instance_ref = InstanceRef.from_dir(config_dir, config_filename=config_filename)
    return create_instance_from_ref(instance_ref)


def create_instance_from_ref(instance_ref: InstanceRef) -> "DagsterInstance":
    from dagster._core.instance.instance import DagsterInstance

    check.inst_param(instance_ref, "instance_ref", InstanceRef)

    # DagsterInstance doesn't implement ConfigurableClass, but we may still sometimes want to
    # have custom subclasses of DagsterInstance. This machinery allows for those custom
    # subclasses to receive additional keyword arguments passed through the config YAML.
    klass = instance_ref.custom_instance_class or DagsterInstance
    kwargs = instance_ref.custom_instance_class_config

    unified_storage = instance_ref.storage
    run_storage = unified_storage.run_storage if unified_storage else instance_ref.run_storage
    event_storage = (
        unified_storage.event_log_storage if unified_storage else instance_ref.event_storage
    )
    schedule_storage = (
        unified_storage.schedule_storage if unified_storage else instance_ref.schedule_storage
    )

    return klass(
        instance_type=InstanceType.PERSISTENT,
        local_artifact_storage=instance_ref.local_artifact_storage,
        run_storage=run_storage,  # type: ignore  # (possible none)
        event_storage=event_storage,  # type: ignore  # (possible none)
        schedule_storage=schedule_storage,
        compute_log_manager=None,  # lazy load
        scheduler=instance_ref.scheduler,
        run_coordinator=None,  # lazy load
        run_launcher=None,  # lazy load
        settings=instance_ref.settings,
        secrets_loader=instance_ref.secrets_loader,
        defs_state_storage=instance_ref.defs_state_storage,
        ref=instance_ref,
        **kwargs,
    )

import datetime
import os
import pickle
import platform
import shutil
import time
import uuid
from contextlib import contextmanager
from typing import Optional, TypedDict

from dagster import (
    Field,
    InitResourceContext,
    InputContext,
    Int,
    IOManager,
    MetadataValue,
    OutputContext,
    String,
    io_manager,
)
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from wandb import Artifact
from wandb.data_types import WBValue

from dagster_wandb.resources import WANDB_CLOUD_HOST
from dagster_wandb.utils.errors import (
    WandbArtifactsIOManagerError,
    raise_on_empty_configuration,
    raise_on_unknown_partition_keys,
    raise_on_unknown_read_configuration_keys,
    raise_on_unknown_write_configuration_keys,
)
from dagster_wandb.utils.pickling import (
    ACCEPTED_SERIALIZATION_MODULES,
    pickle_artifact_content,
    unpickle_artifact_content,
)
from dagster_wandb.version import __version__

UNIT_TEST_RUN_ID = "0ab2e48b-6d63-4ff5-b160-662cc60145f4"


class Config(TypedDict):
    dagster_run_id: str
    wandb_host: str
    wandb_entity: str
    wandb_project: str
    wandb_run_name: Optional[str]
    wandb_run_id: Optional[str]
    wandb_run_tags: Optional[list[str]]
    base_dir: str
    cache_duration_in_minutes: Optional[int]


class ArtifactsIOManager(IOManager):
    """IO Manager to handle Artifacts in Weights & Biases (W&B) .

    It handles 3 different inputs:
    - Pickable objects (the serialization module is configurable)
    - W&B Objects (Audio, Table, Image, etc)
    - W&B Artifacts
    """

    def __init__(self, wandb_client, config: Config):
        self.wandb = wandb_client

        dagster_run_id = config["dagster_run_id"]
        self.dagster_run_id = dagster_run_id
        self.wandb_host = config["wandb_host"]
        self.wandb_entity = config["wandb_entity"]
        self.wandb_project = config["wandb_project"]
        self.wandb_run_id = config.get("wandb_run_id") or dagster_run_id
        self.wandb_run_name = config.get("wandb_run_name") or f"dagster-run-{dagster_run_id[0:8]}"
        # augments the run tags
        wandb_run_tags = config["wandb_run_tags"] or []
        if "dagster_wandb" not in wandb_run_tags:
            wandb_run_tags = [*wandb_run_tags, "dagster_wandb"]
        self.wandb_run_tags = wandb_run_tags

        self.base_dir = config["base_dir"]
        cache_duration_in_minutes = config["cache_duration_in_minutes"]
        default_cache_expiration_in_minutes = 60 * 24 * 30  # 60 minutes * 24 hours * 30 days
        self.cache_duration_in_minutes = (
            cache_duration_in_minutes
            if cache_duration_in_minutes is not None
            else default_cache_expiration_in_minutes
        )

    def _get_local_storage_path(self):
        path = self.base_dir
        if os.path.basename(path) != "storage":
            path = os.path.join(path, "storage")
        path = os.path.join(path, "wandb_artifacts_manager")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_artifacts_path(self, name, version):
        local_storage_path = self._get_local_storage_path()
        path = os.path.join(local_storage_path, "artifacts", f"{name}.{version}")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_wandb_logs_path(self):
        local_storage_path = self._get_local_storage_path()
        # Adding a random uuid to avoid collisions in multi-process context
        path = os.path.join(local_storage_path, "runs", self.dagster_run_id, str(uuid.uuid4()))
        os.makedirs(path, exist_ok=True)
        return path

    def _clean_local_storage_path(self):
        local_storage_path = self._get_local_storage_path()
        cache_duration_in_minutes = self.cache_duration_in_minutes
        current_timestamp = int(time.time())
        expiration_timestamp = current_timestamp - (
            cache_duration_in_minutes * 60  # convert to seconds
        )

        for root, dirs, files in os.walk(local_storage_path, topdown=False):
            for name in files:
                current_file_path = os.path.join(root, name)
                most_recent_access = os.lstat(current_file_path).st_atime
                if most_recent_access <= expiration_timestamp or cache_duration_in_minutes == 0:
                    os.remove(current_file_path)
            for name in dirs:
                current_dir_path = os.path.join(root, name)
                if not os.path.islink(current_dir_path):
                    if len(os.listdir(current_dir_path)) == 0 or cache_duration_in_minutes == 0:
                        shutil.rmtree(current_dir_path)

    @contextmanager
    def wandb_run(self):
        self.wandb.init(
            id=self.wandb_run_id,
            name=self.wandb_run_name,
            project=self.wandb_project,
            entity=self.wandb_entity,
            dir=self._get_wandb_logs_path(),
            tags=self.wandb_run_tags,
            anonymous="never",
            resume="allow",
        )
        try:
            yield self.wandb.run
        finally:
            self.wandb.finish()
            self._clean_local_storage_path()

    def _upload_artifact(self, context: OutputContext, obj):
        if not context.has_partition_key and context.has_asset_partitions:
            raise WandbArtifactsIOManagerError(
                "Sorry, but the Weights & Biases (W&B) IO Manager can't handle processing several"
                " partitions at the same time within a single run. Please process each partition"
                " separately. If you think this might be an error, don't hesitate to reach out to"
                " Weights & Biases Support."
            )

        with self.wandb_run() as run:
            parameters = {}
            if context.definition_metadata is not None:
                parameters = context.definition_metadata.get("wandb_artifact_configuration", {})

            raise_on_unknown_write_configuration_keys(parameters)

            serialization_module = parameters.get("serialization_module", {})
            serialization_module_name = serialization_module.get("name", "pickle")

            if serialization_module_name not in ACCEPTED_SERIALIZATION_MODULES:
                raise WandbArtifactsIOManagerError(
                    f"Oops! It looks like the value you provided, '{serialization_module_name}',"
                    " isn't recognized as a valid serialization module. Here are the ones we do"
                    f" support: {ACCEPTED_SERIALIZATION_MODULES}."
                )

            serialization_module_parameters = serialization_module.get("parameters", {})
            serialization_module_parameters_with_protocol = {
                "protocol": (
                    pickle.HIGHEST_PROTOCOL  # we use the highest available protocol if we don't pass one
                ),
                **serialization_module_parameters,
            }

            artifact_type = parameters.get("type", "artifact")
            artifact_description = parameters.get("description")
            artifact_metadata = {
                "source_integration": "dagster_wandb",
                "source_integration_version": __version__,
                "source_dagster_run_id": self.dagster_run_id,
                "source_created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source_python_version": platform.python_version(),
            }
            if isinstance(obj, Artifact):
                if parameters.get("name") is not None:
                    raise WandbArtifactsIOManagerError(
                        "You've provided a 'name' property in the 'wandb_artifact_configuration'"
                        " settings. However, this 'name' property should only be used when the"
                        " output isn't already an Artifact object."
                    )

                if parameters.get("type") is not None:
                    raise WandbArtifactsIOManagerError(
                        "You've provided a 'type' property in the 'wandb_artifact_configuration'"
                        " settings. However, this 'type' property should only be used when the"
                        " output isn't already an Artifact object."
                    )

                if obj.name is None:
                    raise WandbArtifactsIOManagerError(
                        "The Weights & Biases (W&B) Artifact you provided is missing a name."
                        " Please, assign a name to your Artifact."
                    )

                if context.has_asset_key and obj.name != context.get_asset_identifier()[0]:
                    asset_identifier = context.get_asset_identifier()[0]
                    context.log.warning(
                        f"Please note, the name '{obj.name}' of your Artifact is overwritten by the"
                        f" name derived from the AssetKey '{asset_identifier}'. For consistency and"
                        " to avoid confusion, we advise sharing a constant for both your asset's"
                        " name and the artifact's name."
                    )
                    obj._name = asset_identifier  # noqa: SLF001

                if context.has_partition_key:
                    artifact_name = f"{obj.name}.{context.partition_key}"
                    # The Artifact provided is produced in a partitioned execution we add the
                    # partition as a suffix to the Artifact name
                    obj._name = artifact_name  # noqa: SLF001

                if len(serialization_module) != 0:  # not an empty dict
                    context.log.warning(
                        "You've included a 'serialization_module' in the"
                        " 'wandb_artifact_configuration' settings. However, this doesn't have any"
                        " impact when the output is already an Artifact object."
                    )

                # The obj is already an Artifact we augment its metadata
                artifact = obj

                artifact.metadata = {**artifact.metadata, **artifact_metadata}

                if artifact.description is not None and artifact_description is not None:
                    raise WandbArtifactsIOManagerError(
                        "You've given a 'description' in the 'wandb_artifact_configuration'"
                        " settings for an existing Artifact that already has a description. Please,"
                        " either set the description using 'wandb_artifact_argument' or when"
                        " creating your Artifact."
                    )
                if artifact_description is not None:
                    artifact.description = artifact_description
            else:
                if context.has_asset_key:
                    if parameters.get("name") is not None:
                        raise WandbArtifactsIOManagerError(
                            "You've included a 'name' property in the"
                            " 'wandb_artifact_configuration' settings. But, a 'name' is only needed"
                            " when there's no 'AssetKey'. When an Artifact is created from an"
                            " @asset, it uses the asset name. When it's created from an @op with an"
                            " 'asset_key' for the output, that value is used. Please remove the"
                            " 'name' property."
                        )
                    artifact_name = context.get_asset_identifier()[0]  # name of asset
                else:
                    name_parameter = parameters.get("name")
                    if name_parameter is None:
                        raise WandbArtifactsIOManagerError(
                            "The 'name' property is missing in the 'wandb_artifact_configuration'"
                            " settings. For Artifacts created from an @op, a 'name' property is"
                            " needed. You could also use an @asset as an alternative."
                        )
                    assert name_parameter is not None
                    artifact_name = name_parameter

                if context.has_partition_key:
                    artifact_name = f"{artifact_name}.{context.partition_key}"

                # We replace the | character with - because it is not allowed in artifact names
                # The | character is used in multi-dimensional partition keys
                artifact_name = str(artifact_name).replace("|", "-")

                # Creates an artifact to hold the obj
                artifact = self.wandb.Artifact(
                    name=artifact_name,
                    type=artifact_type,
                    description=artifact_description,
                    metadata=artifact_metadata,
                )
                if isinstance(obj, WBValue):
                    if len(serialization_module) != 0:  # not an empty dict
                        context.log.warning(
                            "You've included a 'serialization_module' in the"
                            " 'wandb_artifact_configuration' settings. However, this doesn't have"
                            " any impact when the output is already a W&B object like e.g Table or"
                            " Image."
                        )
                    # Adds the WBValue object using the class name as the name for the file
                    artifact.add(obj, obj.__class__.__name__)
                elif obj is not None:
                    # The output is not a native wandb Object, we serialize it
                    pickle_artifact_content(
                        context,
                        serialization_module_name,
                        serialization_module_parameters_with_protocol,
                        artifact,
                        obj,
                    )

            # Add any files: https://docs.wandb.ai/ref/python/artifact#add_file
            add_files = parameters.get("add_files")
            if add_files is not None and len(add_files) > 0:
                for add_file in add_files:
                    artifact.add_file(**add_file)

            # Add any dirs: https://docs.wandb.ai/ref/python/artifact#add_dir
            add_dirs = parameters.get("add_dirs")
            if add_dirs is not None and len(add_dirs) > 0:
                for add_dir in add_dirs:
                    artifact.add_dir(**add_dir)

            # Add any reference: https://docs.wandb.ai/ref/python/artifact#add_reference
            add_references = parameters.get("add_references")
            if add_references is not None and len(add_references) > 0:
                for add_reference in add_references:
                    artifact.add_reference(**add_reference)

            # Augments the aliases
            aliases = parameters.get("aliases", [])
            aliases.append(f"dagster-run-{self.dagster_run_id[0:8]}")
            if "latest" not in aliases:
                aliases.append("latest")

            # Logs the artifact
            self.wandb.log_artifact(artifact, aliases=aliases)
            artifact.wait()

            # Adds useful metadata to the output or Asset
            artifacts_base_url = (
                "https://wandb.ai"
                if self.wandb_host == WANDB_CLOUD_HOST
                else self.wandb_host.rstrip("/")
            )
            assert artifact.id is not None
            output_metadata = {
                "dagster_run_id": MetadataValue.dagster_run(self.dagster_run_id),
                "wandb_artifact_id": MetadataValue.text(artifact.id),
                "wandb_artifact_type": MetadataValue.text(artifact.type),
                "wandb_artifact_version": MetadataValue.text(artifact.version),
                "wandb_artifact_size": MetadataValue.int(artifact.size),
                "wandb_artifact_url": MetadataValue.url(
                    f"{artifacts_base_url}/{run.entity}/{run.project}/artifacts/{artifact.type}/{'/'.join(artifact.name.rsplit(':', 1))}"
                ),
                "wandb_entity": MetadataValue.text(run.entity),
                "wandb_project": MetadataValue.text(run.project),
                "wandb_run_id": MetadataValue.text(run.id),
                "wandb_run_name": MetadataValue.text(run.name),
                "wandb_run_path": MetadataValue.text(run.path),
                "wandb_run_url": MetadataValue.url(run.url),
            }
            context.add_output_metadata(output_metadata)

    def _download_artifact(self, context: InputContext):
        with self.wandb_run() as run:
            parameters = {}
            if context.definition_metadata is not None:
                parameters = context.definition_metadata.get("wandb_artifact_configuration", {})

            raise_on_unknown_read_configuration_keys(parameters)

            partitions_configuration = parameters.get("partitions", {})

            if not context.has_asset_partitions and len(partitions_configuration) > 0:
                raise WandbArtifactsIOManagerError(
                    "You've included a 'partitions' value in the 'wandb_artifact_configuration'"
                    " settings but it's not within a partitioned execution. Please only use"
                    " 'partitions' within a partitioned context."
                )

            if context.has_asset_partitions:
                # Note: this is currently impossible to unit test with current Dagster APIs but was
                # tested thoroughly manually
                name = parameters.get("get")
                path = parameters.get("get_path")
                if name is not None or path is not None:
                    raise WandbArtifactsIOManagerError(
                        "You've given a value for 'get' and/or 'get_path' in the"
                        " 'wandb_artifact_configuration' settings during a partitioned execution."
                        " Please use the 'partitions' property to set 'get' or 'get_path' for each"
                        " individual partition. To set a default value for all partitions, use '*'."
                    )

                artifact_name = parameters.get("name")
                if artifact_name is None:
                    artifact_name = context.asset_key.path[0]  # name of asset

                partitions = [
                    (key, f"{artifact_name}.{ str(key).replace('|', '-')}")
                    for key in context.asset_partition_keys
                ]

                output = {}

                for key, artifact_name in partitions:
                    context.log.info(f"Handling partition with key '{key}'")
                    partition_configuration = partitions_configuration.get(
                        key, partitions_configuration.get("*")
                    )

                    raise_on_empty_configuration(key, partition_configuration)
                    raise_on_unknown_partition_keys(key, partition_configuration)

                    partition_version = None
                    partition_alias = None
                    if partition_configuration and partition_configuration is not None:
                        partition_version = partition_configuration.get("version")
                        partition_alias = partition_configuration.get("alias")
                        if partition_version is not None and partition_alias is not None:
                            raise WandbArtifactsIOManagerError(
                                "You've provided both 'version' and 'alias' for the partition with"
                                " key '{key}'. You should only use one of these properties at a"
                                " time. If you choose not to use any, the latest version will be"
                                " used by default. If this partition is configured with the '*'"
                                " key, please correct the wildcard configuration."
                            )
                    partition_identifier = partition_version or partition_alias or "latest"

                    artifact_uri = (
                        f"{run.entity}/{run.project}/{artifact_name}:{partition_identifier}"
                    )
                    try:
                        api = self.wandb.Api()
                        api.artifact(artifact_uri)
                    except Exception as exception:
                        raise WandbArtifactsIOManagerError(
                            "The artifact you're attempting to download might not exist, or you"
                            " might have forgotten to include the 'name' property in the"
                            " 'wandb_artifact_configuration' settings."
                        ) from exception

                    artifact = run.use_artifact(artifact_uri)

                    artifacts_path = self._get_artifacts_path(artifact_name, artifact.version)
                    if partition_configuration and partition_configuration is not None:
                        partition_name = partition_configuration.get("get")
                        partition_path = partition_configuration.get("get_path")
                        if partition_name is not None and partition_path is not None:
                            raise WandbArtifactsIOManagerError(
                                "You've provided both 'get' and 'get_path' in the"
                                " 'wandb_artifact_configuration' settings for the partition with"
                                " key '{key}'. Only one of these properties should be used. If you"
                                " choose not to use any, the whole Artifact will be returned. If"
                                " this partition is configured with the '*' key, please correct the"
                                " wildcard configuration."
                            )

                        if partition_name is not None:
                            wandb_object = artifact.get(partition_name)
                            if wandb_object is not None:
                                output[key] = wandb_object
                                continue

                        if partition_path is not None:
                            path = artifact.get_path(partition_path)
                            download_path = path.download(root=artifacts_path)
                            if download_path is not None:
                                output[key] = download_path
                                continue

                    artifact_dir = artifact.download(root=artifacts_path)
                    unpickled_content = unpickle_artifact_content(artifact_dir)
                    if unpickled_content is not None:
                        output[key] = unpickled_content
                        continue

                    artifact.verify(root=artifacts_path)
                    output[key] = artifact

                if len(output) == 1:
                    # If there's only one partition, return the value directly
                    return next(iter(output.values()))

                return output

            elif context.has_asset_key:
                # Input is an asset
                if parameters.get("name") is not None:
                    raise WandbArtifactsIOManagerError(
                        "A conflict has been detected in the provided configuration settings. The"
                        " 'name' parameter appears to be specified twice - once in the"
                        " 'wandb_artifact_configuration' metadata dictionary, and again as an"
                        " AssetKey. Kindly avoid setting the name directly, since the AssetKey will"
                        " be used for this purpose."
                    )
                artifact_name = context.get_asset_identifier()[0]  # name of asset
            else:
                artifact_name = parameters.get("name")
                if artifact_name is None:
                    raise WandbArtifactsIOManagerError(
                        "The 'name' property is missing in the 'wandb_artifact_configuration'"
                        " settings. For Artifacts used in an @op, a 'name' property is required."
                        " You could use an @asset as an alternative."
                    )

            if context.has_partition_key:
                artifact_name = f"{artifact_name}.{context.partition_key}"

            artifact_alias = parameters.get("alias")
            artifact_version = parameters.get("version")

            if artifact_alias is not None and artifact_version is not None:
                raise WandbArtifactsIOManagerError(
                    "You've provided both 'version' and 'alias' in the"
                    " 'wandb_artifact_configuration' settings. Only one should be used at a time."
                    " If you decide not to use any, the latest version will be applied"
                    " automatically."
                )

            artifact_identifier = artifact_alias or artifact_version or "latest"
            artifact_uri = f"{run.entity}/{run.project}/{artifact_name}:{artifact_identifier}"

            # This try/except block is a workaround for a bug in the W&B SDK, this should be removed
            # once the bug is fixed.
            try:
                artifact = run.use_artifact(artifact_uri)
            except Exception:
                api = self.wandb.Api()
                artifact = api.artifact(artifact_uri)

            name = parameters.get("get")
            path = parameters.get("get_path")
            if name is not None and path is not None:
                raise WandbArtifactsIOManagerError(
                    "You've provided both 'get' and 'get_path' in the"
                    " 'wandb_artifact_configuration' settings. Only one should be used at a time."
                    " If you decide not to use any, the entire Artifact will be returned."
                )

            if name is not None:
                return artifact.get(name)

            artifacts_path = self._get_artifacts_path(artifact_name, artifact.version)
            if path is not None:
                path = artifact.get_path(path)
                return path.download(root=artifacts_path)

            artifact_dir = artifact.download(root=artifacts_path)

            unpickled_content = unpickle_artifact_content(artifact_dir)
            if unpickled_content is not None:
                return unpickled_content

            artifact.verify(root=artifacts_path)
            return artifact

    def handle_output(self, context: OutputContext, obj) -> None:
        if obj is None:
            context.log.warning(
                "The output value given to the Weights & Biases (W&B) IO Manager is empty. If this"
                " was intended, you can disregard this warning."
            )
        else:
            try:
                self._upload_artifact(context, obj)
            except WandbArtifactsIOManagerError as exception:
                raise exception
            except Exception as exception:
                raise WandbArtifactsIOManagerError() from exception

    def load_input(self, context: InputContext):
        try:
            return self._download_artifact(context)
        except WandbArtifactsIOManagerError as exception:
            raise exception
        except Exception as exception:
            raise WandbArtifactsIOManagerError() from exception


@dagster_maintained_io_manager
@io_manager(
    required_resource_keys={"wandb_resource", "wandb_config"},
    description="IO manager to read and write W&B Artifacts",
    config_schema={
        "run_name": Field(
            String,
            is_required=False,
            description=(
                "Short display name for this run, which is how you'll identify this run in the UI."
                " By default, it`s set to a string with the following format dagster-run-[8 first"
                " characters of the Dagster Run ID] e.g. dagster-run-7e4df022."
            ),
        ),
        "run_id": Field(
            String,
            is_required=False,
            description=(
                "Unique ID for this run, used for resuming. It must be unique in the project, and"
                " if you delete a run you can't reuse the ID. Use the name field for a short"
                " descriptive name, or config for saving hyperparameters to compare across runs."
                r" The ID cannot contain the following special characters: /\#?%:.. You need to set"
                " the Run ID when you are doing experiment tracking inside Dagster to allow the IO"
                " Manager to resume the run. By default it`s set to the Dagster Run ID e.g "
                " 7e4df022-1bf2-44b5-a383-bb852df4077e."
            ),
        ),
        "run_tags": Field(
            [String],
            is_required=False,
            description=(
                "A list of strings, which will populate the list of tags on this run in the UI."
                " Tags are useful for organizing runs together, or applying temporary labels like"
                " 'baseline' or 'production'. It's easy to add and remove tags in the UI, or filter"
                " down to just runs with a specific tag. Any W&B Run used by the integration will"
                " have the dagster_wandb tag."
            ),
        ),
        "base_dir": Field(
            String,
            is_required=False,
            description=(
                "Base directory used for local storage and caching. W&B Artifacts and W&B Run logs"
                " will be written and read from that directory. By default, it`s using the"
                " DAGSTER_HOME directory."
            ),
        ),
        "cache_duration_in_minutes": Field(
            Int,
            is_required=False,
            description=(
                "Defines the amount of time W&B Artifacts and W&B Run logs should be kept in the"
                " local storage. Only files and directories that were not opened for that amount of"
                " time are removed from the cache. Cache purging happens at the end of an IO"
                " Manager execution. You can set it to 0, if you want to disable caching"
                " completely. Caching improves speed when an Artifact is reused between jobs"
                " running on the same machine. It defaults to 30 days."
            ),
        ),
    },
)
def wandb_artifacts_io_manager(context: InitResourceContext):
    """Dagster IO Manager to create and consume W&B Artifacts.

    It allows any Dagster @op or @asset to create and consume W&B Artifacts natively.

    For a complete set of documentation, see `Dagster integration <https://docs.wandb.ai/guides/integrations/dagster>`_.

    **Example:**

    .. code-block:: python

            @repository
            def my_repository():
                return [
                    *with_resources(
                        load_assets_from_current_module(),
                        resource_defs={
                            "wandb_config": make_values_resource(
                                entity=str,
                                project=str,
                            ),
                            "wandb_resource": wandb_resource.configured(
                                {"api_key": {"env": "WANDB_API_KEY"}}
                            ),
                            "wandb_artifacts_manager": wandb_artifacts_io_manager.configured(
                                {"cache_duration_in_minutes": 60} # only cache files for one hour
                            ),
                        },
                        resource_config_by_key={
                            "wandb_config": {
                                "config": {
                                    "entity": "my_entity",
                                    "project": "my_project"
                                }
                            }
                        },
                    ),
                ]


            @asset(
                name="my_artifact",
                metadata={
                    "wandb_artifact_configuration": {
                        "type": "dataset",
                    }
                },
                io_manager_key="wandb_artifacts_manager",
            )
            def create_dataset():
                return [1, 2, 3]

    """
    wandb_client = context.resources.wandb_resource["sdk"]
    wandb_host = context.resources.wandb_resource["host"]
    wandb_entity = context.resources.wandb_config["entity"]
    wandb_project = context.resources.wandb_config["project"]

    wandb_run_name = None
    wandb_run_id = None
    wandb_run_tags = None
    base_dir = (
        context.instance.storage_directory() if context.instance else os.environ["DAGSTER_HOME"]
    )
    cache_duration_in_minutes = None
    if context.resource_config is not None:
        wandb_run_name = context.resource_config.get("run_name")
        wandb_run_id = context.resource_config.get("run_id")
        wandb_run_tags = context.resource_config.get("run_tags")
        base_dir = context.resource_config.get("base_dir", base_dir)
        cache_duration_in_minutes = context.resource_config.get("cache_duration_in_minutes")

    if "PYTEST_CURRENT_TEST" in os.environ:
        dagster_run_id = UNIT_TEST_RUN_ID
    else:
        dagster_run_id = context.run_id

    assert dagster_run_id is not None

    config: Config = {
        "dagster_run_id": dagster_run_id,
        "wandb_host": wandb_host,
        "wandb_entity": wandb_entity,
        "wandb_project": wandb_project,
        "wandb_run_name": wandb_run_name,
        "wandb_run_id": wandb_run_id,
        "wandb_run_tags": wandb_run_tags,
        "base_dir": base_dir,
        "cache_duration_in_minutes": cache_duration_in_minutes,
    }
    return ArtifactsIOManager(wandb_client, config)
